# 📊 API与数据结构映射图

## Temu API ↔️ 系统数据流图

```mermaid
graph TB
    subgraph "Temu API"
        A1[order/list<br/>订单列表API]
        A2[order/detail<br/>订单详情API]
        A3[product/list<br/>商品列表API]
        A4[product/detail<br/>商品详情API]
        A5[activity/list<br/>活动列表API]
    end
    
    subgraph "系统数据同步层"
        B1[OrderSyncService]
        B2[ProductSyncService]
        B3[ActivitySyncService]
    end
    
    subgraph "数据库表"
        C1[(orders<br/>订单表)]
        C2[(products<br/>商品表)]
        C3[(product_costs<br/>成本表)]
        C4[(activities<br/>活动表)]
        C5[(shops<br/>店铺表)]
    end
    
    subgraph "业务功能"
        D1[订单管理]
        D2[商品管理]
        D3[财务分析]
        D4[SKU分析]
        D5[爆单榜]
        D6[物流管理]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B2
    A5 --> B3
    
    B1 --> C1
    B2 --> C2
    B2 --> C3
    B3 --> C4
    
    C5 -.关联.-> C1
    C5 -.关联.-> C2
    C5 -.关联.-> C4
    C2 -.关联.-> C3
    C2 -.关联.-> C1
    
    C1 --> D1
    C1 --> D3
    C1 --> D6
    C2 --> D2
    C2 --> D4
    C2 --> D5
    C3 --> D3
    C4 --> D2
```

## 数据实体关系图 (ERD)

```mermaid
erDiagram
    SHOP ||--o{ ORDER : "has"
    SHOP ||--o{ PRODUCT : "has"
    SHOP ||--o{ ACTIVITY : "has"
    PRODUCT ||--o{ ORDER : "belongs_to"
    PRODUCT ||--o{ PRODUCT_COST : "has_history"
    
    SHOP {
        int id PK
        string shop_id UK "Temu店铺ID"
        string shop_name "店铺名称"
        string region "地区"
        string entity "经营主体"
        string access_token "访问令牌"
        boolean is_active "是否启用"
        datetime last_sync_at "最后同步时间"
    }
    
    ORDER {
        int id PK
        int shop_id FK
        string order_sn UK "订单编号"
        string temu_order_id UK "Temu订单ID"
        int product_id FK
        string product_name "商品名称"
        string product_sku "SKU"
        int quantity "数量"
        decimal unit_price "单价"
        decimal total_price "总价"
        decimal unit_cost "单位成本"
        decimal total_cost "总成本"
        decimal profit "利润"
        enum status "状态"
        datetime order_time "下单时间"
        datetime payment_time "支付时间"
        datetime shipping_time "发货时间"
        datetime delivery_time "送达时间"
        string shipping_country "收货国家"
    }
    
    PRODUCT {
        int id PK
        int shop_id FK
        string product_id "Temu商品ID"
        string product_name "商品名称"
        string sku UK "商品SKU"
        decimal current_price "当前售价"
        int stock_quantity "库存数量"
        boolean is_active "是否在售"
        string category "分类"
        string manager "负责人"
    }
    
    PRODUCT_COST {
        int id PK
        int product_id FK
        decimal cost_price "成本价"
        datetime effective_from "生效开始"
        datetime effective_to "生效结束"
    }
    
    ACTIVITY {
        int id PK
        int shop_id FK
        string activity_id "Temu活动ID"
        string activity_name "活动名称"
        enum activity_type "活动类型"
        datetime start_time "开始时间"
        datetime end_time "结束时间"
        boolean is_active "是否进行中"
    }
```

## API 请求与响应映射

### 1. 订单API映射

