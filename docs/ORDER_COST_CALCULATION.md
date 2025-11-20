# 订单成本计算与预估回款功能

## 功能概述

本功能将商品管理列表中的供货价格、成本价格自动带入到订单列表中，计算每个订单的成本和利润，并统计每日预估回款金额。

## 功能特性

### 1. 订单成本计算
- **自动匹配**：通过 SKU 货号、产品 ID 或 SPU ID 自动匹配商品
- **历史成本**：支持根据订单时间获取对应时期的历史成本价
- **批量计算**：一键批量计算所有订单的成本和利润
- **增量更新**：只计算未计算成本的订单，避免重复计算

### 2. 商品匹配优先级
1. **productSkuId** (product_id) - 最高优先级
2. **extCode** (SKU货号) - 次优先级  
3. **spu_id** - 备用匹配

### 3. 每日预估回款统计
- **按日聚合**：统计每日的订单量、销售额、成本和利润
- **可视化图表**：折线图展示每日趋势
- **明细表格**：详细的每日数据列表
- **汇总统计**：总订单数、总销售额、总成本、总利润

## 使用方法

### 前端操作

1. **进入财务管理页面**
   - 点击左侧菜单 "财务管理"
   - 切换到 "预估回款" 标签页

2. **计算订单成本**
   - 点击 "计算订单成本" 按钮
   - 系统自动匹配商品并计算成本
   - 等待计算完成，查看提示信息

3. **查看预估回款**
   - 汇总统计卡片：总订单数、总销售额、总成本、总利润
   - 折线图：每日销售额、成本、利润趋势
   - 明细表格：每日详细数据

### API 调用

#### 计算订单成本

```bash
POST /api/order-costs/calculate
Content-Type: application/json
Authorization: Bearer {token}

{
  "shop_id": 1,              # 可选，指定店铺ID
  "order_ids": [1, 2, 3],    # 可选，指定订单ID列表
  "force_recalculate": false  # 是否强制重新计算
}
```

**响应示例**：
```json
{
  "total": 100,
  "success": 85,
  "failed": 0,
  "skipped": 15,
  "message": "订单成本计算完成 - 总计: 100, 成功: 85, 失败: 0, 跳过: 15"
}
```

#### 获取每日预估回款

```bash
GET /api/order-costs/daily-forecast?start_date=2024-01-01&end_date=2024-01-31&shop_id=1
Authorization: Bearer {token}
```

**响应示例**：
```json
[
  {
    "date": "2024-01-01",
    "order_count": 25,
    "total_amount": 12500.50,
    "total_cost": 8000.30,
    "total_profit": 4500.20,
    "profit_margin": 36.0
  },
  ...
]
```

## 数据流程

```
1. 订单同步
   ↓
2. 商品同步
   ↓
3. 手动录入商品成本价格
   ↓
4. 点击"计算订单成本"按钮
   ↓
5. 系统匹配商品并计算成本
   ↓
6. 更新订单的 unit_cost, total_cost, profit 字段
   ↓
7. 统计每日预估回款数据
   ↓
8. 前端展示统计结果
```

## 计算逻辑

### 成本计算
- **单位成本** (unit_cost) = 商品的成本价格 (cost_price)
- **总成本** (total_cost) = 单位成本 × 订单数量
- **利润** (profit) = 订单总价 (total_price) - 总成本

### 排除订单
以下订单不参与成本计算和统计：
- 已取消的订单 (CANCELLED)
- 已退款的订单 (REFUNDED)
- 总价为 0 或负数的订单

### 货币转换
所有金额统一转换为 CNY 进行统计：
- USD → CNY: 汇率 7.0
- CNY → CNY: 保持不变

## 注意事项

1. **成本价格录入**
   - 成本价格需要在商品列表中手动录入
   - 支持历史成本记录，可记录不同时期的成本价格

2. **计算时机**
   - 首次使用需要点击"计算订单成本"按钮
   - 新订单同步后，需要重新点击计算按钮
   - 成本价格更新后，可强制重新计算（force_recalculate=true）

3. **数据准确性**
   - 确保商品列表中的成本价格准确
   - 确保订单和商品的 SKU 匹配正确
   - 定期检查计算结果，及时处理未匹配的订单

4. **性能优化**
   - 默认只计算未计算成本的订单
   - 可按店铺或订单ID分批计算
   - 计算结果会缓存，避免重复计算

## 数据库字段

### Order 表
- `unit_cost`: 单位成本 (Numeric)
- `total_cost`: 总成本 (Numeric)
- `profit`: 利润 (Numeric)
- `product_id`: 关联的商品ID (ForeignKey)

### Product 表
- `current_price`: 当前售价 (供货价格，手动录入)
- `sku`: SKU货号
- `product_id`: Temu商品ID
- `spu_id`: SPU ID

### ProductCost 表
- `cost_price`: 成本价格
- `effective_from`: 生效开始时间
- `effective_to`: 生效结束时间
- `notes`: 备注

## 故障排查

### 订单未计算成本
1. 检查商品列表中是否有对应的商品
2. 检查商品是否设置了成本价格
3. 检查订单的 SKU、product_id、spu_id 是否正确
4. 查看后端日志，确认匹配过程

### 统计数据不准确
1. 检查是否有订单未计算成本
2. 检查货币转换是否正确
3. 检查是否排除了已取消和已退款的订单
4. 重新计算订单成本（force_recalculate=true）

### 性能问题
1. 分批计算：指定 shop_id 或 order_ids
2. 增量计算：默认只计算未计算的订单
3. 定期维护：定期检查和清理无效订单

## 相关文件

### 后端
- `backend/app/services/order_cost_service.py` - 订单成本计算服务
- `backend/app/api/order_costs.py` - 订单成本API
- `backend/app/models/order.py` - 订单模型
- `backend/app/models/product.py` - 商品模型

### 前端
- `frontend/src/services/orderCostApi.ts` - 订单成本API服务
- `frontend/src/pages/Finance.tsx` - 财务管理页面

## 更新日志

### v1.0.0 (2024-01-20)
- 实现订单成本自动计算功能
- 实现每日预估回款统计功能
- 支持历史成本价格查询
- 支持货币转换（USD/CNY）
- 实现前端可视化展示

