# 实时计算GMV和利润的设计方案

## 一、问题分析

### 当前问题
1. **数据不一致**：订单同步时计算并存储GMV、成本、利润，如果商品价格或成本价变化，历史订单数据不会自动更新
2. **维护成本高**：需要重新同步订单才能更新数据
3. **数据冗余**：存储了可计算的数据，占用存储空间

### 改进目标
1. **实时计算**：查询时根据订单时间和商品信息，实时查找当时有效的价格和成本
2. **数据一致性**：商品价格或成本价变化时，历史订单统计自动反映最新数据
3. **灵活性**：支持价格历史追溯，准确反映订单当时的实际价格

## 二、设计方案

### 方案1：完全实时计算（推荐）

**核心思路**：
- 订单表只存储基础信息（订单号、商品SKU、数量、时间、product_id等）
- 不存储计算出的GMV、成本、利润
- 查询时通过JOIN商品表和成本表，实时计算

**优点**：
- 数据完全实时，价格变化立即反映
- 不需要维护冗余数据
- 支持价格历史追溯

**缺点**：
- 查询性能可能较慢（需要JOIN和子查询）
- 需要优化查询和添加索引

### 方案2：混合方案（缓存+实时）

**核心思路**：
- 订单表保留GMV、成本、利润字段，但标记为"缓存"字段
- 订单同步时不计算，或计算后标记为"需要更新"
- 查询时优先使用缓存字段，如果标记为过期则实时计算
- 提供后台任务定期更新缓存

**优点**：
- 查询性能好（有缓存）
- 支持实时计算（缓存过期时）
- 可以异步更新缓存

**缺点**：
- 需要维护缓存状态
- 实现复杂度较高

## 三、推荐方案：完全实时计算

### 1. 数据库设计

**订单表（orders）**：
- 保留：`product_id`, `product_sku`, `quantity`, `order_time`, `currency`
- 移除或标记为可选：`unit_price`, `total_price`, `unit_cost`, `total_cost`, `profit`
- 或者：保留这些字段但标记为"缓存字段"，不强制同步时计算

### 2. 实时计算逻辑

**计算GMV**：
```sql
-- 根据订单时间查找当时有效的供货价
SELECT 
    o.*,
    COALESCE(
        -- 查找订单时间有效的商品价格
        (SELECT p.current_price 
         FROM products p 
         WHERE p.id = o.product_id 
         AND p.created_at <= o.order_time
         ORDER BY p.created_at DESC 
         LIMIT 1),
        -- 如果没有历史价格，使用当前价格
        (SELECT p.current_price FROM products p WHERE p.id = o.product_id)
    ) * o.quantity AS total_price
FROM orders o
```

**计算成本**：
```sql
-- 根据订单时间查找当时有效的成本价
SELECT 
    o.*,
    COALESCE(
        -- 查找订单时间有效的成本价
        (SELECT pc.cost_price 
         FROM product_costs pc 
         WHERE pc.product_id = o.product_id 
         AND pc.effective_from <= o.order_time
         AND (pc.effective_to IS NULL OR pc.effective_to > o.order_time)
         ORDER BY pc.effective_from DESC 
         LIMIT 1),
        NULL
    ) * o.quantity AS total_cost
FROM orders o
```

**计算利润**：
```sql
-- 利润 = GMV - 成本
total_price - total_cost AS profit
```

### 3. SQLAlchemy实现

**使用子查询和JOIN**：
```python
from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.orm import aliased

# 创建子查询：获取订单时间有效的商品价格
product_price_subq = (
    select(Product.current_price)
    .where(
        and_(
            Product.id == Order.product_id,
            Product.created_at <= Order.order_time
        )
    )
    .order_by(Product.created_at.desc())
    .limit(1)
    .scalar_subquery()
)

# 创建子查询：获取订单时间有效的成本价
cost_price_subq = (
    select(ProductCost.cost_price)
    .where(
        and_(
            ProductCost.product_id == Order.product_id,
            ProductCost.effective_from <= Order.order_time,
            or_(
                ProductCost.effective_to.is_(None),
                ProductCost.effective_to > Order.order_time
            )
        )
    )
    .order_by(ProductCost.effective_from.desc())
    .limit(1)
    .scalar_subquery()
)

# 计算GMV、成本、利润
gmv = func.coalesce(product_price_subq, Product.current_price) * Order.quantity
cost = cost_price_subq * Order.quantity
profit = gmv - cost
```

### 4. 性能优化

