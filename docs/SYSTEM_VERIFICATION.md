# 系统运行状态验证指南

## ✅ 系统已正常访问

从财务页面可以看到系统已经可以正常访问，数据正常显示。

## 🔍 功能验证清单

### 1. 页面访问验证

- [x] 财务管理页面可以访问
- [x] 本月概览数据正常显示
- [x] 汇总统计数据正常显示
- [x] 回款趋势图表正常显示

### 2. 数据验证

#### 已正常显示的数据
- ✅ 本月总收入: ¥988,965.00
- ✅ 本月总利润: ¥142,674.00
- ✅ 利润率: 14.43%
- ✅ 总订单数: 5,947 单
- ✅ 总销售额: ¥1,377,745
- ✅ 总成本: ¥1,177,363
- ✅ 总利润: ¥200,382
- ✅ 回款趋势图表（echofrog 和 festival finds 店铺）

#### 需要检查的数据
- ⚠️ 预估回款数据（可能因为订单成本未计算完成）
- ⚠️ 明细数据表格

### 3. 预估回款数据说明

**预估回款数据**需要满足以下条件才会显示：
1. 订单必须有成本信息（`unit_cost`, `total_cost`）
2. 订单必须有利润信息（`profit`）
3. 订单金额必须大于0

**如果预估回款为空，请执行：**

```bash
# 在服务器上执行
cd /path/to/temu-Omni
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/update_order_costs.py
```

或者通过前端页面点击"计算订单成本"按钮。

---

## 🔧 系统功能验证

### 验证1: 检查定时任务

```bash
# 在服务器上执行
curl -X GET "http://localhost:8000/api/system/scheduler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 调度器应该显示为运行状态，包含3个任务：
- 更新订单成本（每30分钟）
- 同步订单数据（每30分钟）
- 同步商品数据（每60分钟）

### 验证2: 检查数据同步

```bash
# 检查最后同步时间
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.core.database import SessionLocal; from app.models.shop import Shop; db = SessionLocal(); shops = db.query(Shop).all(); [print(f'{s.shop_name}: {s.last_sync_at}') for s in shops]"
```

### 验证3: 检查订单成本计算

```bash
# 运行验证脚本
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/verify_order_amount_and_collection.py
```

---

## 📊 数据完整性检查

### 检查订单金额

```sql
-- 检查没有金额的订单数量
SELECT COUNT(*) 
FROM orders 
WHERE (total_price IS NULL OR total_price = 0)
  AND status NOT IN ('CANCELLED', 'REFUNDED');
```

### 检查订单成本

```sql
-- 检查没有成本的订单数量
SELECT COUNT(*) 
FROM orders 
WHERE (unit_cost IS NULL OR total_cost IS NULL)
  AND status NOT IN ('CANCELLED', 'REFUNDED');
```

### 检查回款数据

```sql
-- 检查已签收订单数量
SELECT COUNT(*) 
FROM orders 
WHERE status = 'DELIVERED' 
  AND delivery_time IS NOT NULL;
```

---

## 🎯 系统运行状态总结

### ✅ 正常运行的功能

1. **前端访问** - 页面可以正常访问
2. **数据展示** - 财务数据正常显示
3. **图表渲染** - 回款趋势图表正常显示
4. **数据统计** - 本月概览和汇总统计正常

### ⚠️ 需要关注的功能

1. **预估回款** - 如果为空，需要计算订单成本
2. **明细数据** - 检查是否正常加载
3. **定时任务** - 确认是否正常运行

---

## 🚀 优化建议

### 1. 确保订单成本已计算

```bash
# 手动触发成本计算
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/update_order_costs.py
```

### 2. 检查定时任务状态

通过API或日志确认定时任务正常运行。

### 3. 监控系统日志

定期查看日志，确保没有错误：

```bash
docker-compose -f docker-compose.prod.yml logs --tail=50
```

---

*系统已基本正常运行，建议定期检查数据完整性和定时任务状态。*


