# ForgGPT 数据源和接口文档

## 一、概述

本文档详细说明目前提供给 ForgGPT AI 的数据源、接口和查询能力。

## 二、数据源分类

### 2.1 系统提示词中的数据（每次对话都提供）

**位置**: `backend/app/services/forggpt_service.py` → `_get_system_prompt()`

#### 数据概览（实时查询）
```python
# 基础统计
- 店铺数量：shop_count (Shop.count())
- 订单总数：order_count (Order.count())
- 商品总数：product_count (Product.count())

# 最近7天数据
- 最近7天GMV：recent_gmv (最近7天订单的total_price总和)
- 最近7天订单量：recent_order_count (最近7天的订单数量)
```

**查询方式**:
```python
# 店铺数量
shop_count = self.db.query(Shop).count()

# 订单总数
order_count = self.db.query(Order).count()

# 商品总数
product_count = self.db.query(Product).count()

# 最近7天数据
seven_days_ago = datetime.now() - timedelta(days=7)
recent_orders = self.db.query(Order).filter(
    Order.order_time >= seven_days_ago
).all()
recent_gmv = sum([float(order.total_price or 0) for order in recent_orders])
recent_order_count = len(recent_orders)
```

### 2.2 数据上下文中的数据（根据用户问题动态注入）

**位置**: `backend/app/services/forggpt_service.py` → `_get_data_context()`

#### 2.2.1 订单相关数据

**触发关键词**: `订单`、`order`、`gmv`、`销售`、`sales`

**数据来源**: `StatisticsService.get_order_statistics()`

**提供的数据**:
```python
订单数据（最近30天）：
- 总订单数：total_orders
- 总GMV：total_gmv (CNY)
- 总利润：total_profit (CNY)
- 平均订单金额：avg_order_amount (CNY)
- 退款订单数：refunded_orders
- 退款率：refund_rate (%)
```

**查询参数**:
- `start_date`: 最近30天
- `shop_ids`: None (所有店铺)
- `status`: None (排除已取消和已退款订单)

**StatisticsService 提供的完整统计**:
```python
{
    'total_orders': int,           # 总订单数（按订单号去重）
    'total_gmv': float,            # 总GMV（CNY）
    'total_cost': float,           # 总成本（CNY）
    'total_profit': float,         # 总利润（CNY）
    'avg_order_amount': float,     # 平均订单金额（CNY）
    'profit_margin': float,        # 利润率（%）
    'refunded_orders': int,        # 退款订单数
    'refund_rate': float,          # 退款率（%）
    'cancelled_orders': int,       # 取消订单数
    'cancelled_rate': float,       # 取消率（%）
}
```

#### 2.2.2 商品相关数据

**触发关键词**: `商品`、`product`、`sku`、`销量`、`库存`

**数据来源**: 直接查询 `Product` 和 `Order` 表

**提供的数据**:
```python
商品数据：
- 商品总数：total_products
- 在售商品数：active_products
- 销量前10商品：
  - {product_name} ({sku}): {total_sales}件
```

**查询方式**:
```python
# 商品统计
total_products = self.db.query(Product).count()
active_products = self.db.query(Product).filter(Product.is_active == True).count()

# 销量前10商品
top_products = self.db.query(
    Product.id,
    Product.product_name,
    Product.sku,
    func.sum(Order.quantity).label('total_sales')
).join(
    Order, Product.id == Order.product_id
).filter(
    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED])
).group_by(
    Product.id, Product.product_name, Product.sku
).order_by(
    func.sum(Order.quantity).desc()
).limit(10).all()
```

#### 2.2.3 店铺相关数据

**触发关键词**: `店铺`、`shop`、`store`

**数据来源**: 直接查询 `Shop` 表

**提供的数据**:
```python
店铺数据：
- 店铺总数：shop_count
- 店铺列表：
  - {shop_name} (ID: {shop_id}, 环境: {environment})
```

**查询方式**:
```python
shops = self.db.query(Shop).all()
# 最多显示10个店铺
for shop in shops[:10]:
    # shop.shop_name, shop.id, shop.environment.value
```

## 三、可用的数据模型和字段

### 3.1 Shop（店铺）模型

**表名**: `shops`

