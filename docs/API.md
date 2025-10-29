# API 文档

## 基础信息

- **基础URL**: `http://localhost:8000/api`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 店铺管理 API

### 获取店铺列表

```http
GET /api/shops
```

**查询参数**：
- `skip`: 跳过记录数（分页）
- `limit`: 返回记录数（分页）

**响应示例**：
```json
[
  {
    "id": 1,
    "shop_id": "shop001",
    "shop_name": "美国店铺",
    "region": "US",
    "entity": "公司A",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### 创建店铺

```http
POST /api/shops
```

**请求体**：
```json
{
  "shop_id": "shop001",
  "shop_name": "美国店铺",
  "region": "US",
  "entity": "公司A",
  "access_token": "your_access_token",
  "description": "备注信息"
}
```

### 更新店铺

```http
PUT /api/shops/{shop_id}
```

### 删除店铺

```http
DELETE /api/shops/{shop_id}
```

## 订单管理 API

### 获取订单列表

```http
GET /api/orders
```

**查询参数**：
- `skip`: 跳过记录数
- `limit`: 返回记录数
- `shop_id`: 店铺ID筛选
- `status_filter`: 订单状态筛选
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应示例**：
```json
[
  {
    "id": 1,
    "order_sn": "ORDER001",
    "shop_id": 1,
    "product_name": "商品A",
    "quantity": 2,
    "unit_price": 10.00,
    "total_price": 20.00,
    "unit_cost": 5.00,
    "total_cost": 10.00,
    "profit": 10.00,
    "status": "completed",
    "order_time": "2024-01-01T10:00:00"
  }
]
```

### 创建订单

```http
POST /api/orders
```

### 更新订单

```http
PUT /api/orders/{order_id}
```

## 商品管理 API

### 获取商品列表

```http
GET /api/products
```

### 添加商品成本

```http
POST /api/products/costs
```

**请求体**：
```json
{
  "product_id": 1,
  "cost_price": 5.00,
  "currency": "USD",
  "effective_from": "2024-01-01T00:00:00",
  "notes": "批量采购价格"
}
```

## 统计分析 API

### 获取总览统计

```http
GET /api/statistics/overview
```

**查询参数**：
- `shop_ids`: 店铺ID列表（多个用逗号分隔）
- `start_date`: 开始日期
- `end_date`: 结束日期
- `status`: 订单状态

**响应示例**：
```json
{
  "total_orders": 100,
  "total_gmv": 10000.00,
  "total_cost": 5000.00,
  "total_profit": 5000.00,
  "avg_order_value": 100.00,
  "profit_margin": 50.00
}
```

### 获取每日统计

```http
GET /api/statistics/daily
```

**查询参数**：
- `shop_ids`: 店铺ID列表
- `start_date`: 开始日期
- `end_date`: 结束日期
- `days`: 天数（默认30）

**响应示例**：
```json
[
  {
    "date": "2024-01-01",
    "orders": 10,
    "gmv": 1000.00,
    "cost": 500.00,
    "profit": 500.00
  }
]
```

### 获取每周统计

```http
GET /api/statistics/weekly
```

### 获取每月统计

```http
GET /api/statistics/monthly
```

### 获取店铺对比

```http
GET /api/statistics/shops/comparison
```

### 获取销量趋势

```http
GET /api/statistics/trend
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

