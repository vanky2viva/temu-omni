# 订单和商品同步机制设计方案

## 一、需求分析

### 1.1 当前问题
- 订单列表同步和包裹号获取耦合在一起，影响同步性能
- 包裹号获取需要调用详情接口，耗时较长
- 全量同步和增量同步的机制需要优化
- 商品列表同步也需要全量/增量机制

### 1.2 目标
- **解耦订单列表同步和包裹号获取**：列表同步快速完成，包裹号异步补齐
- **优化全量/增量同步机制**：订单和商品都支持全量/增量同步
- **提高系统响应性**：用户不需要等待包裹号获取完成
- **统一同步策略**：订单和商品使用相同的同步机制

## 二、架构设计

### 2.1 整体流程

```
┌─────────────────────────────────────────────────────────────┐
│                    订单同步流程                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   1. 订单列表同步（同步/异步）        │
        │   - 全量同步：指定时间范围            │
        │   - 增量同步：从last_sync_at开始      │
        │   - 使用 bg.order.list.v2.get        │
        └─────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────────┐
        │   2. 订单数据保存到数据库            │
        │   - 保存订单基本信息                  │
        │   - 更新订单状态                      │
        │   - 保存到 raw 表                    │
        └─────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────────┐
        │   3. 异步任务队列（包裹号补齐）       │
        │   - 识别需要包裹号的订单             │
        │   - 加入任务队列                     │
        │   - 后台异步处理                     │
        └─────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 订单列表同步服务（SyncService）
- **职责**：快速拉取订单列表，保存基本信息
- **接口**：`bg.order.list.v2.get`
- **输出**：订单基本信息 + 需要补齐包裹号的订单列表

#### 2.2.2 订单详情补齐服务（OrderDetailEnrichmentService）
- **职责**：异步获取订单详情，补齐包裹号等信息
- **接口**：`bg.order.detail.v2.get`
- **触发方式**：任务队列/定时任务

#### 2.2.3 任务队列（Task Queue）
- **方案选择**：
  - **方案A**：使用 Redis + 后台线程（轻量级，适合当前架构）
  - **方案B**：使用 Celery（功能强大，但需要额外组件）
  - **推荐**：方案A（Redis + 后台线程）

## 三、详细设计

### 3.1 全量/增量同步机制

#### 3.1.1 订单全量同步（Full Sync）
```python
# 触发条件
- 手动触发（用户点击"全量同步"）
- 首次同步（last_sync_at 为 None）
- 定期全量同步（每日一次）

# 时间范围策略
- 默认：最近365天
- 可配置：通过参数指定时间范围
- 分页拉取：每页100条，循环直到无更多数据

# 特点
- 覆盖指定时间范围内的所有订单
- 可能耗时较长，适合在低峰期执行
- 可以设置进度回调，实时反馈
```

#### 3.1.2 订单增量同步（Incremental Sync）
```python
# 触发条件
- 定时任务（每10分钟）
- 手动触发（用户点击"增量同步"）

# 时间范围策略
- 开始时间：shop.last_sync_at（如果存在）
- 结束时间：当前时间
- 如果 last_sync_at 为 None：使用首次同步策略（最近7天）

# 特点
- 只同步新增和更新的订单
- 快速完成，适合频繁执行
- 自动更新 last_sync_at
```

#### 3.1.3 商品全量同步（Full Sync）
```python
# 触发条件
- 手动触发（用户点击"全量同步"）
- 首次同步（last_product_sync_at 为 None）
- 定期全量同步（每日一次）

# 同步策略
- 同步所有在售商品（skc_site_status=1）
- 分页拉取：每页100条，循环直到无更多数据
- 通过商品ID判断是否已存在

# 特点
- 覆盖所有在售商品
- 可能耗时较长，适合在低峰期执行
```

#### 3.1.4 商品增量同步（Incremental Sync）
```python
# 触发条件
- 定时任务（每10分钟）
- 手动触发（用户点击"增量同步"）

# 同步策略
- 只同步新增和更新的商品
- 通过商品ID判断是否已存在
- 如果商品已存在，则更新；否则创建

