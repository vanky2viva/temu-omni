# 订单字段说明 - SKU相关字段

## 订单表（Order）的所有字段

### 基本信息字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | Integer | 主键，自增 |
| `shop_id` | Integer | 店铺ID（外键关联shops表） |

### 订单信息字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `order_sn` | String(100) | 订单编号 |
| `temu_order_id` | String(100) | Temu订单ID |
| `parent_order_sn` | String(100) | 父订单编号（用于关联同一父订单下的多个子订单） |

### **商品信息字段（重点）**
| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `product_id` | Integer | **商品ID（外键关联products表）** | 通过这个字段可以关联到Product表 |
| `product_name` | String(500) | 商品名称 | 冗余字段，从商品表冗余过来 |
| `product_sku` | String(200) | **商品SKU** | **这是SKU货号（从Temu API获取的sku字段）** |
| `spu_id` | String(100) | SPU ID | 一个SPU对应多个SKU |
| `quantity` | Integer | 购买数量（应履约件数） |

### 价格信息字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `unit_price` | Numeric(10,2) | 单价（供货价，CNY） |
| `total_price` | Numeric(10,2) | GMV（订单总价，供货价×数量，CNY） |
| `currency` | String(10) | 原始货币（USD/CNY等，仅用于记录，价格已统一为CNY） |

### 成本和利润字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `unit_cost` | Numeric(10,2) | 单位成本（CNY） |
| `total_cost` | Numeric(10,2) | 总成本（单位成本×数量，CNY） |
| `profit` | Numeric(10,2) | 利润（GMV-总成本，CNY） |

### 订单状态字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `status` | Enum | 订单状态（PENDING/PAID/PROCESSING/SHIPPED/DELIVERED/COMPLETED/CANCELLED/REFUNDED） |

### 时间信息字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `order_time` | DateTime | 下单时间 |
| `payment_time` | DateTime | 支付时间 |
| `shipping_time` | DateTime | 发货时间 |
| `expect_ship_latest_time` | DateTime | 预期最晚发货时间 |
| `delivery_time` | DateTime | 送达时间 |

### 客户信息字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `customer_id` | String(100) | 客户ID |
| `shipping_country` | String(50) | 收货国家 |
| `shipping_city` | String(100) | 收货城市 |
| `shipping_province` | String(50) | 收货省份/州 |
| `shipping_postal_code` | String(20) | 收货邮编 |

### 其他字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `notes` | Text | 备注 |
| `raw_data` | Text | 原始数据JSON |
| `raw_data_id` | Integer | 关联原始数据表ID |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

---

## 商品表（Product）的SKU相关字段

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `id` | Integer | 主键 | **这个id对应Order表的product_id** |
| `product_id` | String(100) | Temu商品ID | |
| `sku` | String(200) | **商品SKU** | **这是SKU ID（商品的唯一标识符）** |
| `product_name` | String(500) | 商品名称 | |
| `manager` | String(100) | 负责人 | |

---

## 关键区别说明

### Order.product_sku vs Product.sku

1. **`Order.product_sku`**：
   - 存储在订单表中
   - 直接从Temu API获取的sku字段值
   - **这是SKU货号（可能在不同订单中重复，因为同一商品可以有多个订单）**
   - 示例：`LBB3-1-US`、`LBB4-A-US`

2. **`Product.sku`**：
   - 存储在商品表中
   - 通过`Order.product_id`关联到`Product.id`可以获取
   - **这是SKU ID（商品的唯一标识符，同一商品对应一个SKU ID）**
   - 示例：可能是相同的SKU ID，或者是商品表中的标准SKU标识符

### 关联关系

```
Order表                    Product表
--------                   ---------
product_id  ----->------>  id
product_sku  (SKU货号)      sku  (SKU ID)
```

**结论**：
- 如果要显示 **SKU ID**（商品的唯一标识符），应该使用 **`Product.sku`**（通过`Order.product_id`关联获取）
- 如果显示的是 **SKU货号**（订单中直接存储的值），则是 **`Order.product_sku`**

---

## 确认方法

要确认哪个字段是SKU ID，可以：
1. 查看数据库中的示例数据
2. 对比`Order.product_sku`和`Product.sku`的值
3. 确认哪个是唯一的商品标识符，哪个是订单中的SKU货号

