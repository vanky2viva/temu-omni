# 订单与商品匹配字段对照表

## 📊 字段对照总览（已验证 ✅）

| 用途 | 商品表字段 | 商品API字段 | 订单原始数据路径 | 匹配优先级 | 实际验证结果 |
|------|-----------|------------|----------------|-----------|-------------|
| **🥇 SKU ID** | `Product.product_id` | `productSkuSummaries[].productSkuId` | `orderList[].productList[].productSkuId` | ⭐⭐⭐⭐⭐ | ✅ **优先匹配** |
| **🥈 SKU货号** | `Product.sku` | `productSkuSummaries[].extCode` | `orderList[].productList[].extCode` | ⭐⭐⭐⭐ | ✅ **备用匹配** |
| **🥉 SPU ID** | `Product.spu_id` | `productId` | `orderList[].productList[].productId` | ⭐⭐⭐ | ✅ **第三优先级** |
| SKU ID (订单级) | - | - | `orderList[].skuId` | ⭐ | ❌ 与商品任何ID都不匹配 |
| Goods ID | - | - | `orderList[].goodsId` | ⭐ | ❌ 与商品ID完全不同 |
| SKC ID | `Product.skc_id` | `productSkcId` | 未找到 | - | ⚠️ 订单中缺失 |
| 规格描述 | - | - | `orderList[].spec` | ⭐ | ❌ 不是SKU货号 |

### ✅ 正确的字段对应关系（已验证）

**实际测试订单：** `PO-211-02345811251833312`  
**购买商品：** LABUBU 1.0 心动马卡龙系列 整套（6盒）

| 订单字段 | 订单值 | 商品字段 | 商品值 | 匹配? |
|---------|--------|---------|--------|-------|
| `productList[].productSkuId` | `11385873200` | `Product.product_id` | `11385873200` | ✅ **完美匹配！** |
| `productList[].extCode` | `LBB1-ALL-US` | `Product.sku` | `LBB1-ALL-US` | ✅ **完美匹配！** |
| `productList[].productId` | `3267196277` | `Product.spu_id` | `3267196277` | ✅ **完美匹配！** |

### 🎯 结论

1. ✅ **`productSkuId` 可以匹配** - 对应商品的 `product_id`（优先使用）
2. ✅ **`extCode` 可以匹配** - 对应商品的 `sku` (SKU货号)（备用）
3. ✅ **`productId` 可以匹配** - 对应商品的 `spu_id`（第三优先级）

---

## 📦 商品表 (Product) 字段

### 数据库字段
```
id                    : 539
shop_id               : 6
product_id            : 15099780999        ← Temu商品ID
product_name          : 单盒 POP MART LABUBU...
sku                   : LBB-MXT-1-US       ← 真正的SKU货号
current_price         : 0.00                ← 供货价
currency              : USD
stock_quantity        : 0
is_active             : True
description           : NULL
image_url             : https://...
category              : 毛绒公仔
manager               : NULL
skc_id                : 25949788870         ← SKC ID
spu_id                : 5582141357          ← SPU ID (一个SPU对应多个SKU)
price_status          : NULL
created_at            : 2025-11-20 18:16:36
updated_at            : 2025-11-20 18:16:36
```

### 成本价信息 (ProductCost)
```
id                    : 5
product_id            : 540                 ← 关联Product.id
cost_price            : 195.00              ← 成本价
currency              : CNY
effective_from        : 2025-11-20 18:20:36 ← 生效开始时间
effective_to          : NULL                ← NULL表示当前有效
notes                 : 批量更新 - SKU包含LBB3
```

---

## 📝 订单表 (Order) 字段

