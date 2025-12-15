# 订单和商品同步机制实现总结

## 已完成的功能

### 1. 数据库模型 ✅
- **OrderDetailTask 模型**：订单详情补齐任务表
  - 字段：shop_id, parent_order_sn, order_ids, status, package_sn, error_message, retry_count, max_retries
  - 状态：pending, processing, completed, failed
  - 最大重试次数：5次

- **Shop 模型扩展**：
  - 订单同步：last_sync_at, last_full_sync_at, sync_status
  - 商品同步：last_product_sync_at, last_product_full_sync_at, product_sync_status

### 2. 订单详情补齐服务 ✅
- **OrderDetailEnrichmentService**：
  - 创建补齐任务（为已发货/已签收订单）
  - 批量处理任务（50个父订单/批）
  - 从订单详情接口获取包裹号
  - 任务重试机制（最多5次）
  - Redis队列管理

### 3. Redis任务队列 ✅
- **队列操作**：
  - LPUSH：任务入队
  - RPOP：任务出队
  - LLEN：队列长度
  - SETEX：任务锁和状态
- **任务锁机制**：防止重复处理（TTL=5分钟）
- **任务状态存储**：TTL=24小时

### 4. 后台工作线程 ✅
- **OrderDetailWorker**：
  - 持续轮询任务队列
  - 批量处理（50个父订单/批）
  - 轮询间隔：5秒
  - 自动启动/停止（应用生命周期管理）

### 5. 同步服务改造 ✅
- **SyncService 修改**：
  - 移除同步获取包裹号逻辑
  - 同步完成后自动创建补齐任务
  - 更新同步状态管理
  - 支持全量/增量同步

### 6. 定时任务配置 ✅
- **订单同步**：
  - 增量同步：每10分钟
  - 全量同步：每日凌晨2点
- **商品同步**：
  - 增量同步：每10分钟
  - 全量同步：每日凌晨3点

### 7. API接口 ✅
- **GET /api/sync/shops/{shop_id}/orders/progress**：查询订单同步进度
- **POST /api/sync/shops/{shop_id}/orders/enrich-details**：手动触发包裹号补齐
- **GET /api/sync/shops/{shop_id}/orders/enrich-tasks**：查询补齐任务状态
- **GET /api/sync/orders/enrich-tasks/stats**：获取所有任务统计
- **GET /api/sync/monitoring/alerts**：获取监控告警
- **GET /api/sync/monitoring/health**：获取系统健康状态

### 8. 监控和告警 ✅
- **MonitoringService**：
  - 队列积压检查（阈值：1000个任务）
  - 任务失败率检查（阈值：10%）
  - 同步状态检查
  - 工作线程状态检查
  - 系统健康评分

## 工作流程

### 订单同步流程
```
1. 定时任务触发（增量10分钟 / 全量每日）
   ↓
2. 调用 bg.order.list.v2.get 获取订单列表
   ↓
3. 保存订单基本信息到数据库
   ↓
4. 识别需要补齐包裹号的订单（SHIPPED/DELIVERED + 无包裹号）
   ↓
5. 创建补齐任务，加入Redis队列
   ↓
6. 后台工作线程持续处理队列
   ↓
7. 调用 bg.order.detail.v2.get 获取包裹号
   ↓
8. 更新订单包裹号
```

### 商品同步流程
```
1. 定时任务触发（增量10分钟 / 全量每日）
   ↓
2. 调用商品列表API获取商品
   ↓
3. 保存/更新商品信息到数据库
   ↓
4. 更新商品同步状态和时间
```

## 配置参数

- **批量处理大小**：50个父订单/批
- **最大重试次数**：5次
- **轮询间隔**：5秒
- **任务锁TTL**：5分钟
- **任务状态TTL**：24小时
- **增量同步间隔**：10分钟
- **全量同步时间**：每日凌晨2点（订单）、3点（商品）

## 告警阈值

- **队列积压**：> 1000个任务
- **任务失败率**：> 10%
- **同步超时**：> 1小时
- **API失败率**：> 5%

## 数据库迁移

需要执行以下迁移：
1. `add_package_sn_to_orders` - 添加包裹号字段
2. `add_sync_fields_to_shops` - 添加同步状态字段
3. `add_order_detail_tasks_table` - 创建任务表

## 启动顺序

1. 应用启动时：
   - 启动定时任务调度器
   - 启动订单详情补齐工作线程

2. 应用关闭时：
   - 停止工作线程
   - 停止定时任务调度器

## 注意事项

1. **Redis依赖**：系统需要Redis支持，如果Redis不可用，任务队列功能会降级
2. **API限流**：遵守Temu API限流规则，工作线程使用并发控制
3. **任务重试**：失败任务会自动重试（最多5次），超过后标记为失败
4. **数据一致性**：订单列表同步和包裹号补齐是异步的，可能存在短暂的数据不一致

## 后续优化方向

1. 任务优先级机制
2. 分布式部署支持
3. 更详细的监控指标
4. 告警通知（邮件/短信/Webhook）
