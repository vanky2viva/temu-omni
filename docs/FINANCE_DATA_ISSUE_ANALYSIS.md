# 财务数据来源和更新机制分析

## 问题描述

财务概览页面的总收入和总利润数据看起来不正确，需要检查数据来源和计算方式。

## ✅ 确认：供货价就是实际收入

**用户确认**：供货价（supply_price）就是实际收入，所以当前的计算逻辑是正确的。

## 当前数据流程

### 1. 订单同步时的价格计算

**文件**: `backend/app/services/sync_service.py` (第610-643行)

```python
# 使用商品的供货价（current_price）作为订单单价
supply_price = price_info.get('supply_price') or Decimal('0')
unit_price = supply_price
total_price = unit_price * Decimal(quantity)  # 供货价 × 数量

# 计算利润
unit_cost = price_info['cost_price']
total_cost = unit_cost * Decimal(quantity)
profit = total_price - total_cost  # 供货价 - 成本价
```

**✅ 确认正确**：
- `total_price` 使用**供货价**（supply_price），这是正确的，因为供货价就是实际收入
- GMV = 供货价 × 数量，这是正确的计算方式
- 利润 = 供货价 - 成本价，这也是正确的

### 2. 财务统计时的数据汇总

**文件**: `backend/app/api/analytics.py` (第567-569行)

```python
total_stats = db.query(
    func.sum(_convert_to_cny(Order.total_price, usd_rate)).label("total_gmv"),
    func.sum(_convert_to_cny(Order.total_cost, usd_rate)).label("total_cost"),
    func.sum(_convert_to_cny(Order.profit, usd_rate)).label("total_profit"),
).filter(and_(*filters)).first()
```

**✅ 确认正确**：
- `total_gmv` 统计的是所有订单的 `total_price` 总和
- 由于 `total_price` 是供货价（实际收入），所以统计是正确的
- 货币转换：USD订单会乘以汇率转换为CNY，CNY订单保持不变

### 3. 前端显示

**文件**: `frontend/src/pages/Finance.tsx` (第435、504行)

```typescript
// 总收入
¥{((monthlyStats?.total_gmv || 0) / 1000).toFixed(1)}k

// 总利润
¥{((monthlyStats?.total_profit || 0) / 1000).toFixed(1)}k
```

## 数据来源分析

### 订单价格字段

| 字段 | 当前值 | 应该的值 | 说明 |
|------|--------|----------|------|
| `Order.total_price` | 供货价（supply_price） | 实际销售价格 | 当前使用供货价，导致GMV被低估 |
| `Order.unit_price` | 供货价（supply_price） | 实际销售单价 | 同上 |
| `Order.profit` | 供货价 - 成本价 | 实际销售价 - 成本价 | 利润计算可能不准确 |

### 数据更新机制

1. **订单同步时**：
   - 从商品表获取 `supply_price`（供货价）
   - 计算 `total_price = supply_price × quantity`
   - 计算 `profit = total_price - total_cost`
   - **未获取实际销售价格**

2. **订单更新时**：
   - 如果订单已存在，会重新匹配商品并更新价格
   - 但仍然使用供货价，不是实际销售价格

3. **财务统计时**：
   - 直接汇总 `Order.total_price` 和 `Order.profit`
   - 由于数据源是供货价，统计结果不准确

## 实际数据检查结果

### 当前数据库统计（所有有效订单）

- **总订单数**: 6,528（按父订单号去重）
- **总GMV**: 2,043,901.98 CNY
- **总成本**: 1,966,944.86 CNY
- **总利润**: 76,957.12 CNY
- **利润率为0的订单**: 2个（0.03%）
- **利润为负的订单**: 182个（2.79%），总利润为 -225,112.60 CNY

### 货币分布

- **USD订单**: 496个，GMV = 568,596.40 CNY（转换后），利润 = -136,447.80 CNY
- **CNY订单**: 6,322个，GMV = 1,475,305.58 CNY，利润 = 213,404.92 CNY
- **汇率**: USD/CNY = 7.1（默认汇率）

## 可能的问题点

### 1. 利润为负的订单

- **发现**：有182个订单的利润为负数
- **原因**：这些订单的成本价高于供货价
- **影响**：这是正常的业务情况（可能由于成本波动、促销等原因）
- **建议**：检查这些订单的成本价设置是否正确

### 2. 未匹配商品的订单

- **发现**：有2个订单的 `total_price` 为 0（未匹配到商品）
- **影响**：这些订单不会计入 GMV，但数量很少（0.03%），影响可忽略
- **建议**：检查这些订单，确保商品匹配逻辑正确

### 3. 货币转换

- **当前汇率**: USD/CNY = 7.1（默认汇率）
- **问题**：如果实际汇率与默认汇率差异较大，可能导致USD订单的GMV和利润不准确
- **建议**：配置极速API密钥，使用实时汇率

### 4. NULL值处理

- **发现**：有2个订单的 `profit` 为 NULL
- **SQL处理**：`func.sum()` 会自动忽略 NULL 值，所以这些订单不会影响利润统计
- **影响**：这些订单的GMV会被计入，但利润不会被计入

