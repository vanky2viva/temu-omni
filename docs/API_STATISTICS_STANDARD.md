# 数据统计接口统一标准

## 概述

本文档定义了系统中所有数据统计接口的统一标准，确保所有页面和AI模块使用一致的统计口径和过滤规则。

## 核心统计规则

### 1. 订单状态过滤

**统一规则：只统计有效订单状态**
- ✅ **包含状态**：
  - `PROCESSING` - 待发货
  - `SHIPPED` - 已发货
  - `DELIVERED` - 已签收
- ❌ **排除状态**：
  - `PAID` - 平台处理中（不计入销量统计）
  - `PENDING` - 待支付
  - `CANCELLED` - 已取消
  - `REFUNDED` - 已退款
  - `COMPLETED` - 已完成（如果存在，根据业务需求决定是否包含）

### 2. 订单数统计口径

**统一规则：按父订单去重统计**
- 如果 `parent_order_sn` 存在，使用 `parent_order_sn` 作为订单标识
- 如果 `parent_order_sn` 为 NULL，使用 `order_sn` 作为订单标识
- **不过滤订单金额**：统计所有有效状态的订单，无论 `total_price` 是否为 0

```sql
-- 父订单键定义
CASE 
    WHEN parent_order_sn IS NOT NULL THEN parent_order_sn 
    ELSE order_sn 
END
```

### 3. 销售件数统计口径

**统一规则：订单包含的商品数量总和**
- 销售件数 = `quantity` 字段的累加和
- 按统计维度（SKU、负责人、店铺等）分组后求和

### 4. GMV 和利润统计口径

**统一规则：按父订单聚合后统计**
1. 先按父订单分组，计算每个父订单的 GMV、成本、利润
2. 然后汇总所有父订单的统计数据
3. 价格字段已统一存储为 CNY，直接使用存储的值

**注意**：
- GMV = `total_price` 的累加和（可能包含 0 值）
- 成本 = `total_cost` 的累加和
- 利润 = `profit` 的累加和（或 GMV - 成本）

### 5. 时间范围处理

**统一规则：**
- 如果提供了 `start_date` 和 `end_date`，使用指定的时间范围
- 如果没有提供时间范围，默认统计所有时间的订单（不限制日期）
- 时间使用香港时区（UTC+8）

### 6. 商品关联规则

**统一规则：通过 `product_id` 关联**
- 订单通过 `Order.product_id` 关联 `Product.id`
- 获取商品信息（名称、负责人、SKU ID 等）
- 如果订单没有 `product_id`，无法关联到商品信息

### 7. SKU ID 识别规则

**统一规则：使用 `Product.product_id` 作为 SKU ID**
- `Product.product_id` = SKU ID（如 `77641044311`）
- `Product.sku` / `Order.product_sku` = SKU 货号（如 `LBB3-1-US`）

## API 接口规范

### 统一查询构建函数

所有统计接口应使用 `build_sales_filters()` 函数构建基础过滤条件：

```python
def build_sales_filters(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    shop_ids: Optional[List[int]] = None,
    manager: Optional[str] = None,
    region: Optional[str] = None,
    sku_search: Optional[str] = None,
) -> List:
    """
    构建销量统计的查询条件
    
    返回统一的过滤条件列表，包含：
    - 订单状态过滤（PROCESSING, SHIPPED, DELIVERED）
    - 时间范围过滤（如果提供）
    - 店铺过滤（如果提供）
    - 其他业务过滤条件
    """
```

### 统一父订单键定义

所有统计查询应使用统一的父订单键：

```python
parent_order_key = case(
    (Order.parent_order_sn.isnot(None), Order.parent_order_sn),
    else_=Order.order_sn
)
```

### 统一统计查询模式

**订单数统计：**
```python
func.count(func.distinct(parent_order_key)).label("order_count")
```

**销售件数统计：**
```python
func.sum(Order.quantity).label("total_quantity")
```