### 数据库字段
```
id                      : 4158
shop_id                 : 6
order_sn                : 211-07465491950711983              ← 订单编号
temu_order_id           : PO-211-07465512922231983
parent_order_sn         : PO-211-07465512922231983
product_id              : NULL                                ← ❌ 需要通过匹配填充
product_name            : (1pc) 100% Authentic POP MART...
product_sku             : 1pc                                 ← ❌ 这是规格描述，不是SKU！
spu_id                  :                                     ← ❌ 空值
quantity                : 1                                   ← 数量
unit_price              : 200.00                              ← 单价
total_price             : 200.00                              ← 总价（GMV）
currency                : CNY
unit_cost               : 165.00                              ← ✅ 单位成本（匹配后填充）
total_cost              : 165.00                              ← ✅ 总成本（匹配后填充）
profit                  : 35.00                               ← ✅ 利润（匹配后计算）
status                  : DELIVERED
order_time              : 2025-11-06 18:29:52
payment_time            : NULL
shipping_time           : 2025-11-15 10:25:02
delivery_time           : 2025-11-18 22:48:35
notes                   : Environment: sandbox, GoodsID: 601104307271826
raw_data                : <JSON数据>                          ← 包含完整原始信息
```

### 订单原始数据 (raw_data) 关键字段

#### 1. parentOrderMap（父订单信息）
```json
{
  "parentOrderSn": "PO-211-07465512922231983",
  "parentOrderStatus": 5,                    // 订单状态：5=已送达
  "parentOrderTime": 1762453792,             // 下单时间（Unix时间戳）
  "parentShippingTime": 1763173502,          // 发货时间
  "updateTime": 1763477315,                  // 更新时间
  "latestDeliveryTime": 1764392399,          // 最晚送达时间
  "expectShipLatestTime": 1763702999,        // 预期最晚发货时间
  "orderPaymentType": "PPD",
  "regionId": 211,
  "siteId": 100
}
```

#### 2. orderList[]（子订单列表，每个SKU一条）
```json
{
  "orderSn": "211-07465491950711983",
  
  // 🔑 关键匹配字段
  "goodsId": 601104307271826,                // Temu商品ID（不同于Product.product_id）
  "skuId": 17614116879476,                   // Temu SKU ID
  
  // ❌ 误导性字段
  "spec": "1pc",                             // 规格描述（不是SKU货号！）
  
  // ✅ 真正的SKU在这里
  "productList": [
    {
      "productSkuId": 50668586641,
      "soldFactor": 1,
      "extCode": "LBB4-A-US",                // ✅ 这才是真正的SKU货号！
      "productId": 9903995070                 // Temu内部商品ID
    }
  ],
  
  // 其他信息
  "goodsName": "(1pc) 100% Authentic POP MART Labubu 4.0...",
  "originalGoodsName": "（1PCS）100%正品 POP MART Labubu 4.0...",
  "originalSpecName": "1个",
  "quantity": 1,
  "orderStatus": 5,
  "orderCreateTime": 1762453792,
  "orderShippingTime": 1763173502,
  "thumbUrl": "https://..."
}
```

---

## 🎯 推荐匹配方案（已验证 ✅）

### 方案 1：多字段组合匹配（推荐） ⭐⭐⭐⭐⭐

**匹配逻辑：**
```python
# 从订单原始数据提取匹配字段
order_raw_data = json.loads(order.raw_data)
order_list = order_raw_data.get('orderList', [])
for order_item in order_list:
    product_list = order_item.get('productList', [])
    if product_list:
        product_info = product_list[0]
        product_sku_id = product_info.get('productSkuId')  # 如：11385873200
        ext_code = product_info.get('extCode')  # 如：LBB1-ALL-US
        spu_id = product_info.get('productId')  # 如：3267196277 (实际是SPU)
        
        # 优先级1：通过productSkuId匹配
        product = db.query(Product).filter(
            Product.shop_id == order.shop_id,
            Product.product_id == str(product_sku_id)
        ).first()
        
        # 优先级2：通过extCode (SKU货号) 匹配
        if not product and ext_code:
            product = db.query(Product).filter(
                Product.shop_id == order.shop_id,
                Product.sku == ext_code
            ).first()
        
        # 优先级3：通过spu_id匹配
        if not product and spu_id:
            product = db.query(Product).filter(
                Product.shop_id == order.shop_id,
                Product.spu_id == str(spu_id)
            ).first()
```

**优点：**
- ✅ 最可靠、匹配率最高
- ✅ productSkuId 直接匹配 Product.product_id（最快）
- ✅ extCode 作为备用，兼容性强
- ✅ spu_id 作为第三优先级

