# 数据库设计文档

## 概述

本系统使用PostgreSQL数据库，通过SQLAlchemy ORM进行数据访问。

## 表结构

### shops（店铺表）

存储Temu店铺的基本信息和授权凭证。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| shop_id | VARCHAR(100) | Temu店铺ID，唯一 |
| shop_name | VARCHAR(200) | 店铺名称 |
| region | VARCHAR(50) | 店铺地区 |
| entity | VARCHAR(200) | 经营主体 |
| access_token | TEXT | 访问令牌 |
| refresh_token | TEXT | 刷新令牌 |
| token_expires_at | DATETIME | 令牌过期时间 |
| is_active | BOOLEAN | 是否启用 |
| last_sync_at | DATETIME | 最后同步时间 |
| description | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引**：
- `shop_id` (UNIQUE)
- `is_active`

### orders（订单表）

存储订单信息，包含价格、成本、利润等财务数据。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| shop_id | INTEGER | 外键，关联shops表 |
| order_sn | VARCHAR(100) | 订单编号，唯一 |
| temu_order_id | VARCHAR(100) | Temu订单ID，唯一 |
| product_id | INTEGER | 外键，关联products表 |
| product_name | VARCHAR(500) | 商品名称 |
| product_sku | VARCHAR(200) | 商品SKU |
| quantity | INTEGER | 购买数量 |
| unit_price | NUMERIC(10,2) | 单价 |
| total_price | NUMERIC(10,2) | 订单总价 |
| currency | VARCHAR(10) | 货币类型 |
| unit_cost | NUMERIC(10,2) | 单位成本 |
| total_cost | NUMERIC(10,2) | 总成本 |
| profit | NUMERIC(10,2) | 利润 |
| status | ENUM | 订单状态 |
| order_time | DATETIME | 下单时间 |
| payment_time | DATETIME | 支付时间 |
| shipping_time | DATETIME | 发货时间 |
| delivery_time | DATETIME | 送达时间 |
| customer_id | VARCHAR(100) | 客户ID |
| shipping_country | VARCHAR(50) | 收货国家 |
| notes | TEXT | 备注 |
| raw_data | TEXT | 原始数据JSON |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**订单状态枚举**：
- `pending`: 待支付
- `paid`: 已支付
- `shipped`: 已发货
- `delivered`: 已送达
- `completed`: 已完成
- `cancelled`: 已取消
- `refunded`: 已退款

**索引**：
- `order_sn` (UNIQUE)
- `temu_order_id` (UNIQUE)
- `shop_id`
- `product_id`
- `status`
- `order_time`

### products（商品表）

存储商品基本信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| shop_id | INTEGER | 外键，关联shops表 |
| product_id | VARCHAR(100) | Temu商品ID |
| product_name | VARCHAR(500) | 商品名称 |
| sku | VARCHAR(200) | 商品SKU |
| current_price | NUMERIC(10,2) | 当前售价 |
| currency | VARCHAR(10) | 货币类型 |
| stock_quantity | INTEGER | 库存数量 |
| is_active | BOOLEAN | 是否在售 |
| description | TEXT | 商品描述 |
| image_url | VARCHAR(500) | 商品图片URL |
| category | VARCHAR(200) | 商品分类 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引**：
- `shop_id`
- `product_id`
- `sku`

### product_costs（商品成本表）

存储商品成本历史记录，支持成本变更追踪。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| product_id | INTEGER | 外键，关联products表 |
| cost_price | NUMERIC(10,2) | 成本价 |
| currency | VARCHAR(10) | 货币类型 |
| effective_from | DATETIME | 生效开始时间 |
| effective_to | DATETIME | 生效结束时间 |
| notes | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |

**索引**：
- `product_id`
- `effective_from`

**逻辑**：
- 当前成本：`effective_to` 为 NULL 的记录
- 历史成本：`effective_to` 不为 NULL 的记录
- 添加新成本时，自动更新旧成本的 `effective_to`

### activities（活动表）

存储营销活动信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| shop_id | INTEGER | 外键，关联shops表 |
| activity_id | VARCHAR(100) | Temu活动ID |
| activity_name | VARCHAR(200) | 活动名称 |
| activity_type | ENUM | 活动类型 |
| start_time | DATETIME | 开始时间 |
| end_time | DATETIME | 结束时间 |
| is_active | BOOLEAN | 是否启用 |
| description | TEXT | 活动描述 |
| notes | TEXT | 备注 |
| raw_data | TEXT | 原始数据JSON |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**活动类型枚举**：
- `discount`: 折扣活动
- `flash_sale`: 限时抢购
- `coupon`: 优惠券
- `promotion`: 促销活动
- `other`: 其他

**索引**：
- `shop_id`
- `activity_id`
- `start_time`
- `end_time`

## 关系图

```
shops (1) ----< (*) orders
shops (1) ----< (*) products
shops (1) ----< (*) activities
products (1) ----< (*) product_costs
products (1) ----< (*) orders
```

## 查询优化建议

### 1. 订单统计查询

使用索引优化时间范围查询：

```sql
SELECT 
    DATE(order_time) as date,
    COUNT(*) as orders,
    SUM(total_price) as gmv,
    SUM(profit) as profit
FROM orders
WHERE shop_id = 1
  AND order_time >= '2024-01-01'
  AND order_time < '2024-02-01'
GROUP BY DATE(order_time);
```

### 2. 店铺对比查询

使用JOIN优化：

```sql
SELECT 
    s.shop_name,
    COUNT(o.id) as orders,
    SUM(o.total_price) as gmv,
    SUM(o.profit) as profit
FROM shops s
LEFT JOIN orders o ON s.id = o.shop_id
WHERE o.order_time >= '2024-01-01'
GROUP BY s.id, s.shop_name;
```

### 3. 成本查询

查找特定时间的商品成本：

```sql
SELECT cost_price
FROM product_costs
WHERE product_id = 1
  AND effective_from <= '2024-01-15'
  AND (effective_to IS NULL OR effective_to > '2024-01-15')
ORDER BY effective_from DESC
LIMIT 1;
```

## 数据迁移

使用Alembic进行数据库迁移：

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 数据备份策略

### 日常备份

每日自动备份：

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U temu_user temu_omni > /backup/temu_omni_$DATE.sql
# 保留30天
find /backup -name "temu_omni_*.sql" -mtime +30 -delete
```

### 重要时间点备份

在以下情况手动备份：
- 大版本升级前
- 批量数据导入前
- 重要功能上线前