# 特点
- 只同步变化的商品
- 快速完成，适合频繁执行
- 自动更新 last_product_sync_at
```

#### 3.1.5 同步状态管理
```python
# Shop 模型字段
- last_sync_at: DateTime  # 最后订单同步时间
- last_full_sync_at: DateTime  # 最后订单全量同步时间
- last_product_sync_at: DateTime  # 最后商品同步时间
- last_product_full_sync_at: DateTime  # 最后商品全量同步时间
- sync_status: Enum  # 订单同步状态（idle, syncing, error）
- product_sync_status: Enum  # 商品同步状态（idle, syncing, error）
- sync_progress: JSON  # 订单同步进度信息（存储在Redis）
- product_sync_progress: JSON  # 商品同步进度信息（存储在Redis）
```

### 3.2 异步包裹号补齐机制

#### 3.2.1 任务识别
```python
# 需要补齐包裹号的订单条件
1. 订单状态为 SHIPPED 或 DELIVERED（排除已取消和待发货订单）
2. package_sn 为空或 None
3. parent_order_sn 不为空（详情接口需要父订单号）

# 任务数据结构
{
    "task_id": "uuid",
    "shop_id": 1,
    "parent_order_sn": "PO-211-xxx",
    "order_ids": [1, 2, 3],  # 该父订单下的所有子订单ID
    "status": "pending",  # pending, processing, completed, failed
    "created_at": "2025-01-01T00:00:00",
    "retry_count": 0,
    "max_retries": 3
}
```

#### 3.2.2 任务队列设计（Redis方案）

```python
# Redis 数据结构
1. 任务队列：List
   - Key: "order_detail_tasks:queue"
   - Value: JSON字符串的任务数据
   - 操作：LPUSH（入队）、RPOP（出队）

2. 任务状态：Hash
   - Key: "order_detail_tasks:status:{task_id}"
   - Field: task_id
   - Value: JSON字符串的任务状态
   - TTL: 24小时

3. 任务锁：String（防止重复处理）
   - Key: "order_detail_tasks:lock:{parent_order_sn}"
   - Value: task_id
   - TTL: 300秒（5分钟）