```mermaid
sequenceDiagram
    participant S as 系统
    participant T as Temu API
    participant DB as 数据库
    
    S->>T: POST /api/order/list
    Note over S,T: 参数：start_time, end_time, page
    T-->>S: 订单列表数据
    Note over T,S: order_sn, product_name,<br/>unit_price, total_amount, status
    
    loop 每个订单
        S->>S: 数据转换
        Note over S: order_sn → order_sn<br/>total_amount → total_price<br/>status → OrderStatus枚举
        
        S->>DB: 查询商品成本
        Note over S,DB: 根据 product_sku 和 order_time
        DB-->>S: unit_cost
        
        S->>S: 计算利润
        Note over S: profit = total_price - total_cost
        
        S->>DB: Upsert订单
        Note over S,DB: 基于 order_sn 唯一键
    end
```

### 2. 商品API映射

```mermaid
sequenceDiagram
    participant S as 系统
    participant T as Temu API
    participant DB as 数据库
    
    S->>T: POST /api/product/list
    Note over S,T: 参数：page, page_size, status
    T-->>S: 商品列表数据
    Note over T,S: product_id, product_name,<br/>sku, price, stock
    
    loop 每个商品
        S->>S: 数据转换
        Note over S: product_id → product_id<br/>price → current_price<br/>stock → stock_quantity
        
        S->>DB: Upsert商品
        Note over S,DB: 基于 shop_id + product_id
        
        alt 商品已存在
            S->>DB: 更新价格和库存
        else 新商品
            S->>DB: 创建新记录
            Note over S,DB: 初始化 manager 为空<br/>需要手动分配
        end
    end
```

## 数据字段详细映射表

### Order 数据映射

| Temu API 字段 | 类型 | 系统字段 | 数据库类型 | 转换说明 |
|--------------|------|---------|-----------|---------|
| order_sn | string | order_sn | VARCHAR(100) | 直接映射 |
| order_id | string | temu_order_id | VARCHAR(100) | 直接映射 |
| product_name | string | product_name | VARCHAR(500) | 直接映射 |
| sku | string | product_sku | VARCHAR(200) | 直接映射 |
| quantity | integer | quantity | INTEGER | 直接映射 |
| unit_price | decimal | unit_price | NUMERIC(10,2) | 金额格式化 |
| total_amount | decimal | total_price | NUMERIC(10,2) | 金额格式化 |
| currency | string | currency | VARCHAR(10) | 直接映射 |
| status | string | status | ENUM | 转为OrderStatus枚举 |
| order_time | timestamp | order_time | DATETIME | Unix时间戳转换 |
| payment_time | timestamp | payment_time | DATETIME | Unix时间戳转换 |
| shipping_time | timestamp | shipping_time | DATETIME | Unix时间戳转换 |
| delivery_time | timestamp | delivery_time | DATETIME | Unix时间戳转换 |
| customer_id | string | customer_id | VARCHAR(100) | 直接映射 |
| shipping_country | string | shipping_country | VARCHAR(50) | 直接映射 |
| - | - | unit_cost | NUMERIC(10,2) | **系统计算** |
| - | - | total_cost | NUMERIC(10,2) | **系统计算** |
| - | - | profit | NUMERIC(10,2) | **系统计算** |

### Product 数据映射

| Temu API 字段 | 类型 | 系统字段 | 数据库类型 | 转换说明 |
|--------------|------|---------|-----------|---------|
| product_id | string | product_id | VARCHAR(100) | 直接映射 |
| product_name | string | product_name | VARCHAR(500) | 直接映射 |
| sku | string | sku | VARCHAR(200) | 直接映射 |
| price | decimal | current_price | NUMERIC(10,2) | 金额格式化 |
| currency | string | currency | VARCHAR(10) | 直接映射 |
| stock | integer | stock_quantity | INTEGER | 直接映射 |
| status | boolean/string | is_active | BOOLEAN | 状态转布尔值 |
| description | string | description | TEXT | 直接映射 |
| image_url | string | image_url | VARCHAR(500) | 直接映射 |
| category | string | category | VARCHAR(200) | 直接映射 |
| - | - | manager | VARCHAR(100) | **手动录入** |

