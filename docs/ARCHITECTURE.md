# 📐 Luffy Store Omni - 系统架构文档

> 版本：v1.0  
> 更新时间：2024-10-29  
> 状态：待验证 Temu API 完整能力

## 📋 目录

1. [系统概述](#系统概述)
2. [技术架构](#技术架构)
3. [数据模型设计](#数据模型设计)
4. [Temu API 映射](#temu-api-映射)
5. [功能模块架构](#功能模块架构)
6. [数据流设计](#数据流设计)
7. [待验证需求](#待验证需求)

---

## 🎯 系统概述

### 业务目标

Luffy Store Omni 是一个跨境电商多店铺管理系统，主要用于：

- 统一管理多个地区、多个经营主体的 Temu 店铺
- 实时同步订单、商品、活动数据
- 提供数据统计、GMV分析、SKU分析、爆单榜等功能
- 支持成本录入和利润计算
- 物流和财务管理

### 核心特性

1. **多店铺管理** - 支持不同地区（US/UK/DE/FR/AU等）店铺
2. **数据同步** - 定时从 Temu API 同步最新数据
3. **财务分析** - 成本、利润、GMV 等财务指标
4. **业绩追踪** - 按负责人统计销售业绩（爆单榜）
5. **物流追踪** - 订单物流状态管理
6. **数据可视化** - 多维度数据报表和图表

---

## 🏗 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                      │
│  React 18 + TypeScript + Ant Design + ECharts               │
│  - 深色极客主题                                               │
│  - 响应式设计                                                 │
│  - 实时数据更新                                               │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────────────────────────┐
│                      API 网关层 (Gateway)                      │
│  FastAPI + Uvicorn/Gunicorn                                 │
│  - 路由管理                                                   │
│  - 请求验证                                                   │
│  - 异常处理                                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                      业务逻辑层 (Services)                     │
│  - 店铺管理服务                                               │
│  - 订单同步服务                                               │
│  - 商品管理服务                                               │
│  - 统计分析服务                                               │
│  - 物流管理服务                                               │
│  - 财务管理服务                                               │
└─────────┬──────────────────────┬────────────────────────────┘
          │                      │
┌─────────▼─────────┐  ┌────────▼──────────┐
│  数据访问层 (DAL)   │  │  外部 API 集成层   │
│  SQLAlchemy ORM   │  │  Temu API Client  │
│  - 模型定义        │  │  - 签名生成        │
│  - CRUD 操作      │  │  - 请求封装        │
│  - 事务管理        │  │  - 错误处理        │
└─────────┬─────────┘  └───────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────┐
│                      数据存储层 (Storage)                      │
│  - PostgreSQL 13 (主数据库)                                   │
│  - Redis 7 (缓存 + 消息队列)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈详情

**前端技术栈：**
- React 18.3 + TypeScript
- Ant Design 5.x (UI 组件库)
- ECharts (数据可视化)
- React Query (数据获取和缓存)
- React Router (路由管理)
- Vite (构建工具)

**后端技术栈：**
- Python 3.9+
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- Pydantic (数据验证)
- Pandas (数据分析)
- Loguru (日志管理)

**数据库：**
- PostgreSQL 13 (关系型数据库)
- Redis 7 (缓存和队列)

**部署：**
- Docker + Docker Compose
- Nginx (生产环境反向代理)
- Gunicorn + Uvicorn (生产环境应用服务器)

---

## 🗄 数据模型设计

### 核心实体关系图 (ERD)

```
┌──────────────────────┐
│       Shop           │
│  (店铺)               │
├──────────────────────┤
│ id (PK)              │
│ shop_id              │ Temu店铺ID
│ shop_name            │ 店铺名称
│ region               │ 地区 (US/UK/DE...)
│ entity               │ 经营主体
│ app_key              │ API密钥
│ app_secret           │ API密钥
│ access_token         │ 访问令牌
│ is_active            │ 是否启用
│ last_sync_at         │ 最后同步时间
└──────────┬───────────┘
           │ 1
           │
           │ N
┌──────────▼───────────┐       ┌──────────────────────┐
│      Order           │   N   │     Product          │
│  (订单)               │◄──────┤  (商品)               │
├──────────────────────┤       ├──────────────────────┤
│ id (PK)              │       │ id (PK)              │
│ shop_id (FK)         │       │ shop_id (FK)         │
│ order_sn             │       │ product_id           │ Temu商品ID
│ temu_order_id        │       │ product_name         │
│ product_id (FK)      │       │ sku                  │
│ product_name         │       │ current_price        │
│ product_sku          │       │ currency             │
│ quantity             │       │ stock_quantity       │
│ unit_price           │       │ is_active            │
│ total_price          │       │ category             │
│ currency             │       │ manager              │ 负责人
│ unit_cost            │       │ created_at           │
│ total_cost           │       │ updated_at           │
│ profit               │       └──────────┬───────────┘
│ status               │                  │ 1
│ order_time           │                  │
│ payment_time         │                  │ N
│ shipping_time        │       ┌──────────▼───────────┐
│ delivery_time        │       │   ProductCost        │
│ shipping_country     │       │  (商品成本)           │
│ created_at           │       ├──────────────────────┤
│ updated_at           │       │ id (PK)              │
└──────────────────────┘       │ product_id (FK)      │
                               │ cost_price           │ 成本价
                               │ currency             │
                               │ effective_from       │ 生效开始
                               │ effective_to         │ 生效结束
                               │ notes                │
                               │ created_at           │
                               └──────────────────────┘

┌──────────────────────┐
│     Activity         │
│  (活动)               │
├──────────────────────┤
│ id (PK)              │
│ shop_id (FK)         │
│ activity_id          │ Temu活动ID
│ activity_name        │
│ activity_type        │
│ start_time           │
│ end_time             │
│ is_active            │
│ description          │
│ created_at           │
└──────────────────────┘

┌──────────────────────┐
│   SystemConfig       │
│  (系统配置)           │
├──────────────────────┤
│ id (PK)              │
│ key                  │ 配置键
│ value                │ 配置值
│ description          │
│ created_at           │
│ updated_at           │
└──────────────────────┘
```

### 数据模型详细说明

#### 1. Shop (店铺表)

```python
shop_id: str           # Temu店铺唯一标识
shop_name: str         # 店铺名称
region: str            # 地区代码 (US/UK/DE/FR/AU/CA/IT/ES/JP/KR)
entity: str            # 经营主体
app_key: str           # Temu App Key (可选，优先使用系统级配置)
app_secret: str        # Temu App Secret (可选)
access_token: str      # 店铺访问令牌 (必需)
refresh_token: str     # 刷新令牌
token_expires_at: datetime  # 令牌过期时间
is_active: bool        # 是否启用
last_sync_at: datetime # 最后数据同步时间
```

**设计说明：**
- 支持应用级和店铺级API配置
- access_token 是店铺独立授权
- 支持多地区、多主体店铺管理

#### 2. Order (订单表)

```python
order_sn: str              # 系统订单编号 (唯一)
temu_order_id: str         # Temu平台订单ID (唯一)
product_id: int            # 关联商品ID (FK)
product_name: str          # 商品名称 (冗余存储)
product_sku: str           # 商品SKU
quantity: int              # 购买数量
unit_price: Decimal        # 单价
total_price: Decimal       # 订单总价
currency: str              # 货币 (USD/EUR/GBP等)
unit_cost: Decimal         # 单位成本
total_cost: Decimal        # 总成本
profit: Decimal            # 利润 (total_price - total_cost)
status: OrderStatus        # 订单状态枚举
order_time: datetime       # 下单时间
payment_time: datetime     # 支付时间
shipping_time: datetime    # 发货时间
delivery_time: datetime    # 送达时间
customer_id: str           # 客户ID
shipping_country: str      # 收货国家
```

**订单状态枚举：**
```python
PENDING = "pending"        # 待支付
PAID = "paid"             # 已支付
SHIPPED = "shipped"       # 已发货
DELIVERED = "delivered"   # 已送达
COMPLETED = "completed"   # 已完成
CANCELLED = "cancelled"   # 已取消
REFUNDED = "refunded"     # 已退款
```

**设计说明：**
- 冗余存储商品信息，避免历史订单受商品变更影响
- 利润自动计算：profit = total_price - total_cost
- 完整的订单生命周期时间戳

#### 3. Product (商品表)

```python
product_id: str           # Temu商品ID
product_name: str         # 商品名称
sku: str                  # 商品SKU
current_price: Decimal    # 当前售价
currency: str             # 货币
stock_quantity: int       # 库存数量
is_active: bool           # 是否在售
description: str          # 商品描述
image_url: str            # 商品图片URL
category: str             # 商品分类
manager: str              # 负责人 (用于爆单榜统计)
```

**设计说明：**
- manager字段用于业绩统计和爆单榜
- 支持历史成本记录（通过ProductCost表）

#### 4. ProductCost (商品成本表)

```python
product_id: int           # 关联商品ID (FK)
cost_price: Decimal       # 成本价
currency: str             # 货币
effective_from: datetime  # 生效开始时间
effective_to: datetime    # 生效结束时间
notes: str                # 备注
```

**设计说明：**
- 支持成本历史记录
- 通过时间范围查询历史成本
- 用于准确计算历史订单利润

#### 5. Activity (活动表)

```python
activity_id: str          # Temu活动ID
activity_name: str        # 活动名称
activity_type: ActivityType  # 活动类型
start_time: datetime      # 开始时间
end_time: datetime        # 结束时间
is_active: bool           # 是否进行中
description: str          # 活动描述
```

**活动类型枚举：**
```python
DISCOUNT = "discount"         # 折扣活动
FLASH_SALE = "flash_sale"    # 限时抢购
COUPON = "coupon"            # 优惠券
BUNDLE = "bundle"            # 组合优惠
```

---

## 🔌 Temu API 映射

### API 端点清单

基于现有代码，系统使用以下 Temu API：

#### 1. 订单相关 API

| API 端点 | 方法 | 功能 | 系统模型 | 状态 |
|---------|------|------|---------|------|
| `/api/order/list` | POST | 获取订单列表 | Order | ✅ 已实现 |
| `/api/order/detail` | POST | 获取订单详情 | Order | ✅ 已实现 |

**请求参数 (order/list)：**
```json
{
  "app_key": "string",
  "access_token": "string",
  "timestamp": 1234567890,
  "start_time": 1234567890,    // Unix时间戳
  "end_time": 1234567890,      // Unix时间戳
  "page": 1,
  "page_size": 100,
  "status": "optional",         // 订单状态筛选
  "sign": "signature"
}
```

**响应数据映射：**
```
Temu API 响应          →  系统 Order 模型
────────────────────────────────────────────
order_sn              →  order_sn
order_id              →  temu_order_id
product_name          →  product_name
sku                   →  product_sku
quantity              →  quantity
unit_price            →  unit_price
total_amount          →  total_price
currency              →  currency
status                →  status
order_time            →  order_time
payment_time          →  payment_time
shipping_time         →  shipping_time
delivery_time         →  delivery_time
customer_id           →  customer_id
shipping_country      →  shipping_country
```

#### 2. 商品相关 API

| API 端点 | 方法 | 功能 | 系统模型 | 状态 |
|---------|------|------|---------|------|
| `/api/product/list` | POST | 获取商品列表 | Product | ✅ 已实现 |
| `/api/product/detail` | POST | 获取商品详情 | Product | ✅ 已实现 |

**请求参数 (product/list)：**
```json
{
  "app_key": "string",
  "access_token": "string",
  "timestamp": 1234567890,
  "page": 1,
  "page_size": 100,
  "status": "optional",         // 商品状态筛选
  "sign": "signature"
}
```

**响应数据映射：**
```
Temu API 响应          →  系统 Product 模型
────────────────────────────────────────────
product_id            →  product_id
product_name          →  product_name
sku                   →  sku
price                 →  current_price
currency              →  currency
stock                 →  stock_quantity
status                →  is_active
description           →  description
image_url             →  image_url
category              →  category
```

#### 3. 活动相关 API

| API 端点 | 方法 | 功能 | 系统模型 | 状态 |
|---------|------|------|---------|------|
| `/api/activity/list` | POST | 获取活动列表 | Activity | ✅ 已实现 |

**请求参数 (activity/list)：**
```json
{
  "app_key": "string",
  "access_token": "string",
  "timestamp": 1234567890,
  "start_time": 1234567890,
  "end_time": 1234567890,
  "page": 1,
  "page_size": 100,
  "sign": "signature"
}
```

### API 签名机制

```python
def generate_sign(params: dict, app_secret: str) -> str:
    """
    Temu API 签名生成规则：
    1. 按参数名排序
    2. 拼接为 key1value1key2value2...
    3. 在前后添加 app_secret
    4. 进行 HMAC-SHA256 签名
    5. 转大写返回
    """
    # 1. 排序参数
    sorted_params = sorted(params.items())
    
    # 2. 拼接字符串
    param_str = ""
    for key, value in sorted_params:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        param_str += f"{key}{value}"
    
    # 3. 签名
    sign_str = app_secret + param_str + app_secret
    sign = hmac.new(
        app_secret.encode('utf-8'),
        sign_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return sign
```

---

## 📦 功能模块架构

### 模块划分

```
Luffy Store Omni
│
├── 📊 Dashboard (仪表板)
│   ├── 核心指标卡片 (订单量/GMV/利润/利润率)
│   ├── 近30天销售趋势图
│   └── 店铺业绩对比图
│
├── 🏪 Shop Management (店铺管理)
│   ├── 店铺列表
│   ├── 添加/编辑店铺
│   ├── 店铺授权配置
│   └── 数据同步管理
│
├── 📦 Order Management (订单管理)
│   ├── 订单列表 (紧凑表格)
│   ├── 订单详情
│   ├── 订单筛选 (状态/时间/店铺)
│   ├── 批量操作
│   └── 订单导出
│
├── 🛍️ Product Management (商品管理)
│   ├── 商品列表 (紧凑表格)
│   ├── 商品详情
│   ├── 成本录入
│   ├── 负责人分配
│   └── 批量操作
│
├── 🚚 Logistics Management (物流管理) ⭐ 新增
│   ├── 物流单号追踪
│   ├── 承运商管理
│   ├── 物流状态监控
│   ├── 异常订单处理
│   └── 物流报表
│
├── 💰 Finance Management (财务管理) ⭐ 新增
│   ├── 财务报表
│   ├── 收入统计
│   ├── 成本分析
│   ├── 利润分析
│   ├── 结算管理
│   └── 账单导出
│
├── 📈 Statistics (数据统计)
│   ├── 多维度数据分析
│   ├── 时间序列分析
│   ├── 趋势预测
│   └── 自定义报表
│
├── 📋 GMV Table (GMV表格)
│   ├── 按日/周/月查看GMV
│   ├── 店铺GMV对比
│   ├── GMV趋势分析
│   └── 数据导出
│
├── 📊 SKU Analysis (SKU分析)
│   ├── SKU销量排行
│   ├── SKU对比分析
│   ├── 负责人业绩
│   └── SKU趋势分析
│
├── 👑 Hot Seller Ranking (爆单榜)
│   ├── 负责人销量排行
│   ├── SKU销量统计
│   ├── 业绩达成率
│   └── 排行趋势
│
└── ⚙️ System Settings (系统设置)
    ├── 应用级API配置
    ├── 同步策略设置
    ├── 用户管理
    └── 系统参数
```

### 模块依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Pages                        │
│  Dashboard | Shops | Orders | Products | ...            │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│                    API Endpoints                         │
│  /api/shops | /api/orders | /api/products | ...         │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│                  Business Services                       │
│  ShopService | OrderService | ProductService | ...      │
└────────────┬──────────────────┬─────────────────────────┘
             │                  │
┌────────────▼──────┐  ┌───────▼──────────┐
│   Database Layer   │  │  Temu API Client │
│   PostgreSQL       │  │                  │
└────────────────────┘  └──────────────────┘
```

---

## 🔄 数据流设计

### 1. 数据同步流程

```
┌─────────────┐
│  定时任务     │ 每30分钟触发
│  Schedule    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│  1. 遍历所有启用的店铺                 │
│     shop.is_active == True          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  2. 调用 Temu API 获取数据            │
│     - orders/list                   │
│     - products/list                 │
│     - activities/list               │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  3. 数据清洗和转换                    │
│     - 格式标准化                      │
│     - 数据验证                        │
│     - 关联关系处理                    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  4. 存储到数据库                      │
│     - Upsert 策略                    │
│     - 事务处理                        │
│     - 错误回滚                        │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  5. 更新店铺同步时间                  │
│     shop.last_sync_at = now()       │
└──────────────────────────────────────┘
```

### 2. 订单处理流程

```
┌─────────────┐
│  Temu API   │
│  订单数据    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│  1. 订单基础信息入库                  │
│     - order_sn                      │
│     - product_name                  │
│     - total_price                   │
│     - status                        │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  2. 关联商品信息                      │
│     - 通过 product_sku 匹配          │
│     - 获取 product_id               │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  3. 获取商品成本                      │
│     - 查询 ProductCost              │
│     - 根据 order_time 匹配有效成本   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  4. 计算利润                          │
│     profit = total_price - total_cost│
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  5. 更新订单完整信息                  │
│     - unit_cost                     │
│     - total_cost                    │
│     - profit                        │
└──────────────────────────────────────┘
```

### 3. 统计分析流程

```
┌─────────────┐
│  用户请求    │ GET /api/statistics/overview
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│  1. 查询数据库                        │
│     - 聚合查询 (GROUP BY)            │
│     - 时间范围筛选                    │
│     - 店铺筛选                        │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  2. Redis 缓存检查                    │
│     - 检查缓存是否存在                │
│     - 缓存有效期 5分钟                │
└──────┬───────────────────────────────┘
       │
       ├─ 缓存命中 ──────────┐
       │                    │
       ├─ 缓存未命中         │
       ▼                    │
┌──────────────────┐        │
│  3. 数据聚合计算  │        │
│     - SUM()      │        │
│     - AVG()      │        │
│     - COUNT()    │        │
└──────┬───────────┘        │
       │                    │
       ▼                    │
┌──────────────────┐        │
│  4. 写入缓存      │        │
└──────┬───────────┘        │
       │                    │
       └────────────────────┤
                            │
                            ▼
                   ┌──────────────────┐
                   │  5. 返回数据      │
                   └──────────────────┘
```

---

## ⚠️ 待验证需求

### 🔍 需要从 Temu API 文档确认的能力

请参考 [Temu API 文档](https://agentpartner.temu.com/document?cataId=875198836203&docId=877385749076) 验证以下内容：

#### 1. 物流管理相关 API

| 需求 | API 端点（待确认） | 优先级 | 备注 |
|------|------------------|--------|------|
| 获取物流追踪信息 | `/api/logistics/tracking` ? | ⭐⭐⭐ | 物流单号、承运商、状态 |
| 获取物流公司列表 | `/api/logistics/carriers` ? | ⭐⭐ | 承运商信息 |
| 更新物流状态 | `/api/logistics/update` ? | ⭐⭐ | 如需手动更新 |

**数据需求：**
- 物流单号 (tracking_number)
- 承运商信息 (carrier_name, carrier_code)
- 物流状态 (pending, shipped, in_transit, delivered, exception)
- 物流时间线 (timeline events)
- 物流异常信息

#### 2. 财务管理相关 API

| 需求 | API 端点（待确认） | 优先级 | 备注 |
|------|------------------|--------|------|
| 获取结算信息 | `/api/finance/settlement` ? | ⭐⭐⭐ | 结算周期、金额 |
| 获取交易流水 | `/api/finance/transactions` ? | ⭐⭐⭐ | 收入、退款、手续费 |
| 获取账户余额 | `/api/finance/balance` ? | ⭐⭐ | 可用余额、冻结金额 |
| 获取手续费明细 | `/api/finance/fees` ? | ⭐⭐ | 平台佣金、支付手续费 |

**数据需求：**
- 结算状态 (pending, settled, failed)
- 结算金额和周期
- 交易手续费
- 退款信息
- 账户余额

#### 3. 订单详细信息

| 需求 | 字段（待确认） | 优先级 | 备注 |
|------|--------------|--------|------|
| 订单成本价格 | `cost_price` ? | ⭐⭐⭐ | 用于利润计算 |
| 物流信息 | `tracking_number`, `carrier` ? | ⭐⭐⭐ | 关联物流 |
| 客户信息 | `customer_name`, `email` ? | ⭐⭐ | 可选 |
| 支付方式 | `payment_method` ? | ⭐⭐ | 财务分析 |
| 手续费 | `platform_fee`, `payment_fee` ? | ⭐⭐ | 利润计算 |

#### 4. 商品详细信息

| 需求 | 字段（待确认） | 优先级 | 备注 |
|------|--------------|--------|------|
| 商品成本价 | `cost_price` ? | ⭐⭐⭐ | 利润计算核心 |
| 商品规格 | `specifications` ? | ⭐⭐ | SKU详情 |
| 多图片支持 | `images[]` ? | ⭐ | 商品展示 |
| 销量数据 | `total_sales` ? | ⭐⭐ | 分析使用 |

#### 5. 店铺信息

| 需求 | 字段（待确认） | 优先级 | 备注 |
|------|--------------|--------|------|
| 店铺统计数据 | `shop_stats` ? | ⭐⭐ | 总销量、总GMV |
| 店铺评分 | `rating` ? | ⭐ | 可选 |
| 店铺等级 | `level` ? | ⭐ | 可选 |

#### 6. Webhook 支持

| 需求 | 能力（待确认） | 优先级 | 备注 |
|------|--------------|--------|------|
| 订单状态变更通知 | Webhook | ⭐⭐⭐ | 实时更新 |
| 库存变更通知 | Webhook | ⭐⭐ | 实时库存 |
| 物流状态更新通知 | Webhook | ⭐⭐⭐ | 物流追踪 |

### 📋 验证清单

请查阅 Temu API 文档并填写：

- [ ] 物流追踪API是否支持？API端点是什么？
- [ ] 财务结算API是否支持？API端点是什么？
- [ ] 订单数据是否包含成本价格？字段名是什么？
- [ ] 订单数据是否包含物流信息？字段名是什么？
- [ ] 订单数据是否包含手续费信息？字段名是什么？
- [ ] 商品数据是否包含成本价格？字段名是什么？
- [ ] 商品数据是否包含销量统计？字段名是什么？
- [ ] 是否支持Webhook推送？如何配置？
- [ ] API限流策略是什么？（QPS限制）
- [ ] 批量API是否支持？单次最大数量？

### 🔄 备选方案

如果 Temu API 不支持某些功能，我们的备选方案：

| 功能 | Temu API 不支持的备选方案 |
|------|------------------------|
| 物流追踪 | 手动录入物流单号 + 第三方物流API查询 |
| 商品成本 | 系统内手动录入成本（已实现ProductCost表） |
| 财务结算 | 根据订单数据自行计算 + 手动录入手续费 |
| Webhook | 定时轮询API（已实现，可调整频率） |
| 手续费 | 系统配置固定费率 + 手动调整 |

---

## 📊 系统容量规划

### 数据量预估

| 实体 | 日增长 | 月增长 | 年增长 | 存储空间（年） |
|------|--------|--------|--------|-------------|
| 订单 | 1000 | 30K | 360K | ~500MB |
| 商品 | 50 | 1.5K | 18K | ~50MB |
| 活动 | 10 | 300 | 3.6K | ~10MB |
| 成本记录 | 20 | 600 | 7.2K | ~5MB |

**总计：** 约 600MB/年（单店铺）

**10店铺：** 约 6GB/年

### 性能指标

| 指标 | 目标值 | 当前架构支持 |
|------|--------|------------|
| API响应时间 | < 500ms | ✅ FastAPI + 索引优化 |
| 页面加载时间 | < 2s | ✅ React Query缓存 |
| 并发用户 | 100+ | ✅ Gunicorn多进程 |
| 数据同步延迟 | 30分钟 | ✅ 定时任务可调整 |
| 数据库查询 | < 100ms | ✅ PostgreSQL索引 |

---

## 🔐 安全设计

### API安全

1. **Temu API签名验证** - HMAC-SHA256签名
2. **HTTPS加密传输** - 生产环境必须
3. **Access Token管理** - 安全存储，定期刷新
4. **请求限流** - 防止API滥用

### 数据安全

1. **敏感数据加密** - app_secret, access_token加密存储
2. **SQL注入防护** - SQLAlchemy ORM参数化查询
3. **XSS防护** - React自动转义
4. **CORS配置** - 限制允许的域名

---

## 📝 开发规范

### 代码规范

- **Python**: PEP 8 + Black格式化
- **TypeScript**: ESLint + Prettier
- **Git**: Conventional Commits
- **API**: RESTful设计原则

### 数据库规范

- 所有表必须有 `id` 主键
- 所有表必须有 `created_at` 和 `updated_at`
- 外键必须设置级联删除策略
- 索引命名：`idx_{table}_{column}`
- 约束命名：`uk_{table}_{column}` (unique)

---

## 🚀 后续优化方向

### 功能增强

1. **用户权限管理** - 多用户、角色权限
2. **数据导出增强** - Excel/CSV批量导出
3. **报表订阅** - 邮件定时推送报表
4. **预警系统** - 库存预警、异常订单预警
5. **移动端适配** - 响应式设计优化

### 性能优化

1. **Redis缓存扩展** - 热点数据缓存
2. **数据库读写分离** - 主从复制
3. **CDN加速** - 静态资源分发
4. **数据分区** - 按时间分区历史数据
5. **API批量操作** - 减少请求次数

### 技术升级

1. **消息队列** - RabbitMQ/Kafka处理异步任务
2. **搜索引擎** - Elasticsearch全文搜索
3. **监控告警** - Prometheus + Grafana
4. **日志分析** - ELK Stack
5. **容器编排** - Kubernetes

---

## 📚 相关文档

- [部署指南](GITHUB_DEPLOYMENT.md)
- [API文档](API.md)
- [数据库设计](DATABASE_SCHEMA.md)
- [Temu API指南](TEMU_API_GUIDE.md)

---

**文档维护：** 本文档需要在验证Temu API能力后更新

**更新记录：**
- 2024-10-29: 初始版本，基于现有代码创建
- 待更新: 根据Temu API文档完善物流、财务相关能力


