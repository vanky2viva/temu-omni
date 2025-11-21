# Temu 订单列表 API 返回字段说明

## API 接口

- **接口**: `bg.order.list.v2.get`
- **方法**: POST
- **URL**: `https://openapi-b-us.temu.com/openapi/router`

## 响应数据结构

### 顶层结构

```json
{
  "success": true,
  "result": {
    "totalItemNum": 4764,        // 总订单数
    "pageItems": [...]           // 订单项数组
  }
}
```

### pageItems 数组结构

每个 `pageItem` 包含一个父订单（parentOrder）和其下的子订单列表（orderList）：

```json
{
  "parentOrderMap": { ... },     // 父订单信息
  "orderList": [ ... ]           // 子订单列表
}
```

---

## 父订单信息 (parentOrderMap)

### 基本信息

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `parentOrderSn` | String | 父订单编号 | `"PO-211-02066072965752676"` |
| `parentOrderStatus` | Integer | 父订单状态 | `1` = 待发货, `2` = 待确认, `3` = 已确认 |
| `parentOrderTime` | Long | 父订单创建时间（Unix时间戳，秒） | `1763622700` |
| `parentShippingTime` | Long/null | 父订单发货时间 | `null` 或时间戳 |
| `updateTime` | Long | 最后更新时间 | `1763622776` |

### 区域和站点信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `regionId` | Integer | 区域ID | `211` = 美国 |
| `siteId` | Integer | 站点ID | `100` = 主站点 |

### 订单标签 (parentOrderLabel)

订单标签数组，每个标签包含 `name` 和 `value`：

| 标签名 | 说明 |
|--------|------|
| `soon_to_be_overdue` | 即将逾期 |
| `past_due` | 已逾期 |
| `pending_buyer_cancellation` | 待买家取消 |
| `pending_buyer_address_change` | 待买家修改地址 |
| `pending_risk_control_alert` | 风控预警 |
| `signature_required_on_delivery` | 需要签收 |

### 物流和履约信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `shippingMethod` | Integer | 物流方式 | `1` = 标准物流 |
| `latestDeliveryTime` | Long | 最晚送达时间（Unix时间戳） | `1765515599` |
| `expectShipLatestTime` | Long/null | 期望最晚发货时间 | `null` 或时间戳 |
| `fulfillmentWarning` | String[] | 履约警告列表 | 如：`["RESTRICT_USPS_SELF_SHIPPING"]` |
| `isShipmentConsolidatedByMainMall` | Boolean | 是否由主店铺合并发货 | `false` |

### 支付信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `orderPaymentType` | String | 支付类型 | `"PPD"` = 预付 |
| `hasShippingFee` | Boolean/null | 是否有运费 | `null` |

### 其他信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `batchOrderNumberList` | Array/null | 批次订单号列表 | `null` |
| `parentOrderPendingFinishTime` | Long/null | 待完成时间 | `null` 或时间戳 |

---

## 子订单信息 (orderList)

每个子订单包含以下信息：

### 订单标识

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `orderSn` | String | 子订单编号 | `"211-02066112942712676"` |
| `goodsId` | Long | 商品ID | `601104248302027` |
| `skuId` | Long | SKU ID | `17613836106883` |

### 商品信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `goodsName` | String | 商品名称（英文） |
| `originalGoodsName` | String | 商品名称（原始语言，如中文） |
| `spec` | String | 规格 | `"1"`, `"1pc"` |
| `originalSpecName` | String | 原始规格名称 |
| `thumbUrl` | String | 商品缩略图URL |

### 数量信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `quantity` | Integer | 当前数量（应履约数量） |
| `originalOrderQuantity` | Integer | 原始订单数量 |
| `canceledQuantityBeforeShipment` | Integer | 发货前取消数量 |

### 订单状态

| 字段名 | 类型 | 说明 | 状态值 |
|--------|------|------|--------|
| `orderStatus` | Integer | 订单状态 | `1` = 待发货, `2` = 待确认, `3` = 已确认 |
| `isCancelledDuringPending` | Boolean | 是否在待处理期间被取消 | `false` |

### 订单标签 (orderLabel)

| 标签名 | 说明 |
|--------|------|
| `customized_products` | 定制商品 |
| `US_to_CA` | 美国到加拿大 |
| `Y2_advance_sale` | Y2预售 |

