# 订单金额和回款统计验证指南

## 📋 验证内容

本指南说明如何验证以下功能是否正常：

1. **订单金额计算**：订单金额是否正确计算和存储
2. **回款统计**：回款统计逻辑是否正确
3. **定时任务**：定时任务是否正常运行

## 🔍 验证方法

### 方法1：使用验证脚本（推荐）

运行验证脚本，自动检查所有项目：

```bash
cd backend
python scripts/verify_order_amount_and_collection.py
```

脚本会检查：
- ✅ 订单金额为0或空的订单数量
- ✅ 订单金额计算是否正确（unit_price × quantity = total_price）
- ✅ 订单金额统计汇总
- ✅ 回款统计逻辑（签收日期 + 8天）
- ✅ 定时任务调度器状态
- ✅ 订单成本计算服务

### 方法2：通过API验证

#### 检查定时任务状态

```bash
# 获取定时任务状态
curl -X GET "http://localhost:8000/api/system/scheduler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例：
```json
{
  "running": true,
  "initialized": true,
  "jobs": [
    {
      "id": "update_order_costs",
      "name": "更新订单成本",
      "next_run_time": "2024-01-15T10:30:00",
      "trigger": "interval[0:30:00]"
    }
  ],
  "message": "调度器运行中"
}
```

#### 检查回款统计

```bash
# 获取回款统计数据
curl -X GET "http://localhost:8000/api/analytics/payment-collection?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 手动触发订单成本计算

```bash
# 手动触发订单成本计算
curl -X POST "http://localhost:8000/api/order-costs/calculate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": null,
    "order_ids": null,
    "force_recalculate": false
  }'
```

### 方法3：查看应用日志

查看应用日志，确认定时任务是否正常执行：

```bash
# 查看日志（如果使用 Docker）
docker logs temu-omni-backend | grep "定时任务"

# 或查看日志文件
tail -f logs/app.log | grep "定时任务"
```

正常日志示例：
```
开始执行定时任务：更新订单成本...
订单成本更新完成 - 总计: 100, 成功: 95, 失败: 0, 跳过: 5
```

## ✅ 验证检查清单

### 订单金额验证

- [ ] 没有订单金额为0或空的订单（或数量在可接受范围内）
- [ ] 所有订单的金额计算正确（unit_price × quantity = total_price）
- [ ] 订单金额统计汇总正常
- [ ] 货币转换正确（USD → CNY）

### 回款统计验证

- [ ] 已签收订单能正确识别
- [ ] 回款日期计算正确（签收日期 + 8天）
- [ ] 回款金额统计正确
- [ ] 回款统计按店铺分组正确

### 定时任务验证

- [ ] 调度器在应用启动时自动启动
- [ ] 定时任务每30分钟执行一次
- [ ] 任务执行日志正常
- [ ] 没有任务执行失败的错误

## 🔧 常见问题排查

### 问题1：订单金额为0

**原因**：
- 订单同步时没有正确设置金额
- 商品没有供货价格

**解决方法**：
1. 运行订单成本计算脚本：
   ```bash
   python scripts/update_order_costs.py
   ```
2. 检查商品是否有供货价格
3. 检查订单同步逻辑

### 问题2：回款统计为空

**原因**：
- 没有已签收的订单
- 签收日期为空
- 回款日期不在查询范围内

**解决方法**：
1. 检查是否有已签收订单：
   ```sql
   SELECT COUNT(*) FROM orders WHERE status = 'DELIVERED' AND delivery_time IS NOT NULL;
   ```
2. 检查签收日期是否正确设置
3. 扩大查询日期范围

### 问题3：定时任务未运行

**原因**：
- 调度器未启动
- 应用启动时出错
- APScheduler 配置错误

**解决方法**：
1. 检查应用启动日志，确认调度器是否启动
2. 通过API检查调度器状态
3. 手动重启应用

## 📊 数据验证SQL查询

### 检查订单金额

```sql
-- 检查金额为0的订单
SELECT COUNT(*) 
FROM orders 
WHERE (total_price IS NULL OR total_price = 0)
  AND status NOT IN ('CANCELLED', 'REFUNDED');

-- 检查金额计算错误的订单
SELECT order_sn, unit_price, quantity, total_price, 
       (unit_price * quantity) as expected_total
FROM orders
WHERE unit_price IS NOT NULL 
  AND total_price IS NOT NULL
  AND quantity IS NOT NULL
  AND unit_price > 0
  AND total_price != (unit_price * quantity)
LIMIT 10;
```

### 检查回款统计

```sql
-- 检查已签收订单
SELECT COUNT(*) 
FROM orders 
WHERE status = 'DELIVERED' 
  AND delivery_time IS NOT NULL;

-- 检查回款日期计算
SELECT 
    order_sn,
    delivery_time,
    delivery_time + INTERVAL '8 days' as collection_date,
    total_price
FROM orders
WHERE status = 'DELIVERED'
  AND delivery_time IS NOT NULL
LIMIT 10;
```

## 🚀 定期验证建议

建议定期（每天或每周）运行验证脚本，确保系统正常运行：

1. **每日验证**：检查订单金额和回款统计
2. **每周验证**：全面验证所有功能
3. **监控告警**：设置监控，当发现问题时自动告警

## 📝 验证报告

验证脚本会生成详细的验证报告，包括：

- 订单金额统计
- 回款统计汇总
- 定时任务状态
- 发现的问题和建议

根据报告结果，可以：
1. 及时发现问题
2. 了解数据质量
3. 优化系统性能