```

#### 3.2.3 后台工作线程

```python
# 工作线程设计
class OrderDetailWorker:
    """订单详情补齐工作线程"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.batch_size = 10  # 每批处理10个任务
        self.poll_interval = 5  # 轮询间隔（秒）
    
    def start(self):
        """启动工作线程"""
        # 在应用启动时启动
        
    def stop(self):
        """停止工作线程"""
        # 在应用关闭时停止
        
    def process_tasks(self):
        """处理任务队列"""
        while self.running:
            # 1. 从队列获取任务（批量）
            # 2. 调用详情接口获取包裹号
            # 3. 更新数据库
            # 4. 更新任务状态
            # 5. 处理失败重试
```

#### 3.2.4 任务处理流程

```
1. 订单列表同步完成
   ↓
2. 识别需要补齐的订单（SHIPPED/DELIVERED + 无包裹号，排除已取消和待发货）
   ↓
3. 按父订单号分组，创建任务
   ↓
4. 任务入队（Redis List）
   ↓
5. 后台工作线程轮询队列
   ↓
6. 批量获取任务（batch_size=10）
   ↓
7. 并发调用详情接口（使用 asyncio）
   ↓
8. 更新数据库包裹号
   ↓
9. 更新任务状态
   ↓
10. 失败任务重试（最多3次）
```

### 3.3 API设计

#### 3.3.1 同步订单列表API

```python
POST /api/sync/orders
{
    "shop_id": 1,
    "full_sync": false,  # true=全量, false=增量
    "begin_time": 1234567890,  # 可选，Unix时间戳
    "end_time": 1234567890,  # 可选，Unix时间戳
    "async": true  # 是否异步执行
}

Response:
{
    "task_id": "uuid",  # 如果async=true
    "status": "started",
    "message": "同步任务已启动"
}
```

#### 3.3.2 查询同步进度API

```python
GET /api/sync/orders/progress?shop_id=1

Response:
{
    "status": "syncing",  # idle, syncing, completed, error
    "progress": 45.5,  # 百分比
    "total": 1000,
    "processed": 455,
    "new": 100,
    "updated": 355,
    "failed": 0,
    "estimated_remaining_seconds": 120
}
```

#### 3.3.3 手动触发包裹号补齐API

```python
POST /api/sync/orders/enrich-details
{
    "shop_id": 1,  # 可选，不指定则处理所有店铺
    "order_status": ["SHIPPED", "DELIVERED"],  # 可选（排除已取消和待发货）
    "force": false  # 是否强制重新获取（即使已有包裹号）
}

Response:
{
    "task_count": 50,
    "message": "已创建50个补齐任务"
}
```

#### 3.3.4 查询补齐任务状态API

```python
GET /api/sync/orders/enrich-tasks?shop_id=1&status=pending

Response:
{
    "total": 50,
    "pending": 10,
    "processing": 5,
    "completed": 30,
    "failed": 5,
    "tasks": [
        {
            "task_id": "uuid",
            "parent_order_sn": "PO-211-xxx",
            "status": "pending",
            "created_at": "2025-01-01T00:00:00"
        }
    ]
}
```

### 3.4 数据库设计

#### 3.4.1 新增表：order_detail_tasks

```sql
CREATE TABLE order_detail_tasks (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    parent_order_sn VARCHAR(100) NOT NULL,
    order_ids INTEGER[] NOT NULL,  -- 该父订单下的所有子订单ID
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    package_sn VARCHAR(200),  -- 获取到的包裹号
    error_message TEXT,  -- 错误信息
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_shop_status (shop_id, status),
    INDEX idx_parent_order_sn (parent_order_sn),
    INDEX idx_status_created (status, created_at)
);
```

#### 3.4.2 Shop表扩展字段

```sql
ALTER TABLE shops ADD COLUMN IF NOT EXISTS last_full_sync_at TIMESTAMP;
ALTER TABLE shops ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'idle';
```

### 3.5 定时任务设计

#### 3.5.1 订单增量同步任务（高频）

```python
# 每10分钟执行一次
@schedule(interval=10 minutes)
def incremental_order_sync_job():
    """增量同步订单列表"""
    # 1. 获取所有启用的店铺
    # 2. 对每个店铺执行增量同步
    # 3. 同步完成后，自动创建包裹号补齐任务
```

#### 3.5.2 订单全量同步任务（低频）

```python
# 每日凌晨2点执行
@schedule(cron="0 2 * * *")
def full_order_sync_job():
    """全量同步订单列表（每日一次）"""
    # 1. 获取所有启用的店铺
    # 2. 对每个店铺执行全量同步（最近365天）
    # 3. 同步完成后，自动创建包裹号补齐任务
```

#### 3.5.3 商品增量同步任务（高频）

```python
# 每10分钟执行一次
@schedule(interval=10 minutes)
def incremental_product_sync_job():
    """增量同步商品列表"""
    # 1. 获取所有启用的店铺
    # 2. 对每个店铺执行增量同步
    # 3. 只同步新增和更新的商品
```

#### 3.5.4 商品全量同步任务（低频）

```python
# 每日凌晨3点执行
@schedule(cron="0 3 * * *")
def full_product_sync_job():
    """全量同步商品列表（每日一次）"""
    # 1. 获取所有启用的店铺
    # 2. 对每个店铺执行全量同步（所有在售商品）
    # 3. 同步所有商品信息
```

#### 3.5.3 包裹号补齐任务（持续运行）

```python
# 后台工作线程持续运行
def enrich_order_details_worker():
    """订单详情补齐工作线程"""
    # 1. 持续轮询任务队列
    # 2. 批量处理任务
    # 3. 处理失败重试
    # 4. 清理过期任务
```

#### 3.5.4 任务清理任务（定期）

```python
# 每天凌晨3点执行
@schedule(cron="0 3 * * *")
def cleanup_tasks_job():
    """清理过期和失败的任务"""
    # 1. 删除7天前已完成的任务
    # 2. 删除超过最大重试次数的失败任务
    # 3. 清理Redis中的过期数据
```

## 四、实现方案对比

### 4.1 方案A：Redis + 后台线程（推荐）

**优点**：
- 轻量级，不需要额外组件
- 与现有Redis基础设施集成
- 实现简单，维护成本低
- 适合中小规模应用

**缺点**：
- 单机部署，无法横向扩展
- 工作线程故障会影响任务处理

**适用场景**：当前项目规模，单机部署

### 4.2 方案B：Celery + Redis/RabbitMQ

**优点**：
- 支持分布式部署，可横向扩展
- 功能强大，支持任务优先级、延迟执行等
- 有完善的监控和管理工具

**缺点**：
- 需要额外的Celery Worker进程
- 配置和维护更复杂
- 对于当前需求可能过度设计

**适用场景**：大规模部署，需要分布式任务处理

### 4.3 方案C：数据库轮询（不推荐）

**优点**：
- 实现简单，不需要额外组件

**缺点**：
- 数据库压力大
- 实时性差
- 不适合高并发场景

## 五、性能优化

### 5.1 批量处理
- 订单列表同步：每页100条
- 包裹号获取：批量处理10个父订单
- 数据库更新：批量提交

### 5.2 并发控制
- API限流：遵守Temu API限流规则
- 任务并发：使用asyncio并发调用详情接口（最多5个并发）
- 数据库连接池：合理配置连接池大小

### 5.3 缓存策略
- 同步进度：存储在Redis，TTL=1小时
- 任务状态：存储在Redis，TTL=24小时
- 避免重复任务：使用Redis锁机制

## 六、错误处理和重试

### 6.1 任务重试策略
```python
# 重试规则
- 最大重试次数：3次
- 重试间隔：指数退避（1分钟、5分钟、30分钟）
- 重试条件：
  * API调用失败（网络错误、超时）
  * API返回错误码（非业务错误）
  * 数据库更新失败

# 不重试的情况
- API返回业务错误（订单不存在等）
- 超过最大重试次数
```

### 6.2 错误记录
- 记录到数据库（order_detail_tasks.error_message）
- 记录到日志系统
- 发送告警（可选）

## 七、监控和告警

### 7.1 监控指标
- 同步任务执行时间
- 任务队列长度
- 任务成功率
- API调用成功率
- 数据库更新延迟

### 7.2 告警规则
- 任务队列积压超过1000个
- 任务失败率超过10%
- 同步任务执行时间超过1小时
- API调用失败率超过5%

## 八、实施计划

### 阶段1：基础架构（1-2天）
1. 创建 order_detail_tasks 表
2. 实现任务队列（Redis）
3. 实现后台工作线程
4. 实现任务创建和入队逻辑

### 阶段2：同步服务改造（1-2天）
1. 修改 SyncService，移除同步获取包裹号的逻辑
2. 实现任务创建逻辑（识别需要补齐的订单）
3. 优化全量/增量同步机制
4. 添加同步状态管理

### 阶段3：API和前端（1天）
1. 实现同步进度查询API
2. 实现任务状态查询API
3. 前端显示同步进度和任务状态

### 阶段4：测试和优化（1-2天）
1. 单元测试
2. 集成测试
3. 性能测试
4. 优化和调优

## 九、风险评估

### 9.1 技术风险
- **Redis故障**：任务队列丢失
  - 缓解：定期备份，任务持久化到数据库
  
- **API限流**：Temu API限流导致任务失败
  - 缓解：实现限流控制，任务重试机制

### 9.2 业务风险
- **数据不一致**：订单列表已同步，但包裹号未补齐
  - 缓解：前端显示"包裹号获取中"状态，定期补齐任务

## 十、后续优化方向

1. **任务优先级**：重要订单优先处理
2. **分布式部署**：支持多Worker节点
3. **任务调度优化**：智能调度，避免API限流
4. **数据一致性检查**：定期检查并补齐缺失数据