**GMV 和利润统计（按父订单聚合）：**
```python
# 先按父订单分组
parent_order_stats = db.query(
    parent_order_key.label('parent_key'),
    func.sum(Order.total_price).label('parent_gmv'),
    func.sum(Order.total_cost).label('parent_cost'),
    func.sum(Order.profit).label('parent_profit'),
).filter(and_(*filters)).group_by(parent_order_key).subquery()

# 然后汇总
total_stats = db.query(
    func.count(parent_order_stats.c.parent_key).label("total_orders"),
    func.sum(parent_order_stats.c.parent_gmv).label("total_gmv"),
    func.sum(parent_order_stats.c.parent_cost).label("total_cost"),
    func.sum(parent_order_stats.c.parent_profit).label("total_profit"),
).first()
```

## API 接口列表

### 1. 订单总览统计

**接口：** `GET /statistics/overview/`

**用途：** 仪表板总览、AI 模块数据获取

**统计指标：**
- `total_orders` - 总订单数（按父订单去重）
- `total_gmv` - 总GMV（CNY）
- `total_cost` - 总成本（CNY）
- `total_profit` - 总利润（CNY）
- `avg_order_value` - 平均订单价值
- `profit_margin` - 利润率（%）

**过滤规则：**
- 使用 `build_sales_filters()` 构建基础过滤
- 不过滤订单金额

### 2. 销量总览

**接口：** `GET /analytics/sales-overview`

**用途：** 销量统计页面、AI 模块数据获取

**统计指标：**
- `total_quantity` - 总销量（件数）
- `total_orders` - 总订单数（按父订单去重）
- `total_gmv` - 总GMV（CNY）
- `total_profit` - 总利润（CNY）
- `daily_trends` - 按天趋势数据
- `shop_trends` - 按店铺趋势数据

**过滤规则：**
- 使用 `build_sales_filters()` 构建基础过滤
- 不过滤订单金额

### 3. SKU 销量排行

**接口：** `GET /analytics/sku-sales-ranking`

**用途：** SKU 销量分析、AI 模块数据获取

**统计维度：** 按 SKU ID（`Product.product_id`）分组

**统计指标：**
- `sku` - SKU ID（`Product.product_id`）
- `product_name` - 商品名称
- `manager` - 负责人
- `total_quantity` - 销售件数
- `order_count` - 订单数（按父订单去重）
- `total_gmv` - GMV
- `total_profit` - 利润

**过滤规则：**
- 使用 `build_sales_filters()` 构建基础过滤
- 通过 `product_id` 关联 Product 表获取 SKU ID

### 4. 负责人业绩统计

**接口：** `GET /analytics/manager-sales`

**用途：** 负责人业绩分析、AI 模块数据获取

**统计维度：** 按负责人分组

**统计指标：**
- `manager` - 负责人
- `total_quantity` - 销售件数
- `order_count` - 订单数（按父订单去重）
- `total_gmv` - GMV
- `total_profit` - 利润
- `daily_trends` - 按天趋势数据

**过滤规则：**
- 使用 `build_sales_filters()` 构建基础过滤
- 通过 `product_id` 关联 Product 表获取负责人
- 不过滤订单金额

### 5. GMV 表格

**接口：** `GET /analytics/gmv-table`

**用途：** GMV 趋势分析

**统计维度：** 按时间周期（日/周/月）和店铺分组

**过滤规则：**
- 使用 `build_sales_filters()` 构建基础过滤

## AI 模块数据访问

### 专用数据访问接口（推荐）

AI 模块应优先使用专门设计的统一数据访问接口（`/api/ai-data/*`），这些接口遵循统一的统计规则，确保数据一致性：

#### 统计类接口

1. **销量总览：** `GET /api/ai-data/sales-overview`
   - 返回订单数、销售件数、GMV、成本、利润等核心指标
   - 支持时间范围、店铺、负责人、地区筛选
   
2. **SKU 统计：** `GET /api/ai-data/sku-statistics`
   - 返回按 SKU ID 分组的统计数据
   - 支持时间范围、店铺、负责人、地区筛选
   
3. **负责人统计：** `GET /api/ai-data/manager-statistics`
   - 返回按负责人分组的统计数据
   - 支持时间范围、店铺、地区筛选
   
4. **数据摘要：** `GET /api/ai-data/data-summary`
   - 返回全面的数据摘要，包括总览、top SKU、top 负责人
   - 适合快速获取整体数据概览

