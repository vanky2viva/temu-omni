# Temu Omni 架构优化方案（同步、API、及时性、性能）

本文在当前实现基础上给出可落地的优化路线。引用的代码位置以仓库现状为准，便于拆分任务。

## 现状与痛点（摘自代码）
- 同步调度：`backend/app/core/scheduler.py` 使用单进程 APScheduler、串行遍历店铺，`asyncio.run` 包裹每家店的同步，CPU/网络空转且无法水平扩展。
- 数据写入：`SyncService` 每条订单 `commit`，缺少幂等 upsert，容易放大锁与 I/O；成本计算同样是批量扫描同步运行（`OrderCostCalculationService.calculate_order_costs`）。
- API 调用：`TemuService` 每次请求创建/关闭 client，缺少统一重试、熔断和速率治理；没有 request/response 级别的链路日志与指标。
- 数据及时性：订单同步、成本计算固定间隔，缺少事件触发或延迟队列，对“刚支付/刚发货”类事件响应慢。
- 性能可见性：缺少对关键路径的指标收集（同步耗时、API 失败率、DB 写入吞吐）。

## 总体策略
1) 将“同步/计算”拆成可并发、可调度的任务队列；2) 架设统一的 API 访问层负责重试、限流和熔断；3) 引入增量水位和事件触发提高及时性；4) 用批处理 + upsert 提高数据库写入效率；5) 补齐观测性与告警。

## 优化方案（分模块）

### 1) 同步架构
- 任务队列化：用 Redis + RQ/Celery（生产推荐 Celery）替换 APScheduler 承载任务；`scheduler.py` 改为“生产任务 + 推送到队列”，worker 可水平扩容。
- 并发模型：按 shop 维度设置队列或并发 key（避免同店铺并发导致重复）；允许多店铺并行，单店铺串行。
- 增量水位：引入 `sync_cursor` 表，按实体（order/product）+ shop 记录 `last_synced_at`、`page_token`，避免重复计算并支持断点续传。
- 幂等写入：在 `SyncService` 改用 upsert（SQLAlchemy `insert(...).on_conflict_do_update`）按唯一键 `(order_sn, product_sku, spu_id)` 写入，并将 `commit` 频率改为批次（如 200 条一批）。
- 失败重试：队列任务使用指数退避，超过阈值写入死信队列 + 报警。

### 2) API 获取与治理
- Client 复用：`TemuService` 维护长生命周期 httpx.AsyncClient（带连接池、HTTP/2），放在 worker 启动/关闭钩子中。
- 速率与熔断：在代理层（`proxy-server`）和 SDK 层同时做令牌桶限流、超时/重试（幂等请求可安全重试），对 429/5xx 自动退避。
- 结构化日志：为每个请求打 `shop_id`, `api`, `latency`, `status`，便于定位。
- 输入校验：在 API 返回处理层统一做 schema 校验/字段缺失兜底，减少下游异常。

### 3) 数据更新及时性
- 事件驱动：对“新支付/待发货”等状态使用短周期（5-10 分钟）的轻量任务；对“已发货待签收”使用延迟队列（出库后按 SLA-1h 重查）。
- 写后触发：订单写入后将需要成本重算的订单 ID 推入 `recalc_cost` 队列，避免按时间扫全表。
- 手动补偿：提供“单店/单订单补偿”任务入口，减少等待固定间隔。

### 4) 成本/指标计算性能
- 按需重算：`OrderCostCalculationService` 改为事件驱动 + 批量（队列消费订单 ID 列表）；全量重算保留离线任务。
- 批量查询：预取成本与商品映射（一次查询多 SKU 的 Product/ProductCost），减少 N+1。
- 缓存与聚合：常用指标（GMV、利润日报）在写入阶段同步更新聚合表或物化视图；前端读取聚合表减轻热点查询。

### 5) 可观测性与告警
- 指标：暴露 Prometheus/StatsD 指标（API/队列队列长度、处理耗时、失败率、DB upsert 耗时）。
- 日志：统一 JSON 结构化日志（包含 trace_id/shop_id/job_id），支持按任务搜索。
- 告警：关键指标阈值报警（API 5xx/429、队列积压、同步失败率、成本计算延迟）。

## 推荐落地顺序
1. 引入任务队列 + worker（保持 APScheduler 只负责入队），同时在 SyncService 改批量提交与 upsert。
2. 给 TemuService/代理增加连接池、重试/限流与结构化日志。
3. 落地增量水位表与事件触发（延迟队列 + 手工补偿接口）。
4. 成本重算改事件驱动，并加入聚合表/物化视图。
5. 加入指标/日志/告警，设置初始阈值。

## 需要变更的关键文件（建议拆分 PR）
- `backend/app/core/scheduler.py`：改为“计划任务 → 入队”。新增 `tasks/` 存放 Celery/RQ 任务定义。
- `backend/app/services/sync_service.py`：批处理 + upsert、移除逐条 commit、使用水位。
- `backend/app/services/temu_service.py` & `proxy-server`：长连接池、重试/限流、结构化日志。
- 新增 `backend/app/models/sync_cursor.py`：维护实体级水位。
- `backend/app/services/order_cost_service.py`：事件驱动重算、批量预取。
- 基础设施：`docker-compose*` 增加 Redis/Celery worker/beat；`docs/` 补充运行与容量规划。 

以上方案在不改变业务的前提下兼顾：更快同步（并发 + 水位断点）、更稳 API（限流/重试/熔断）、及时成本更新（事件驱动）、更好的性能可见性（指标/告警）。***
