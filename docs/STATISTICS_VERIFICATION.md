# 销量统计准确性验证报告

## 验证时间
2025-11-28

## 统计规则确认

### 1. 订单数统计规则
- **规则**：按父订单去重统计
- **实现**：使用 `UnifiedStatisticsService.get_parent_order_key()`
  - 如果 `parent_order_sn` 存在，使用 `parent_order_sn`
  - 否则使用 `order_sn`
- **代码位置**：`backend/app/services/unified_statistics.py:38-48`
- **验证结果**：✓ 正确实现

### 2. 日期统计规则
- **规则**：使用北京时间（UTC+8）提取日期
- **实现**：使用 `get_date_in_beijing_timezone()` 函数
  - 将 naive datetime（表示北京时间）转换为带时区的时间戳
  - 使用 PostgreSQL 的 `timezone('Asia/Shanghai', column)` 函数
  - 然后提取日期部分
- **代码位置**：`backend/app/api/analytics.py:36-53`
- **验证结果**：✓ 已修复，现在正确使用北京时间

### 3. 订单状态过滤
- **规则**：只统计有效订单
- **有效状态**：
  - `PROCESSING`（待发货）
  - `SHIPPED`（已发货）
  - `DELIVERED`（已签收）
- **代码位置**：`backend/app/services/unified_statistics.py:50-62`
- **验证结果**：✓ 正确实现

### 4. 销量统计
- **规则**：子订单内商品数量累计（`quantity` 之和）
- **实现**：使用 `func.sum(Order.quantity)`
- **代码位置**：`backend/app/api/analytics.py:564, 578`
- **验证结果**：✓ 正确实现

## 关键代码片段

### 按天统计趋势（使用北京时间）
```python
# 获取父订单键（用于趋势统计）
parent_order_key = UnifiedStatisticsService.get_parent_order_key()

# 使用北京时间提取日期
date_expr = get_date_in_beijing_timezone(Order.order_time)

# 按天统计趋势
daily_trends = db.query(
    date_expr.label("date"),
    func.sum(Order.quantity).label("quantity"),
    func.count(func.distinct(parent_order_key)).label("orders"),  # 按父订单号去重统计
).filter(and_(*filters)).group_by(
    date_expr
).order_by(
    date_expr
).all()
```

### 按店铺统计趋势（使用北京时间）
```python
shop_trends = db.query(
    date_expr.label("date"),
    Shop.shop_name.label("shop_name"),
    func.sum(Order.quantity).label("quantity"),
    func.count(func.distinct(parent_order_key)).label("orders"),  # 按父订单号去重统计
).join(
    Shop, Shop.id == Order.shop_id
).filter(and_(*filters)).group_by(
    date_expr, Shop.shop_name
).order_by(
    date_expr, Shop.shop_name
).all()
```

## 验证结果

### 数据库时区检查
- **当前设置**：UTC
- **影响**：已通过代码修复，使用 `timezone('Asia/Shanghai', column)` 确保日期提取正确

### 父订单去重验证
- **总订单记录数（不去重）**：8,896
- **父订单数（去重后）**：8,508
- **子订单数**：388
- **验证结果**：✓ 去重逻辑正确

### 日期统计验证（最近7天）
- **时间范围**：2025-11-21 至 2025-11-28（北京时间）
- **总订单数**：1,287（按父订单去重）
- **总销量**：1,445 件
- **每日统计汇总**：
  - 2025-11-21: 109 单, 123 件
  - 2025-11-22: 148 单, 176 件
  - 2025-11-23: 242 单, 272 件
  - 2025-11-24: 230 单, 260 件
  - 2025-11-25: 224 单, 238 件
  - 2025-11-26: 189 单, 211 件
  - 2025-11-27: 145 单, 165 件
- **汇总一致性**：
  - ✓ 订单数汇总一致（1,287 = 1,287）
  - ✓ 销量汇总一致（1,445 = 1,445）

## 结论

✅ **销量统计数据准确**

所有统计规则已正确实现：
1. ✅ 订单数按父订单去重统计
2. ✅ 日期使用北京时间（UTC+8）提取
3. ✅ 只统计有效订单状态
4. ✅ 销量为子订单商品数量累计
5. ✅ 按天和按店铺统计的数据汇总一致

## 相关文件

- `backend/app/api/analytics.py` - 销量统计 API
- `backend/app/services/unified_statistics.py` - 统一统计服务
- `backend/scripts/verify_statistics.py` - 验证脚本

## 运行验证

```bash
cd /Users/vanky/code/temu-Omni/backend
python3 scripts/verify_statistics.py
```