## 需要检查的问题

### 1. 利润为负的订单

**检查SQL**：
```sql
-- 查看利润为负的订单详情
SELECT 
    order_sn,
    product_sku,
    total_price,
    total_cost,
    profit,
    currency,
    order_time
FROM orders
WHERE status IN ('PROCESSING', 'SHIPPED', 'DELIVERED')
  AND profit < 0
ORDER BY profit ASC
LIMIT 20;
```

**可能原因**：
- 成本价设置错误（成本价 > 供货价）
- 商品价格调整（供货价降低，但成本价未更新）
- 促销活动导致供货价低于成本价

### 2. 未匹配商品的订单

**检查SQL**：
```sql
-- 查看价格为0的订单
SELECT 
    order_sn,
    product_sku,
    spu_id,
    product_name,
    total_price,
    order_time
FROM orders
WHERE status IN ('PROCESSING', 'SHIPPED', 'DELIVERED')
  AND total_price = 0;
```

**可能原因**：
- 商品未添加到商品列表
- SKU匹配逻辑有问题（extCode、productSkuId、spu_id都不匹配）

### 3. 汇率准确性

**检查**：
- 当前使用默认汇率 7.1
- 如果实际汇率差异较大，USD订单的GMV和利润会不准确
- **建议**：配置 `JISUAPI_KEY` 环境变量，使用实时汇率

### 4. 日期范围筛选

**检查**：
- 财务概览页面默认显示全部数据（dateRange = null）
- 确认前端传递的日期范围是否正确
- 确认后端是否正确处理日期范围筛选

## 需要检查的问题

1. **供货价 vs 实际销售价格**：
   - 供货价（supply_price）是否就是卖家实际收到的金额？
   - 还是买家支付的价格更高？

2. **订单金额查询接口**：
   - `get_order_amount` 接口返回的是什么价格？
   - 是实际销售价格还是供货价？

3. **数据一致性**：
   - 当前有多少订单的 `total_price` 为 0（未匹配商品）？
   - 这些订单是否应该计入 GMV？

4. **利润计算逻辑**：
   - 利润应该是：实际收入 - 成本
   - 还是：供货价 - 成本（如果供货价就是实际收入）？

## 数据验证检查清单

### ✅ 已确认正确的部分

1. **数据来源**：供货价就是实际收入 ✅
2. **计算逻辑**：GMV = sum(供货价 × 数量) ✅
3. **利润计算**：利润 = 供货价 - 成本价 ✅
4. **货币转换**：USD订单转换为CNY，CNY订单保持不变 ✅
5. **订单筛选**：只统计有效订单（PROCESSING、SHIPPED、DELIVERED） ✅

### ⚠️ 需要检查的部分

1. **利润为负的订单**：
   - 检查182个利润为负的订单
   - 确认成本价设置是否正确
   - 确认是否存在业务逻辑问题

2. **未匹配商品的订单**：
   - 检查2个价格为0的订单
   - 确认商品匹配逻辑是否正确
   - 确认是否需要手动匹配商品

3. **汇率准确性**：
   - 当前使用默认汇率 7.1
   - 如果实际汇率差异较大，建议配置实时汇率API

4. **日期范围筛选**：
   - 确认前端传递的日期范围参数
   - 确认后端是否正确处理日期范围
   - 确认时区转换是否正确（香港时区 UTC+8）

## 建议的检查步骤

1. **检查利润为负的订单**：
   ```sql
   SELECT 
       order_sn,
       product_sku,
       total_price as supply_price,
       total_cost,
       profit,
       (total_cost - total_price) as loss_amount,
       currency
   FROM orders
   WHERE status IN ('PROCESSING', 'SHIPPED', 'DELIVERED')
     AND profit < 0
   ORDER BY profit ASC
   LIMIT 10;
   ```

2. **检查未匹配商品的订单**：
   ```sql
   SELECT 
       order_sn,
       product_sku,
       spu_id,
       product_name,
       order_time
   FROM orders
   WHERE status IN ('PROCESSING', 'SHIPPED', 'DELIVERED')
     AND total_price = 0;
   ```

3. **验证GMV计算**：
   - 从Temu后台选择几个订单，记录实际收入
   - 对比数据库中对应订单的 `total_price`
   - 确认是否一致

4. **验证利润计算**：
   - 检查利润为负的订单的成本价
   - 确认成本价是否设置正确
   - 确认是否存在业务逻辑问题（如促销、价格调整等）

## 总结

**数据计算逻辑是正确的**，因为：
- ✅ 供货价就是实际收入
- ✅ GMV = sum(供货价 × 数量) 是正确的
- ✅ 利润 = 供货价 - 成本价 是正确的
- ✅ 货币转换逻辑正确

**可能的问题**：
- ⚠️ 利润为负的订单需要检查（182个订单）
- ⚠️ 未匹配商品的订单需要处理（2个订单）
- ⚠️ 汇率可能需要使用实时汇率而不是默认汇率

**建议**：
1. 检查利润为负的订单，确认成本价设置是否正确
2. 处理未匹配商品的订单，确保商品匹配逻辑正确
3. 配置实时汇率API，提高USD订单的准确性

