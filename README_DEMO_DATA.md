# 📊 演示数据使用指南

## 🎯 什么是演示数据？

演示数据是为了方便您快速体验系统功能而预生成的测试数据，包括：

- **3个演示店铺**：分布在不同地区（美国、英国、德国等）
- **45个商品**：每个店铺15个商品，包含价格和成本
- **450个订单**：每个店铺150个订单，涵盖过去90天
- **15个活动**：各种类型的营销活动

## 🚀 快速开始

### 方法一：使用 Makefile（推荐）

```bash
# 确保服务已启动
make dev

# 生成演示数据
make demo-data
```

### 方法二：使用 Docker Compose

```bash
# 确保服务已启动
docker-compose up -d

# 生成演示数据
docker-compose exec backend python scripts/generate_demo_data.py
```

### 方法三：在容器内运行

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行脚本
./scripts/run_demo.sh
```

### 方法四：本地环境

```bash
# 进入backend目录
cd backend

# 激活虚拟环境
source venv/bin/activate

# 运行脚本
python scripts/generate_demo_data.py
```

## 📋 演示数据内容

### 店铺信息

| 店铺名称 | 地区 | 商品数 | 订单数 | 状态 |
|---------|------|--------|--------|------|
| 演示店铺1 (US) | 美国 | 15 | 150 | 已配置API |
| 演示店铺2 (UK) | 英国 | 15 | 150 | 已配置API |
| 演示店铺3 (DE) | 德国 | 15 | 150 | 已配置API |

### 数据特点

#### 商品
- 涵盖多个品类：电子产品、配件、运动用品、生活用品
- 价格范围：$5 - $100
- 成本利润率：30% - 60%
- 包含库存信息
- 75%的商品在售，25%已下架

#### 订单
- 时间跨度：最近90天
- 订单状态分布：
  - 已完成：40%
  - 已送达：20%
  - 已发货：15%
  - 已支付：10%
  - 待支付：5%
  - 已取消/已退款：各5%
- 每个订单包含完整的价格、成本、利润数据

#### 活动
- 包含多种类型：促销、折扣、限时抢购等
- 有过去的活动（已结束）
- 有进行中的活动
- 有未来的活动（即将开始）

## 🎨 体验功能

生成演示数据后，您可以：

### 1. 查看仪表板
访问 http://localhost:5173/dashboard

- 📈 查看总订单量、GMV、利润等核心指标
- 📊 查看销售趋势图表
- 🏪 查看店铺对比数据

### 2. 店铺管理
访问 http://localhost:5173/shops

- 查看多个店铺信息
- 为每个店铺配置独立的API密钥
- 查看API配置状态

### 3. 订单管理
访问 http://localhost:5173/orders

- 浏览450个订单
- 按店铺、状态、时间筛选
- 查看订单的价格、成本、利润

### 4. 商品管理
访问 http://localhost:5173/products

- 查看所有商品
- 为商品录入成本
- 查看成本历史

### 5. 数据统计
访问 http://localhost:5173/statistics

- 切换每日/每周/每月视图
- 按店铺筛选数据
- 查看销量趋势和增长率

## 🔄 重新生成数据

如果您想清除现有数据并重新生成：

```bash
# 方法一：使用Makefile
make demo-data

# 方法二：使用Docker Compose
docker-compose exec backend python scripts/generate_demo_data.py
```

脚本会自动清除旧的演示数据（所有 `DEMO_` 开头的店铺及其关联数据），然后生成新的演示数据。

## ⚠️ 注意事项

### 演示数据标识
- 所有演示店铺的 `shop_id` 以 `DEMO_` 开头
- 删除脚本只会清理演示数据，不会影响您的真实数据

### API密钥
- 演示店铺会自动配置模拟的API密钥（`demo_app_key_*`）
- 这些密钥**不是真实的**，无法用于实际的Temu API调用
- 如需测试真实API，请：
  1. 创建新店铺（非演示店铺）
  2. 在店铺管理中配置真实的API密钥
  3. 使用同步功能获取真实数据

### 数据量
- 默认生成450个订单，可以在脚本中调整
- 如果觉得数据太多或太少，编辑 `generate_demo_data.py`:
  ```python
  # 修改这些参数
  shops = generate_shops(db, count=3)          # 店铺数量
  products = generate_products(db, shops, products_per_shop=15)  # 每店铺商品数
  orders = generate_orders(db, shops, products, orders_per_shop=150)  # 每店铺订单数
  ```

## 🧹 清理演示数据

### 只删除演示数据

```bash
# 使用Python脚本（推荐）
docker-compose exec backend python -c "
from scripts.generate_demo_data import clear_demo_data
from app.core.database import SessionLocal
db = SessionLocal()
clear_demo_data(db)
db.close()
print('演示数据已清除')
"
```

### 清除所有数据（重置系统）

```bash
# 停止服务并删除所有数据
make clean

# 重新启动
make dev
make db-init

# 重新生成演示数据
make demo-data
```

## 💡 最佳实践

### 初次使用
1. 先生成演示数据熟悉系统
2. 了解各个功能模块
3. 测试数据筛选和统计

### 正式使用
1. 清除或保留演示数据
2. 添加真实店铺
3. 配置真实的API密钥
4. 开始同步真实数据

### 演示展示
1. 使用演示数据进行功能演示
2. 展示各种数据可视化图表
3. 演示后可快速重置

## 📈 数据示例

生成完成后，您会看到类似这样的摘要：

```
==========================================
演示数据生成完成！
==========================================

📊 数据统计:
  • 店铺数量: 3
  • 商品数量: 45
  • 订单数量: 450

💰 财务数据:
  • 总GMV: $25,843.50
  • 总利润: $13,921.47
  • 利润率: 53.87%

🏪 店铺列表:
  • 演示店铺1 (US): 150个订单, GMV $8,614.50
  • 演示店铺2 (UK): 150个订单, GMV $8,614.50
  • 演示店铺3 (DE): 150个订单, GMV $8,614.50

✅ 现在可以访问系统查看演示数据了！
```

## 🆘 常见问题

### Q: 生成数据失败？
A: 确保数据库已初始化：`make db-init`

### Q: 如何修改生成的数据量？
A: 编辑 `backend/scripts/generate_demo_data.py` 中的参数

### Q: 演示数据会影响真实数据吗？
A: 不会。演示数据有特殊标识，删除时只会清除演示数据

### Q: 可以自定义演示数据吗？
A: 可以。修改 `generate_demo_data.py` 脚本，自定义商品名称、价格范围等

### Q: 如何只保留部分演示数据？
A: 在界面中手动删除不需要的店铺即可

---

## 🎊 开始体验

现在运行 `make demo-data`，立即体验完整的系统功能！

