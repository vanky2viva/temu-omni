# 履约类型处理说明

## 当前实现状态

### ✅ 已确认：所有履约类型的订单都会被统计

经过代码检查，**无论订单的履约类型（`fulfillmentType`）是什么，所有同步到的订单都会被统计入订单中**。

### 1. 订单同步逻辑

**位置**：`backend/app/services/sync_service.py`

**处理流程**：
1. 从 Temu API 获取订单数据
2. 遍历所有订单（`order_list`）
3. 处理每个子订单（`order_item`）
4. **没有根据 `fulfillmentType` 过滤订单**

**关键代码**：
```python
# 处理父订单下的每个子订单
for order_item in order_list:
    order_sn = order_item.get('orderSn')
    if not order_sn:
        logger.warning(f"子订单缺少orderSn: {order_item}")
        continue  # 只跳过缺少订单号的订单，不根据履约类型过滤
    
    # 保存并处理订单
    self._process_order_legacy(order_item, parent_order, order_data, raw_order, existing_orders_map)
```

**结论**：✅ 所有履约类型的订单都会被同步到数据库

### 2. 订单统计逻辑

**位置**：`backend/app/api/analytics.py` - `build_sales_filters()`

**过滤条件**：
- ✅ 只根据订单状态过滤（`PROCESSING`、`SHIPPED`、`DELIVERED`）
- ✅ 根据时间范围过滤
- ✅ 根据店铺、负责人、地区、SKU 过滤
- ❌ **不根据履约类型过滤**

**关键代码**：
```python
def build_sales_filters(...):
    filters = []
    
    # 订单状态筛选：只统计有效订单
    filters.append(Order.status.in_([
        OrderStatus.PROCESSING,  # 待发货
        OrderStatus.SHIPPED,     # 已发货
        OrderStatus.DELIVERED    # 已签收
    ]))
    
    # 时间、店铺、负责人等筛选...
    # 注意：没有根据 fulfillmentType 过滤
    
    return filters
```

**结论**：✅ 所有履约类型的订单都会被统计（只要订单状态符合条件）

### 3. 订单模型

**位置**：`backend/app/models/order.py`

**当前字段**：
- 订单基本信息（订单号、父订单号等）
- 商品信息（SKU、SPU、数量等）
- 价格信息（单价、总价、成本、利润）
- 订单状态（`OrderStatus` 枚举）
- 时间信息（下单时间、发货时间等）
- **没有 `fulfillmentType` 字段**

**说明**：
- 虽然订单模型中没有 `fulfillmentType` 字段，但这不影响统计
- 所有同步到的订单都会被保存到数据库
- 统计时不会根据履约类型过滤

## 验证方法

### 1. 检查同步的订单数量

```sql
-- 查看所有订单（不区分履约类型）
SELECT COUNT(*) FROM orders;

-- 查看不同状态的订单数量
SELECT status, COUNT(*) 
FROM orders 
GROUP BY status;
```

### 2. 检查统计是否包含所有订单

运行验证脚本：
```bash
cd /Users/vanky/code/temu-Omni/backend
python3 scripts/verify_statistics.py
```

脚本会验证：
- 总订单记录数
- 父订单数（去重后）
- 统计口径一致性

## 总结

✅ **确认：无论订单的履约类型（`fulfillmentType`）是什么，所有同步到的订单都会被统计入订单中。**

### 关键点：
1. **订单同步**：不根据履约类型过滤，所有订单都会被同步
2. **订单统计**：不根据履约类型过滤，所有符合条件的订单都会被统计
3. **统计条件**：只根据订单状态（`PROCESSING`、`SHIPPED`、`DELIVERED`）过滤

### 如果需要存储履约类型信息

如果将来需要在订单模型中存储履约类型信息，可以：
1. 在 `Order` 模型中添加 `fulfillment_type` 字段
2. 在同步时从 API 数据中提取并保存
3. 但统计时仍然不根据履约类型过滤

## 相关文件

- `backend/app/models/order.py` - 订单模型
- `backend/app/services/sync_service.py` - 订单同步服务
- `backend/app/api/analytics.py` - 统计 API（`build_sales_filters` 函数）
- `backend/app/services/unified_statistics.py` - 统一统计服务