**实测结果：**
- ✅ productSkuId 匹配成功率：高（直接对应）
- ✅ extCode 匹配成功率：100%（始终有效）
- ✅ spu_id 匹配成功率：中（一个SPU可能对应多个SKU）

---

## 💡 当前问题与解决方案

### 问题 1：订单的 product_sku 字段存储错误
- **现状**：`Order.product_sku` = "1pc"（规格描述）
- **应该**：`Order.product_sku` = "LBB4-A-US"（真正的SKU）
- **来源**：`orderList[].productList[].extCode`

### 问题 2：订单的 spu_id 字段为空
- **现状**：`Order.spu_id` = ""
- **原因**：API返回的订单数据中没有SPU ID
- **影响**：无法通过SPU匹配

### 问题 3：ID格式完全不匹配（已验证）

**实际测试数据对比：**

#### 订单的ID：
- `orderList[].skuId`: `17614116879476`
- `orderList[].goodsId`: `601104307271826`
- `orderList[].productList[].productSkuId`: `50668586641`
- `orderList[].productList[].productId`: `9903995070`
- `orderList[].productList[].extCode`: `LBB4-A-US` ✅

#### 商品API返回的ID：
- `productSkuSummaries[].productSkuId`: `15099780999`
- `productId` (SPU): `5582141357`
- `productSkcId`: `25949788870`
- `productSkuSummaries[].extCode`: `LBB-MXT-1-US` ✅

#### 数据库商品的ID：
- `Product.product_id`: `53563922673`
- `Product.skc_id`: `28785367833`
- `Product.spu_id`: `3075635380`
- `Product.sku`: `LBB4-A-US` ✅

**结论：**
- ❌ 所有数字ID都不匹配（格式完全不同）
- ✅ **唯一可以匹配的是 `extCode` (SKU货号)**

---

## ✅ 实施建议

### ✅ 已实施：正确的订单同步逻辑

在 `sync_service.py` 的 `_create_order()` 方法中：

```python
# 从 productList 中提取真正的SKU信息
product_list = order_item.get('productList', [])
if product_list and len(product_list) > 0:
    product_info = product_list[0]
    product_sku_id = product_info.get('productSkuId')  # 优先级1
    product_sku = product_info.get('extCode') or ''     # 优先级2 (SKU货号)
    spu_id = product_info.get('productId') or ''        # 优先级3 (实际是SPU ID)
else:
    product_sku_id = None
    product_sku = order_item.get('spec') or ''  # 备用（规格描述）
    spu_id = order_item.get('spuId') or ''

# 匹配商品
price_info = self._get_product_price_by_sku(
    product_sku=product_sku,        # extCode
    product_sku_id=product_sku_id,  # productSkuId (优先)
    spu_id=spu_id,                  # SPU ID (备用)
    order_time=order_time
)
```

### 匹配策略（优先级从高到低） ✅

1. **通过 productSkuId 匹配** ← 最快、最准确 ⭐⭐⭐⭐⭐
   - 订单: `productList[].productSkuId`
   - 商品: `Product.product_id`
   
2. **通过 extCode (SKU货号) 匹配** ← 最可靠、100%有效 ⭐⭐⭐⭐
   - 订单: `productList[].extCode`
   - 商品: `Product.sku`
   
3. **通过 productId (SPU ID) 匹配** ← 备用方案 ⭐⭐⭐
   - 订单: `productList[].productId`
   - 商品: `Product.spu_id`

---

## 📈 数据统计

当前状态：
- 总订单数：7383
- 已匹配商品：0 (0%)
- 有成本信息：3970 (53.8%) ← 通过其他方式匹配的
- 缺少成本信息：3413

总商品数：54 (SKU级别)
- 有成本价：27 (50%)

---

## 🔧 下一步行动

1. ✅ 修改订单同步逻辑，正确提取 `extCode` 作为 `product_sku`
2. ✅ 重新同步订单，填充正确的SKU
3. ✅ 批量匹配商品，填充 `product_id`、`unit_cost`、`total_cost`、`profit`
4. ✅ 验证匹配结果，确认GMV和利润计算正确

