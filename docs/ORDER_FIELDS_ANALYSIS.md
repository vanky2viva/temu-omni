# 订单字段分析文档

## 签收时间字段说明

### 字段选择

经过实际测试对比，**`updateTime` 字段比 `latestDeliveryTime` 更准确**作为签收时间：

- **`latestDeliveryTime`**：系统设定的最晚送达时间（预期时间），不是实际签收时间
- **`updateTime`**：订单状态变更为已收货（status=5）时的时间戳，更接近实际签收时间

### 实现逻辑

1. **当订单状态为已收货（`parentOrderStatus = 5`）时**：
   - 使用 `updateTime` 作为签收时间
   - 这是订单状态变更为已收货的时间，更准确

2. **当订单状态不是已收货时**：
   - 使用 `latestDeliveryTime` 作为最晚送达时间（仅供参考）

### 时区处理

**所有时间戳都会转换为北京时间（UTC+8）**：

- API 返回的时间戳是 UTC 时间（秒级时间戳）
- 系统会自动将 UTC 时间转换为北京时间（UTC+8）
- 存储到数据库的时间已经是北京时间（naive datetime，不带时区信息）
- 前端显示的时间直接是北京时间，无需额外转换

### 时间转换示例

```
UTC 时间戳: 1762185214 (2025-11-03 15:53:34 UTC)
↓ 转换为北京时间（UTC+8）
北京时间: 2025-11-03 23:53:34
↓ 存储到数据库（naive datetime）
数据库值: 2025-11-03 23:53:34
```

### 对比结果

根据实际订单数据对比：

| 订单号 | latestDeliveryTime | updateTime | 时间差 | 说明 |
|--------|-------------------|------------|--------|------|
| PO-211-21833982469753634 | 2025-11-07 12:59:59 | 2025-11-03 23:53:34 | 3.55天 | updateTime更早，更接近实际签收时间 |
| PO-211-21860250389113735 | 2025-11-07 13:59:59 | 2025-11-03 04:07:35 | 4.41天 | updateTime更早，更接近实际签收时间 |

**结论**：`updateTime` 比 `latestDeliveryTime` 早 3-5 天，更接近实际签收时间。

---

# 订单字段分析文档

## 订单号: PO-211-01096246467191000

### 1. 订单列表API返回的字段（bg.order.list.v2.get）

从数据库中已同步的订单原始数据，订单列表API返回以下字段：

#### 父订单信息 (parentOrderMap)

| 字段路径 | 类型 | 说明 | 示例值 |
|---------|------|------|--------|
| `parentOrderMap.parentOrderSn` | string | 父订单号 | `PO-211-01096246467191000` |
| `parentOrderMap.parentOrderStatus` | int | 父订单状态 | `5` (已收货) |
| `parentOrderMap.parentOrderTime` | int | 父订单创建时间（时间戳） | `1762929753` |
| `parentOrderMap.updateTime` | int | 更新时间（时间戳） | `1763498018` |
| `parentOrderMap.expectShipLatestTime` | int | 预期最晚发货时间（时间戳） | `1763109000` |
| `parentOrderMap.parentShippingTime` | int | 父订单发货时间（时间戳） | `1762932944` |
| `parentOrderMap.latestDeliveryTime` | int | 最晚送达时间（时间戳） | `1763711999` |
| `parentOrderMap.orderPaymentType` | string | 支付类型 | `PPD` |
| `parentOrderMap.regionId` | int | 区域ID | `211` (USA) |
| `parentOrderMap.siteId` | int | 站点ID | `100` |
| `parentOrderMap.shippingMethod` | int | 发货方式 | `1` |
| `parentOrderMap.hasShippingFee` | null/boolean | 是否有运费 | `null` |
| `parentOrderMap.parentOrderLabel` | array | 父订单标签列表 | 见下方 |

**父订单标签 (parentOrderLabel)**:
- `soon_to_be_overdue` - 即将逾期
- `past_due` - 已逾期
- `pending_buyer_cancellation` - 待买家取消
- `pending_buyer_address_change` - 待买家地址变更
- `pending_risk_control_alert` - 待风控提醒
- `signature_required_on_delivery` - 需要签收

#### 子订单信息 (orderList[])