**主要字段**:
- `id`: 店铺ID
- `shop_name`: 店铺名称
- `environment`: 环境（US/CN）
- `region`: 区域
- `is_active`: 是否激活
- `default_manager`: 默认负责人
- `created_at`: 创建时间
- `updated_at`: 更新时间

**可查询数据**:
- 所有店铺列表
- 店铺基本信息
- 店铺状态

### 3.2 Order（订单）模型

**表名**: `orders`

**主要字段**:
- `id`: 订单ID
- `shop_id`: 店铺ID
- `order_sn`: 订单号
- `temu_order_id`: Temu订单ID
- `parent_order_sn`: 父订单号
- `product_id`: 商品ID
- `product_name`: 商品名称
- `product_sku`: SKU货号
- `quantity`: 数量
- `unit_price`: 单价
- `total_price`: 总价
- `currency`: 货币
- `unit_cost`: 单位成本
- `total_cost`: 总成本
- `profit`: 利润
- `status`: 订单状态
- `order_time`: 下单时间
- `payment_time`: 支付时间
- `shipping_time`: 发货时间
- `delivery_time`: 签收时间
- `customer_id`: 客户ID
- `shipping_country`: 收货国家
- `shipping_city`: 收货城市
- `raw_data_id`: 原始数据ID

**订单状态枚举**:
- `PENDING`: 待处理
- `PAID`: 已支付
- `SHIPPED`: 已发货
- `DELIVERED`: 已送达
- `RECEIPTED`: 已签收
- `CANCELLED`: 已取消
- `REFUNDED`: 已退款

**可查询数据**:
- 订单列表（支持筛选）
- 订单统计（GMV、利润、订单量等）
- 订单趋势（按时间维度）
- 订单状态分布

### 3.3 Product（商品）模型

**表名**: `products`

**主要字段**:
- `id`: 商品ID
- `shop_id`: 店铺ID
- `product_id`: Temu商品ID
- `product_name`: 商品名称
- `sku`: SKU货号
- `spu_id`: SPU ID
- `category`: 类目
- `current_price`: 当前价格（供货价）
- `currency`: 货币
- `is_active`: 是否在售
- `listed_at`: 上架时间
- `total_sales`: 累计销量
- `manager`: 负责人
- `raw_data_id`: 原始数据ID

**可查询数据**:
- 商品列表
- 商品销量统计
- 商品价格信息
- 商品状态

### 3.4 ProductCost（商品成本）模型

**表名**: `product_costs`

**主要字段**:
- `id`: 成本记录ID
- `product_id`: 商品ID
- `cost_price`: 成本价
- `currency`: 货币
- `effective_from`: 生效开始时间
- `effective_to`: 生效结束时间
- `notes`: 备注

**可查询数据**:
- 商品成本历史
- 当前有效成本价

## 四、可用的服务接口

### 4.1 StatisticsService（统计服务）

**位置**: `backend/app/services/statistics.py`

#### 4.1.1 get_order_statistics()

**功能**: 获取订单统计数据

**参数**:
- `db`: 数据库会话
- `shop_ids`: 店铺ID列表（可选）
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `status`: 订单状态（可选）

**返回数据**:
```python
{
    'total_orders': int,           # 总订单数
    'total_gmv': float,            # 总GMV（CNY）
    'total_cost': float,           # 总成本（CNY）
    'total_profit': float,         # 总利润（CNY）
    'avg_order_amount': float,     # 平均订单金额（CNY）
    'profit_margin': float,        # 利润率（%）
    'refunded_orders': int,        # 退款订单数
    'refund_rate': float,          # 退款率（%）
    'cancelled_orders': int,       # 取消订单数
    'cancelled_rate': float,       # 取消率（%）
}
```

#### 4.1.2 get_order_statistics_cached()

**功能**: 获取订单统计数据（带Redis缓存）

**参数**: 同 `get_order_statistics()`
- `cache_ttl`: 缓存过期时间（秒，默认300秒）

**返回数据**: 同 `get_order_statistics()`

### 4.2 数据库直接查询

**位置**: `backend/app/services/forggpt_service.py`

#### 可用的查询方式

1. **基础查询**
   ```python
   # 计数
   count = self.db.query(Model).count()
   
   # 筛选
   items = self.db.query(Model).filter(Model.field == value).all()
   
   # 排序
   items = self.db.query(Model).order_by(Model.field.desc()).all()
   
   # 限制数量
   items = self.db.query(Model).limit(10).all()
   ```