**索引优化**：
```sql
-- 商品表
CREATE INDEX idx_products_id_created_at ON products(id, created_at);

-- 成本表
CREATE INDEX idx_product_costs_product_effective 
ON product_costs(product_id, effective_from, effective_to);

-- 订单表
CREATE INDEX idx_orders_product_time ON orders(product_id, order_time);
```

**查询优化**：
- 使用物化视图（Materialized View）缓存常用统计
- 使用Redis缓存统计结果
- 批量查询时使用CTE（Common Table Expression）

### 5. 迁移策略

**阶段1：添加实时计算功能**
- 保留现有字段
- 添加实时计算函数/方法
- 统计API优先使用实时计算

**阶段2：逐步迁移**
- 新订单不再计算和存储这些字段
- 旧订单可以继续使用存储的值，或切换到实时计算

**阶段3：完全切换**
- 移除或标记字段为可选
- 所有查询使用实时计算

## 四、实现步骤

### 步骤1：创建实时计算服务

**文件**: `backend/app/services/realtime_calculation.py`

```python
"""实时计算GMV和利润的服务"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case, and_, or_, subquery
from decimal import Decimal
from app.models.order import Order
from app.models.product import Product, ProductCost
from app.utils.currency import CurrencyConverter

class RealtimeCalculationService:
    """实时计算服务"""
    
    @staticmethod
    def calculate_order_gmv(db: Session, order: Order) -> Decimal:
        """计算订单GMV"""
        # 查找订单时间有效的商品价格
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if not product:
            return Decimal('0')
        
        # 使用当前价格（后续可以扩展为查找历史价格）
        supply_price = product.current_price or Decimal('0')
        return supply_price * Decimal(order.quantity)
    
    @staticmethod
    def calculate_order_cost(db: Session, order: Order) -> Decimal:
        """计算订单成本"""
        # 查找订单时间有效的成本价
        cost_record = db.query(ProductCost).filter(
            and_(
                ProductCost.product_id == order.product_id,
                ProductCost.effective_from <= order.order_time,
                or_(
                    ProductCost.effective_to.is_(None),
                    ProductCost.effective_to > order.order_time
                )
            )
        ).order_by(ProductCost.effective_from.desc()).first()
        
        if not cost_record:
            return Decimal('0')
        
        return cost_record.cost_price * Decimal(order.quantity)
    
    @staticmethod
    def calculate_order_profit(db: Session, order: Order) -> Decimal:
        """计算订单利润"""
        gmv = RealtimeCalculationService.calculate_order_gmv(db, order)
        cost = RealtimeCalculationService.calculate_order_cost(db, order)
        return gmv - cost
```

### 步骤2：修改统计查询

**文件**: `backend/app/services/statistics.py`

修改统计查询，使用实时计算而不是存储的字段。

### 步骤3：修改订单同步逻辑

**文件**: `backend/app/services/sync_service.py`

订单同步时不再计算和存储GMV、成本、利润，只存储基础信息。

## 五、性能考虑

### 1. 查询性能

**问题**：实时计算需要JOIN和子查询，可能较慢

**解决方案**：
- 使用索引优化
- 使用物化视图缓存统计结果
- 使用Redis缓存常用查询
- 批量查询时使用CTE优化

### 2. 缓存策略

**统计查询缓存**：
- 使用Redis缓存统计结果（5-10分钟）
- 当商品价格或成本价变化时，清除相关缓存

**订单查询缓存**：
- 单个订单的GMV/成本/利润可以缓存（1小时）
- 批量查询时使用批量计算

## 六、迁移计划

### 阶段1：准备（1-2天）
1. 创建实时计算服务
2. 添加数据库索引
3. 编写单元测试

### 阶段2：并行运行（3-5天）
1. 统计API支持实时计算和存储值两种模式
2. 对比两种方式的结果，确保一致性
3. 性能测试和优化

### 阶段3：切换（1-2天）
1. 所有查询切换到实时计算
2. 订单同步不再计算这些字段
3. 可选：保留字段但标记为废弃

### 阶段4：清理（可选）
1. 移除不再使用的字段
2. 清理相关代码

## 七、风险评估

### 风险1：查询性能下降
- **影响**：高
- **缓解**：使用缓存、索引优化、物化视图

### 风险2：数据不一致
- **影响**：中
- **缓解**：充分测试、对比验证

### 风险3：历史价格追溯
- **影响**：低
- **缓解**：商品表需要支持价格历史（当前只有当前价格）

## 八、后续优化

1. **价格历史表**：为商品价格创建历史记录表，支持价格变化追溯
2. **物化视图**：创建物化视图缓存常用统计，定期刷新
3. **异步计算**：对于复杂统计，使用异步任务计算并缓存结果



