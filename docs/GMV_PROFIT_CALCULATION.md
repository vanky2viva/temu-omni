# GMV和利润计算逻辑说明

## 一、核心概念

### 1. GMV（Gross Merchandise Volume，商品交易总额）
- **定义**：GMV = 供货价 × 数量
- **说明**：供货价就是实际的收入，即平台给卖家的价格
- **字段**：订单表中的 `total_price` 字段存储的就是GMV

### 2. 利润（Profit）
- **定义**：利润 = GMV - 总成本
- **公式**：`profit = total_price - total_cost`
- **说明**：每个子订单的利润 = 该子订单的GMV - 该子订单的总成本

## 二、计算流程

### 1. 订单同步时的计算（子订单级别）

**文件**: `backend/app/services/sync_service.py`

**计算时机**：订单同步时，匹配到商品后立即计算并存储

```python
# 1. 匹配商品，获取供货价和成本价
price_info = self._get_product_price_by_sku(
    product_sku=product_sku,
    order_time=order_time,
    product_sku_id=product_sku_id,
    spu_id=spu_id
)

# 2. 计算GMV（收入）并存储
supply_price = price_info.get('supply_price')  # 供货价（来自商品表的current_price）
unit_price = supply_price  # 单价 = 供货价
total_price = unit_price * quantity  # GMV = 供货价 × 数量

# 3. 计算成本并存储
unit_cost = price_info['cost_price']  # 单位成本（来自商品成本表，根据订单时间查找当时有效的成本价）
total_cost = unit_cost * quantity  # 总成本 = 单位成本 × 数量

# 4. 计算利润并存储
profit = total_price - total_cost  # 利润 = GMV - 总成本

# 5. 存储到订单表
order = Order(
    ...
    unit_price=unit_price,
    total_price=total_price,  # GMV
    unit_cost=unit_cost,
    total_cost=total_cost,
    profit=profit,
    ...
)
```

**关键点**：
- 每个子订单（SKU级别）都有独立的GMV、成本和利润
- 供货价来自商品表的 `current_price` 字段
- 成本价来自商品成本表（`product_costs`），根据订单时间查找当时有效的成本价
- **所有计算值都存储在订单表中，后续统计直接读取**

### 2. 订单级别的汇总

**父订单的GMV、成本、利润**：
- 父订单的GMV = 该父订单下所有子订单的GMV之和
- 父订单的总成本 = 该父订单下所有子订单的总成本之和
- 父订单的利润 = 该父订单下所有子订单的利润之和

**计算方式**（统计时）：
```sql
-- 按父订单分组汇总
SELECT 
    COALESCE(parent_order_sn, order_sn) AS parent_key,
    SUM(total_price) AS parent_gmv,      -- 父订单GMV（从存储值汇总）
    SUM(total_cost) AS parent_cost,      -- 父订单总成本（从存储值汇总）
    SUM(profit) AS parent_profit         -- 父订单利润（从存储值汇总）
FROM orders
WHERE status IN ('PROCESSING', 'SHIPPED', 'DELIVERED')
GROUP BY COALESCE(parent_order_sn, order_sn)
```

### 3. 统计级别的汇总

**总GMV、总成本、总利润**：
- 总GMV = 所有有效订单的GMV之和（按父订单聚合后）
- 总成本 = 所有有效订单的总成本之和（按父订单聚合后）
- 总利润 = 所有有效订单的利润之和（按父订单聚合后）

**计算方式**（`backend/app/api/analytics.py`）：
```python
# 先按父订单分组，汇总每个父订单的GMV、成本、利润（从存储值读取）
parent_order_stats = db.query(
    parent_order_key.label('parent_key'),
    func.sum(_convert_to_cny(Order.total_price, usd_rate)).label('parent_gmv'),
    func.sum(_convert_to_cny(Order.total_cost, usd_rate)).label('parent_cost'),
    func.sum(_convert_to_cny(Order.profit, usd_rate)).label('parent_profit'),
).filter(and_(*filters)).group_by(parent_order_key).subquery()

# 然后汇总所有父订单
total_stats = db.query(
    func.sum(parent_order_stats.c.parent_gmv).label("total_gmv"),
    func.sum(parent_order_stats.c.parent_cost).label("total_cost"),
    func.sum(parent_order_stats.c.parent_profit).label("total_profit"),
).first()
```

## 三、字段命名规范

### 数据库字段

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `unit_price` | Numeric | 单价（供货价） | 来自商品表的current_price |
| `total_price` | Numeric | GMV（订单总价） | = unit_price × quantity，订单同步时计算并存储 |
| `unit_cost` | Numeric | 单位成本 | 来自商品成本表，订单同步时查找并存储 |
| `total_cost` | Numeric | 总成本 | = unit_cost × quantity，订单同步时计算并存储 |
| `profit` | Numeric | 利润 | = total_price - total_cost，订单同步时计算并存储 |

