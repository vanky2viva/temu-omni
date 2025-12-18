# 任务队列和监控告警查看指南

## 重要说明

### 任务完成状态说明

任务可能以两种方式完成：

1. **成功获取包裹号**：任务状态为 `completed`，`package_sn` 有值
2. **成功获取详情但无包裹号**：任务状态为 `completed`，`package_sn` 为 `null`
   - 这种情况表示API调用成功，但订单详情中确实没有包裹号信息
   - **不会重试**，**不计入失败统计**
   - 可能原因：订单已取消但未发货、订单状态异常等

只有API调用失败或超过最大重试次数时，任务才会标记为 `failed`。

## 一、API接口说明

### 1.1 查看任务队列统计

**接口**: `GET /api/sync/orders/enrich-tasks/stats`

**说明**: 获取所有店铺的订单详情补齐任务统计

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/sync/orders/enrich-tasks/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 150,
    "pending": 50,
    "processing": 10,
    "completed": 80,
    "failed": 10,
    "queue_length": 50
  }
}
```

### 1.2 查看指定店铺的任务列表

**接口**: `GET /api/sync/shops/{shop_id}/orders/enrich-tasks`

**参数**:
- `shop_id`: 店铺ID（路径参数）
- `status`: 任务状态筛选（可选，pending/processing/completed/failed）
- `limit`: 返回数量限制（默认50）

**请求示例**:
```bash
# 查看所有任务
curl -X GET "http://localhost:8000/api/sync/shops/1/orders/enrich-tasks?limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 只查看待处理的任务
curl -X GET "http://localhost:8000/api/sync/shops/1/orders/enrich-tasks?status=pending&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "shop_id": 1,
  "stats": {
    "total": 50,
    "pending": 30,
    "processing": 5,
    "completed": 10,
    "failed": 5,
    "queue_length": 30
  },
  "tasks": [
    {
      "task_id": 1,
      "parent_order_sn": "PO-211-xxx",
      "status": "pending",
      "package_sn": null,
      "error_message": null,
      "retry_count": 0,
      "max_retries": 5,
      "created_at": "2025-01-22T10:00:00",
      "completed_at": null,
      "order_count": 3
    }
  ]
}
```

### 1.3 查看监控告警

**接口**: `GET /api/sync/monitoring/alerts`

**说明**: 获取所有监控告警信息

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/sync/monitoring/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 3,
    "errors": 1,
    "warnings": 2,
    "alerts": [
      {
        "type": "queue_backlog",
        "severity": "warning",
        "message": "任务队列积压严重: 1200 个任务待处理",
        "queue_length": 1200,
        "threshold": 1000,
        "timestamp": "2025-01-22T10:00:00"
      },
      {
        "type": "task_failure_rate",
        "severity": "error",
        "message": "任务失败率过高: 15.0% (15/100)",
        "failure_rate": 0.15,
        "failed_count": 15,
        "total_count": 100,
        "hours": 24,
        "timestamp": "2025-01-22T10:00:00"
      },
      {
        "type": "sync_error",
        "severity": "error",
        "message": "店铺 测试店铺 订单同步失败",
        "shop_id": 1,
        "shop_name": "测试店铺",
        "sync_type": "orders",
        "timestamp": "2025-01-22T10:00:00"
      }
    ],
    "timestamp": "2025-01-22T10:00:00"
  }
}
```

### 1.4 查看系统健康状态

**接口**: `GET /api/sync/monitoring/health`