### Activity 数据映射

| Temu API 字段 | 类型 | 系统字段 | 数据库类型 | 转换说明 |
|--------------|------|---------|-----------|---------|
| activity_id | string | activity_id | VARCHAR(100) | 直接映射 |
| activity_name | string | activity_name | VARCHAR(500) | 直接映射 |
| activity_type | string | activity_type | ENUM | 转为ActivityType枚举 |
| start_time | timestamp | start_time | DATETIME | Unix时间戳转换 |
| end_time | timestamp | end_time | DATETIME | Unix时间戳转换 |
| status | string | is_active | BOOLEAN | 根据时间判断 |
| description | string | description | TEXT | 直接映射 |

## 系统扩展字段说明

### 扩展字段来源

| 字段 | 所属表 | 来源 | 用途 |
|------|--------|------|------|
| manager | products | **手动录入** | 业绩统计、爆单榜 |
| unit_cost | orders | **系统计算**（来自product_costs） | 利润计算 |
| total_cost | orders | **系统计算**（unit_cost × quantity） | 利润计算 |
| profit | orders | **系统计算**（total_price - total_cost） | 财务分析 |
| cost_price | product_costs | **手动录入** | 成本管理 |
| effective_from | product_costs | **手动录入** | 成本历史 |
| effective_to | product_costs | **手动录入** | 成本历史 |

## 数据同步策略

### 同步频率

```mermaid
gantt
    title 数据同步时间线
    dateFormat HH:mm
    axisFormat %H:%M
    
    section 订单数据
    API调用（30分钟/次）     :a1, 00:00, 30m
    API调用                  :a2, 00:30, 30m
    API调用                  :a3, 01:00, 30m
    
    section 商品数据
    API调用（1小时/次）      :b1, 00:00, 1h
    API调用                  :b2, 01:00, 1h
    
    section 活动数据
    API调用（6小时/次）      :c1, 00:00, 6h
```

### 同步优先级

| 数据类型 | 同步频率 | 优先级 | 原因 |
|---------|---------|--------|------|
| 订单 | 30分钟 | ⭐⭐⭐ | 实时性要求高 |
| 商品 | 1小时 | ⭐⭐ | 价格、库存变化 |
| 活动 | 6小时 | ⭐ | 变化频率低 |

## 待确认的API能力

### 🔴 高优先级（必需）

1. **订单成本数据**
   - API是否返回成本价？
   - 字段名称：`cost_price` / `purchase_price` ?
   - 如果没有，需要系统内手动维护

2. **物流追踪信息**
   - 订单API是否包含物流单号？
   - 是否有专门的物流追踪API？
   - 字段：`tracking_number`, `carrier_name` ?

3. **手续费信息**
   - 订单API是否包含手续费？
   - 字段：`platform_fee`, `payment_fee` ?
   - 用于准确计算利润

### 🟡 中优先级（重要）

4. **财务结算API**
   - 是否有结算报表API？
   - 是否有资金流水API？
   - 用于财务管理模块

5. **商品销量统计**
   - 商品API是否包含销量数据？
   - 字段：`total_sales`, `monthly_sales` ?

### 🟢 低优先级（可选）

6. **Webhook支持**
   - 是否支持订单状态变更推送？
   - 是否支持库存变更推送？

7. **批量API**
   - 是否支持批量查询？
   - 单次最大数量限制？

## 使用建议

1. **先阅读 Temu API 文档**，对照本文档验证API能力
2. **填写"待确认"清单**，标注实际API端点和字段名
3. **更新 ARCHITECTURE.md**，补充验证后的信息
4. **调整代码实现**，根据实际API响应格式修改
5. **完善错误处理**，处理API限流、异常情况

---

**文档状态：** ⚠️ 待验证 Temu API  
**下一步：** 查阅官方文档并更新本文档