| 字段路径 | 类型 | 说明 | 示例值 |
|---------|------|------|--------|
| `orderList[].orderSn` | string | 子订单号 | `211-01096294963831000` |
| `orderList[].goodsId` | int | 商品ID | `601104678674866` |
| `orderList[].goodsName` | string | 商品名称 | `POP MART LABUBU 3.0...` |
| `orderList[].skuId` | int | SKU ID | `17615924742461` |
| `orderList[].spec` | string | SKU规格 | `1pc` |
| `orderList[].quantity` | int | 数量 | `1` |
| `orderList[].orderStatus` | int | 订单状态 | `5` (已收货) |
| `orderList[].orderCreateTime` | int | 订单创建时间（时间戳） | `1762929753` |
| `orderList[].orderShippingTime` | int | 订单发货时间（时间戳） | `1762932944` |
| `orderList[].fulfillmentType` | string | 履约类型 | `fulfillBySeller` |
| `orderList[].orderPaymentType` | string | 支付类型 | `PPD` |
| `orderList[].thumbUrl` | string | 商品缩略图URL | `https://img.kwcdn.com/...` |
| `orderList[].productList[]` | array | 产品列表 | 见下方 |

**产品信息 (productList[])**:
- `productList[].productId` - 产品ID
- `productList[].productSkuId` - 产品SKU ID
- `productList[].extCode` - 外部编码
- `productList[].soldFactor` - 销售因子

### 2. 订单金额查询API返回的字段（bg.order.amount.query）

**注意**: 由于当前 access_token 未授权此API，无法获取实际返回数据。根据API文档，该接口应该返回订单的成交金额信息。

**预期返回字段**（需要API授权后确认）:
- 订单金额相关字段
- 可能包含：商品金额、运费、税费、折扣、总金额等

### 3. 当前数据库中的订单字段

| 字段名 | 类型 | 说明 | 当前值 |
|--------|------|------|--------|
| `order_sn` | string | 子订单号 | `211-01096294963831000` |
| `parent_order_sn` | string | 父订单号 | `PO-211-01096246467191000` |
| `product_name` | string | 商品名称 | `POP MART LABUBU 3.0...` |
| `product_sku` | string | SKU | `1pc` |
| `quantity` | int | 数量 | `1` |
| `unit_price` | decimal | 单价 | `0.00` ⚠️ |
| `total_price` | decimal | 总价 | `0.00` ⚠️ |
| `currency` | string | 货币 | `USD` |
| `status` | enum | 订单状态 | `DELIVERED` |
| `order_time` | datetime | 下单时间 | `2025-11-12 06:42:33` |
| `shipping_time` | datetime | 发货时间 | `2025-11-12 07:35:44` |
| `delivery_time` | datetime | 送达时间 | `2025-11-21 07:59:59` |

⚠️ **问题**: 当前 `unit_price` 和 `total_price` 都是 `0.00`，说明订单列表API没有返回金额信息。

### 4. 建议的订单列表显示字段

基于以上分析，建议在订单列表中显示以下字段：

#### 必需字段
1. **父订单号** - `parentOrderMap.parentOrderSn` ✅ 已实现
2. **子订单号** - `orderList[].orderSn` ✅ 已实现
3. **商品名称** - `orderList[].goodsName` ✅ 已实现
4. **SKU** - `orderList[].spec` ✅ 已实现
5. **数量** - `orderList[].quantity` ✅ 已实现
6. **订单金额** - 需要通过 `bg.order.amount.query` 获取 ⚠️ 待实现
7. **状态** - `orderList[].orderStatus` ✅ 已实现
8. **下单时间** - `parentOrderMap.parentOrderTime` ✅ 已实现
9. **最晚发货时间** - `parentOrderMap.expectShipLatestTime` ✅ 已实现
10. **签收时间** - `parentOrderMap.latestDeliveryTime` ✅ 已实现

#### 可选字段
- **支付类型** - `parentOrderMap.orderPaymentType` (PPD等)
- **履约类型** - `orderList[].fulfillmentType` (fulfillBySeller等)
- **商品图片** - `orderList[].thumbUrl`
- **区域ID** - `parentOrderMap.regionId`

### 5. 下一步行动

1. **授权API**: 在卖家中心授权 `bg.order.amount.query` API
2. **获取金额**: 使用授权后的 access_token 调用订单金额查询接口
3. **更新显示**: 在订单列表中显示从金额查询接口获取的成交金额
4. **数据同步**: 考虑在同步订单时，同时调用金额查询接口更新订单金额