#### 详细数据接口（新增）

5. **回款统计数据：** `GET /api/ai-data/collection-statistics`
   - 返回回款统计数据（汇总数据，按日期和店铺分组）
   - 回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
   - 返回字段包括：
     - `summary`: 汇总信息（总回款金额、总订单数、店铺列表）
     - `table_data`: 表格数据（按日期和店铺分组的回款金额）
     - `chart_data`: 图表数据（日期列表和每个店铺的折线图数据）
     - `period`: 时间范围信息
   - 支持时间范围（回款日期范围）、店铺筛选
   - 与财务管理页面使用的数据格式一致
   - **这是AI模块获取回款金额的主要接口**
   
6. **回款详细数据：** `GET /api/ai-data/collection-details`
   - 返回回款金额的最小粒度数据（按订单级别）
   - 回款逻辑：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
   - 返回字段包括：订单号、父订单号、店铺名称、商品信息、数量、订单金额、签收时间、回款日期、回款金额等
   - 支持时间范围（回款日期范围）、店铺、订单号筛选
   - 适合查询具体订单的回款情况
   
7. **订单详细数据：** `GET /api/ai-data/order-details`
   - 返回订单的完整详细信息
   - 包含所有订单字段：订单号、商品信息、价格、成本、利润、状态、时间信息、客户信息、物流信息等
   - 支持时间范围（订单时间）、店铺、状态、订单号、SKU、商品名称筛选
   - 支持分页（skip/limit）
   - 适合查询具体订单的详细信息
   
8. **商品成本详细数据：** `GET /api/ai-data/product-cost-details`
   - 返回商品的成本信息，包括当前成本和历史成本记录
   - 返回字段包括：商品ID、商品名称、SKU、Temu商品ID、当前成本、成本货币、生效时间、历史成本记录等
   - 支持按商品ID、Temu商品ID、SKU、商品名称筛选
   - 可选择是否包含历史成本记录
   - 适合查询商品成本变化历史

### 通用数据访问接口（备选）

如果专用接口无法满足需求，可以使用以下通用接口：

1. **订单总览：** `GET /api/statistics/overview/`
2. **销量总览：** `GET /api/analytics/sales-overview`
3. **SKU 排行：** `GET /api/analytics/sku-sales-ranking`
4. **负责人业绩：** `GET /api/analytics/manager-sales`
5. **订单列表：** `GET /api/orders/`（支持详细筛选）

### 数据格式规范

所有统计接口返回的数据格式应统一：

```json
{
  "total_orders": 6534,
  "total_quantity": 7317,
  "total_gmv": 1556661.58,
  "total_cost": 1362237.66,
  "total_profit": 194423.92,
  "profit_margin": 12.49,
  "period": {
    "start_date": "2024-10-24T00:00:00+08:00",
    "end_date": "2024-11-23T23:59:59+08:00",
    "days": 30
  }
}
```

### 时间范围参数

**统一格式：**
- `start_date`: `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- `end_date`: `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- `days`: 整数，表示最近 N 天

**默认行为：**
- 如果不提供日期参数，统计所有时间的订单
- 如果只提供 `days` 参数，统计最近 N 天

## 实施检查清单

- [ ] 所有统计接口使用 `build_sales_filters()` 构建过滤条件
- [ ] 所有订单数统计使用父订单去重
- [ ] 所有接口不过滤订单金额（`total_price > 0`）
- [ ] SKU ID 使用 `Product.product_id`，不是 `Product.sku`
- [ ] 负责人关联通过 `product_id`，不是 `product_name`
- [ ] 价格字段直接使用存储的 CNY 值，不进行货币转换
- [ ] 时间范围处理统一使用香港时区
- [ ] 所有接口返回格式统一

## 注意事项

1. **数据一致性**：确保所有接口使用相同的统计规则，避免不同页面显示不同的数据
2. **性能优化**：对于大数据量统计，考虑使用缓存或异步计算
3. **数据准确性**：定期验证统计结果，确保与订单列表数据一致
4. **AI 模块支持**：确保 AI 模块能访问到所有必要的统计数据和原始数据