### API返回字段

| 字段名 | 说明 | 计算方式 |
|--------|------|----------|
| `total_gmv` | 总GMV | 所有有效订单的GMV之和（按父订单聚合，从存储值读取） |
| `total_cost` | 总成本 | 所有有效订单的总成本之和（按父订单聚合，从存储值读取） |
| `total_profit` | 总利润 | 所有有效订单的利润之和（按父订单聚合，从存储值读取） |
| `profit_margin` | 利润率 | = (total_profit / total_gmv) × 100% |

## 四、统计口径

### 订单数统计
- **口径**：一个不重复的父订单号记为一单
- **计算**：`COUNT(DISTINCT COALESCE(parent_order_sn, order_sn))`
- **说明**：如果 `parent_order_sn` 存在，使用 `parent_order_sn`；否则使用 `order_sn`

### 订单状态筛选
- **有效订单**：只统计 `PROCESSING`（待发货）、`SHIPPED`（已发货）、`DELIVERED`（已签收）
- **排除订单**：`PENDING`（待支付）、`PAID`（平台处理中）、`CANCELLED`（已取消）、`REFUNDED`（已退款）

### 货币转换
- **USD订单**：GMV、成本、利润都乘以汇率（默认7.1）转换为CNY
- **CNY订单**：保持不变
- **统一单位**：所有统计结果统一为CNY

## 五、数据一致性保证

### 1. 订单同步时
- 必须匹配到商品才能计算GMV和利润
- 如果未匹配到商品，`total_price` 设为0，`profit` 为NULL
- 如果匹配到商品但无成本价，`total_price` 有值，但 `profit` 为NULL
- **所有计算值都存储在订单表中，后续统计直接读取，不进行实时计算**

### 2. 统计时
- 只统计 `total_price > 0` 的订单（确保匹配到商品）
- 利润为NULL的订单不参与利润统计（但GMV会被计入）
- 按父订单聚合，确保同一父订单下的多个子订单不会重复计算
- **直接从订单表读取存储的GMV、成本、利润值进行汇总**

### 3. 数据修正
- 如果商品成本价设置错误，需要：
  1. 修正商品成本价
  2. 重新同步相关订单（或手动更新订单的成本和利润）
  3. 统计结果会自动反映更新后的数据

## 六、优势

### 1. 性能优势
- **查询速度快**：统计时直接读取存储值，不需要JOIN商品表和成本表
- **无需实时计算**：避免了复杂的子查询和关联查询

### 2. 数据稳定性
- **历史数据稳定**：订单同步时计算的值不会因为商品价格变化而改变
- **数据一致性**：所有统计都基于同一份存储的数据

### 3. 实现简单
- **逻辑清晰**：计算和存储分离，职责明确
- **易于维护**：不需要复杂的实时计算逻辑

## 七、示例

### 示例1：订单同步时计算
- 商品SKU: `ABC-123`
- 供货价: 100 CNY
- 单位成本: 60 CNY（订单时间有效的成本价）
- 数量: 2

**计算并存储**：
- GMV (`total_price`) = 100 × 2 = 200 CNY
- 总成本 (`total_cost`) = 60 × 2 = 120 CNY
- 利润 (`profit`) = 200 - 120 = 80 CNY

### 示例2：统计时汇总
假设有3个父订单：
- 父订单1: GMV=350, 成本=210, 利润=140（从存储值读取）
- 父订单2: GMV=200, 成本=120, 利润=80（从存储值读取）
- 父订单3: GMV=150, 成本=100, 利润=50（从存储值读取）

**总统计**：
- 总GMV = 350 + 200 + 150 = 700 CNY
- 总成本 = 210 + 120 + 100 = 430 CNY
- 总利润 = 140 + 80 + 50 = 270 CNY
- 利润率 = (270 / 700) × 100% = 38.57%

## 八、注意事项

1. **供货价就是实际收入**：不需要从API获取实际销售价格，供货价就是卖家实际收到的金额
2. **成本价时效性**：成本价根据订单时间查找当时有效的成本记录，支持历史成本追溯
3. **父订单聚合**：统计时必须按父订单聚合，避免重复计算
4. **货币统一**：所有统计结果统一转换为CNY，便于比较和分析
5. **数据完整性**：未匹配到商品的订单不会计入GMV和利润统计
6. **存储优先**：所有计算值在订单同步时计算并存储，统计时直接读取，不进行实时计算