### 履约信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `fulfillmentType` | String | 履约类型 | `"fulfillBySeller"` = 卖家履约 |
| `fulfillmentWarning` | String[] | 履约警告 | `[]` |
| `isShipmentConsolidatedByMainMall` | Boolean | 是否由主店铺合并发货 |

### 仓库信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `inventoryDeductionWarehouseId` | String | 库存扣减仓库ID | `"WH-05065776619650305"` |
| `inventoryDeductionWarehouseName` | String | 库存扣减仓库名称 | `"集滕"`, `"MSS-Y2纽约1号仓"` |

### 时间信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `orderCreateTime` | Long | 订单创建时间（Unix时间戳，秒） |
| `orderShippingTime` | Long/null | 订单发货时间 |
| `earliestTimeGetShippingDocument` | Long/null | 最早获取物流单时间 |
| `earliestTimeBuyShippingLabel` | Long/null | 最早购买物流标签时间 |

### 产品关联信息 (productList)

每个订单可能关联多个产品：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `productSkuId` | Long | 产品SKU ID |
| `productId` | Long | 产品ID |
| `extCode` | String | 外部编码 | `"LBB4-A-US"` |
| `soldFactor` | Integer | 销售因子 | `1` |

### 支付信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `orderPaymentType` | String | 支付类型 | `"PPD"` = 预付 |

---

## 订单状态说明

### 父订单状态 (parentOrderStatus)

- `1` - 待发货（Pending）
- `2` - 待确认（Pending Confirmation）
- `3` - 已确认（Confirmed）

### 子订单状态 (orderStatus)

- `1` - 待发货（Pending）
- `2` - 待确认（Pending Confirmation）
- `3` - 已确认（Confirmed）

---

## 履约警告类型 (fulfillmentWarning)

| 警告类型 | 说明 |
|----------|------|
| `RESTRICT_USPS_SELF_SHIPPING` | 限制使用 USPS 自发货 |
| `RESTRICT_FEDEX_SELF_SHIPPING` | 限制使用 FedEx 自发货 |
| `BLOCK_LOGISTICS_PROVIDERS_{UniUni}` | 阻止特定物流提供商 |
| `SUGGEST_SIGNATURE_ON_DELIVERY` | 建议签收 |

---

## 完整示例

```json
{
  "success": true,
  "result": {
    "totalItemNum": 4764,
    "pageItems": [
      {
        "parentOrderMap": {
          "parentOrderSn": "PO-211-02066072965752676",
          "parentOrderStatus": 1,
          "parentOrderTime": 1763622700,
          "regionId": 211,
          "siteId": 100,
          "shippingMethod": 1,
          "orderPaymentType": "PPD",
          "latestDeliveryTime": 1765515599,
          "fulfillmentWarning": [
            "RESTRICT_USPS_SELF_SHIPPING",
            "RESTRICT_FEDEX_SELF_SHIPPING"
          ],
          "parentOrderLabel": [
            {"name": "soon_to_be_overdue", "value": 0},
            {"name": "past_due", "value": 0}
          ]
        },
        "orderList": [
          {
            "orderSn": "211-02066112942712676",
            "goodsId": 601104248302027,
            "skuId": 17613836106883,
            "goodsName": "POP MART Labubu 4.0...",
            "originalGoodsName": "POP MART Labubu 4.0心底密码系列...",
            "quantity": 1,
            "orderStatus": 1,
            "orderCreateTime": 1763622700,
            "inventoryDeductionWarehouseName": "集滕",
            "productList": [
              {
                "productSkuId": 22702488574,
                "productId": 7981568052,
                "extCode": "LBB4-A-US",
                "soldFactor": 1
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

## 注意事项

1. **父子订单关系**：一个父订单（parentOrder）可以包含多个子订单（orderList）
2. **时间戳格式**：所有时间字段使用 Unix 时间戳（秒级）
3. **状态值**：订单状态使用数字编码，需要转换为对应的状态枚举
4. **多语言**：商品名称包含英文和原始语言两个版本
5. **数量字段**：注意区分 `quantity`（当前应履约数量）和 `originalOrderQuantity`（原始订单数量）