2. **关联查询**
   ```python
   # JOIN查询
   results = self.db.query(Product, Order).join(
       Order, Product.id == Order.product_id
   ).all()
   ```

3. **聚合查询**
   ```python
   # 求和
   total = self.db.query(func.sum(Order.quantity)).scalar()
   
   # 分组统计
   stats = self.db.query(
       Product.id,
       func.sum(Order.quantity).label('total_sales')
   ).join(
       Order, Product.id == Order.product_id
   ).group_by(Product.id).all()
   ```

## 五、当前限制和待扩展

### 5.1 当前限制

1. **数据上下文注入**
   - 仅根据关键词简单匹配
   - 固定时间范围（订单30天，概览7天）
   - 不支持用户指定的时间范围
   - 不支持用户指定的店铺筛选

2. **数据查询能力**
   - 仅提供基础统计，不支持详细查询
   - 不支持复杂的数据分析（如趋势分析、对比分析）
   - 不支持实时数据查询（AI无法主动查询数据库）

3. **文件处理**
   - 文件上传接口已创建，但功能未实现
   - 不支持Excel/CSV/JSON文件解析
   - 不支持在线表格URL处理

### 5.2 待扩展功能

1. **增强数据上下文**
   - 支持用户指定的时间范围
   - 支持用户指定的店铺筛选
   - 支持更智能的关键词匹配（NLP）
   - 支持多维度数据注入（时间趋势、对比数据等）

2. **扩展数据查询能力**
   - 实现AI主动查询数据库的接口
   - 支持复杂的数据分析查询
   - 支持数据可视化数据生成

3. **文件处理能力**
   - 实现Excel/CSV/JSON文件解析
   - 实现在线表格URL处理
   - 实现文件数据分析

4. **其他数据源**
   - 原始数据表（temu_orders_raw, temu_products_raw）
   - 报表快照（report_snapshots）
   - 回款计划（payouts）
   - 活动数据（activities）

## 六、使用示例

### 6.1 系统提示词数据示例

```
当前应用数据概览：
- 店铺数量：5
- 订单总数：1000
- 商品总数：200
- 最近7天GMV：50000.00
- 最近7天订单量：250
```

### 6.2 订单数据上下文示例

```
订单数据（最近30天）：
- 总订单数：500
- 总GMV：100000.00
- 总利润：20000.00
- 平均订单金额：200.00
- 退款订单数：10
- 退款率：2.00%
```

### 6.3 商品数据上下文示例

```
商品数据：
- 商品总数：200
- 在售商品数：150
- 销量前10商品：
  - LABUBU 3.0 (LBB3-1-US): 150件
  - LABUBU 2.0 (LBB2-1-US): 120件
  - LABUBU 4.0 (LBB4-1-US): 100件
  ...
```

### 6.4 店铺数据上下文示例

```
店铺数据：
- 店铺总数：5
- 店铺列表：
  - Shop US 1 (ID: 1, 环境: US)
  - Shop US 2 (ID: 2, 环境: US)
  - Shop CN 1 (ID: 3, 环境: CN)
  ...
```

## 七、总结

### 当前提供的数据源

1. **系统提示词**（每次对话）
   - 店铺数量
   - 订单总数
   - 商品总数
   - 最近7天GMV和订单量

2. **数据上下文**（根据关键词动态注入）
   - 订单统计（最近30天）
   - 商品统计和销量排行
   - 店铺列表

3. **可用的数据模型**
   - Shop（店铺）
   - Order（订单）
   - Product（商品）
   - ProductCost（商品成本）

4. **可用的服务接口**
   - StatisticsService.get_order_statistics()
   - StatisticsService.get_order_statistics_cached()
   - 数据库直接查询（通过SQLAlchemy ORM）

### 数据访问方式

- **直接数据库查询**: 通过SQLAlchemy ORM
- **统计服务**: 通过StatisticsService
- **缓存**: 通过RedisClient（统计数据缓存）

### 数据特点

- **实时性**: 每次对话都查询最新数据
- **智能注入**: 根据用户问题关键词自动注入相关数据
- **数据准确性**: 直接从数据库查询，保证数据准确性
- **性能优化**: 统计数据支持Redis缓存