**说明**: 获取系统健康状态汇总

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/sync/monitoring/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "health_score": 95,
    "worker_running": true,
    "task_stats": {
      "total": 150,
      "pending": 50,
      "processing": 10,
      "completed": 80,
      "failed": 10,
      "queue_length": 50
    },
    "shops_total": 3,
    "shops_with_errors": 0,
    "timestamp": "2025-01-22T10:00:00"
  }
}
```

### 1.5 手动触发包裹号补齐

**接口**: `POST /api/sync/shops/{shop_id}/orders/enrich-details`

**参数**:
- `shop_id`: 店铺ID（路径参数）
- `force`: 是否强制重新获取（查询参数，默认false）

**请求示例**:
```bash
# 为已发货/已签收订单创建补齐任务（排除已取消和待发货）
curl -X POST "http://localhost:8000/api/sync/shops/1/orders/enrich-details?force=false" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 强制重新获取所有订单的包裹号
curl -X POST "http://localhost:8000/api/sync/shops/1/orders/enrich-details?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "message": "已创建 50 个补齐任务",
  "data": {
    "shop_id": 1,
    "task_count": 50
  }
}
```

## 二、通过前端界面查看（待实现）

目前可以通过以下方式在前端查看：

### 2.1 使用浏览器开发者工具

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 调用上述API接口
4. 查看响应数据

### 2.2 使用 Postman 或类似工具

1. 导入API接口
2. 设置认证Token
3. 调用接口查看结果

## 三、告警类型说明

### 3.1 队列积压告警 (queue_backlog)
- **触发条件**: 队列中待处理任务数 > 1000
- **严重程度**: warning
- **处理建议**: 检查工作线程是否正常运行，或增加工作线程数量

### 3.2 任务失败率告警 (task_failure_rate)
- **触发条件**: 最近24小时任务失败率 > 10%
- **严重程度**: error
- **处理建议**: 检查API调用是否正常，查看失败任务的错误信息

### 3.3 同步错误告警 (sync_error)
- **触发条件**: 店铺同步状态为 error
- **严重程度**: error
- **处理建议**: 检查店铺API配置，查看同步日志

### 3.4 同步过期告警 (sync_stale)
- **触发条件**: 超过24小时未同步
- **严重程度**: warning
- **处理建议**: 检查定时任务是否正常运行

### 3.5 工作线程告警 (worker_down)
- **触发条件**: 工作线程未运行
- **严重程度**: error
- **处理建议**: 重启应用或检查工作线程启动日志

## 四、健康状态说明

### 4.1 健康分数计算
- 基础分数: 100
- 工作线程未运行: -30
- 队列积压超过阈值: -20
- 店铺同步错误: -20
- 任务失败: -10

### 4.2 状态等级
- **healthy** (80-100分): 系统运行正常
- **degraded** (50-79分): 系统运行降级，有部分问题
- **unhealthy** (0-49分): 系统运行异常，需要立即处理

## 五、常用查询命令

### 5.1 查看队列长度（通过Redis）
```bash
docker exec temu-omni-backend python -c "from app.core.redis_client import RedisClient; print(f'队列长度: {RedisClient.llen(\"order_detail_tasks:queue\")}')"
```

### 5.2 查看工作线程状态
```bash
docker exec temu-omni-backend python -c "from app.services.order_detail_worker import get_worker; worker = get_worker(); print(f'工作线程运行中: {worker.is_running() if worker else False}')"
```

### 5.3 查看任务统计（通过数据库）
```sql
-- 查看任务统计
SELECT 
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries
FROM order_detail_tasks
GROUP BY status;

-- 查看失败任务详情
SELECT 
    id,
    parent_order_sn,
    error_message,
    retry_count,
    created_at
FROM order_detail_tasks
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;
```

## 六、故障排查

### 6.1 队列积压严重
1. 检查工作线程是否运行: `GET /api/sync/monitoring/health`
2. 检查Redis连接是否正常
3. 查看工作线程日志
4. 考虑增加批量处理大小或工作线程数量

### 6.2 任务失败率高
1. 查看失败任务详情: `GET /api/sync/shops/{shop_id}/orders/enrich-tasks?status=failed`
2. 检查Temu API是否正常
3. 查看错误信息，判断是API问题还是数据问题
4. 对于超过重试次数的任务，可以手动重新创建

### 6.3 工作线程未运行
1. 检查应用启动日志
2. 重启应用: `docker restart temu-omni-backend`
3. 查看是否有异常错误

## 七、最佳实践

1. **定期检查监控告警**: 建议每天查看一次监控告警
2. **关注队列长度**: 如果队列持续增长，需要检查处理速度
3. **监控任务失败率**: 失败率突然升高可能表示API或网络问题
4. **定期清理失败任务**: 对于超过7天的失败任务，可以考虑清理


