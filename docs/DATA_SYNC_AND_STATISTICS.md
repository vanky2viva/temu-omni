# 数据同步与统计功能说明

## 概述

系统通过 Temu API 同步订单和商品数据到数据库，并提供丰富的统计分析功能。

## 数据同步流程

### 1. 订单同步

#### 同步方式
- **全量同步**：首次同步或手动触发全量同步时，会同步指定时间范围内的所有订单（默认1年）
- **增量同步**：基于 `last_sync_at` 时间戳，只同步新增或更新的订单（默认7天）

#### 同步的数据字段

| 字段 | 来源 | 说明 |
|------|------|------|
| `order_sn` | `orderList[].orderSn` | 子订单号 |
| `parent_order_sn` | `parentOrderMap.parentOrderSn` | 父订单号 |
| `product_name` | `orderList[].goodsName` | 商品名称 |
| `product_sku` | `orderList[].spec` | SKU规格 |
| `quantity` | `orderList[].quantity` | 购买数量 |
| `unit_price` | `orderList[].goodsPrice` | 单价（当前为0，需通过金额查询API获取） |
| `total_price` | `orderList[].goodsTotalPrice` | 总价（当前为0，需通过金额查询API获取） |
| `status` | `orderList[].orderStatus` | 订单状态 |
| `order_time` | `parentOrderMap.parentOrderTime` | 下单时间（已转换为北京时间） |
| `payment_time` | `parentOrderMap.paymentTime` | 支付时间（已转换为北京时间） |
| `shipping_time` | `parentOrderMap.parentShippingTime` | 发货时间（已转换为北京时间） |
| `expect_ship_latest_time` | `parentOrderMap.expectShipLatestTime` | 预期最晚发货时间（已转换为北京时间） |
| `delivery_time` | `parentOrderMap.updateTime`（已收货）或 `latestDeliveryTime` | 签收时间（已转换为北京时间） |

#### 时间字段处理

**时区转换**：
- API 返回的时间戳是 UTC 时间（秒级时间戳）
- 系统自动将所有时间戳转换为北京时间（UTC+8）
- 存储到数据库的时间已经是北京时间（naive datetime）

**签收时间逻辑**：
- 当订单状态为已收货（`parentOrderStatus = 5`）时，使用 `updateTime` 作为签收时间（更准确）
- 当订单状态不是已收货时，使用 `latestDeliveryTime` 作为最晚送达时间

### 2. 商品同步

#### 同步方式
- **全量同步**：同步所有商品数据
- **增量同步**：基于 `last_sync_at` 时间戳，只同步新增或更新的商品

#### 支持两种端点

1. **CN 端点**（`bg.goods.list.get`）
   - 使用 CN 区域的 `app_key`、`app_secret` 和 `access_token`
   - 不需要通过代理服务器
   - 用于商品列表、发品、库存、备货履约等操作

2. **标准端点**（`bg.local.goods.list.query`）
   - 使用标准区域的 `app_key`、`app_secret` 和 `access_token`
   - 需要通过代理服务器
   - 用于其他区域的商品查询

### 3. 同步触发方式

#### 前端触发
- 在店铺列表页面，点击"Sync"按钮
- 会同步该店铺的订单、商品和分类数据
- 显示实时同步进度和结果统计

#### API 触发
- `POST /api/sync/shops/{shop_id}/all` - 同步指定店铺的所有数据
- `POST /api/sync/shops/{shop_id}/orders` - 同步指定店铺的订单
- `POST /api/sync/shops/{shop_id}/products` - 同步指定店铺的商品

## 统计功能

### 1. 订单统计

#### 总览统计
- **订单总数**：按订单号去重统计
- **GMV**：订单总金额之和
- **总成本**：订单成本之和
- **总利润**：订单利润之和
- **平均订单价值**：GMV / 订单数
- **利润率**：利润 / GMV × 100%

**API**: `GET /api/statistics/overview/`

#### 每日统计
- 按日期分组统计订单数、GMV、成本、利润
- 支持指定日期范围

**API**: `GET /api/statistics/daily/`

#### 每周/每月统计
- 按周或月分组统计
- 支持指定周期数量

**API**: 
- `GET /api/statistics/weekly/`
- `GET /api/statistics/monthly/`

### 2. 销量统计

#### SKU 销量排行
- 按 SKU 分组统计销量（quantity 之和）
- 显示订单数、GMV、利润
- 支持按销量排序

**API**: `GET /api/analytics/sku-sales`

#### 销量趋势
- 每日销量趋势
- 7日移动平均
- 增长率计算

**API**: `GET /api/analytics/sales-trend`

### 3. 店铺对比

#### 店铺数据对比
- 按店铺分组统计订单数、GMV、成本、利润
- 计算各店铺的利润率
- 支持多店铺对比

**API**: `GET /api/statistics/shop-comparison`

### 4. GMV 表格

#### 按周期统计 GMV
- 支持按天/周/月统计
- 显示订单数、GMV、成本、利润、利润率
- 支持指定周期数量

**API**: `GET /api/analytics/gmv-table`

## 数据使用场景

### 1. 销量分析
- 查看各 SKU 的销量排行
- 分析热销商品
- 识别滞销商品

### 2. 财务分析
- 查看 GMV 趋势
- 分析利润情况
- 计算利润率

### 3. 运营分析
- 对比不同店铺的业绩
- 分析订单状态分布
- 监控发货时效（通过 `expect_ship_latest_time`）

### 4. 时间分析
- 分析订单时间分布
- 查看发货时间趋势
- 监控签收时间

## 注意事项

### 1. 订单金额
- 当前订单列表 API 不返回金额信息
- 需要通过 `bg.order.amount.query` API 获取订单金额
- 该 API 需要单独授权，授权后可在同步时调用并更新订单金额

### 2. 数据更新
- 同步时会更新已存在的订单和商品数据
- 基于订单号（`order_sn`）和商品ID（`product_id`）进行匹配
- 如果订单状态或时间发生变化，会自动更新

### 3. 数据去重
- 订单统计时按订单号去重（一个订单号可能对应多条记录，每个订单号为一单）
- GMV、成本、利润按订单记录统计（每个记录都有对应的金额）

### 4. 时区处理
- 所有时间字段都已转换为北京时间（UTC+8）
- 前端显示时无需额外转换
- 统计时使用的时间都是北京时间

## 后续优化

1. **订单金额同步**：授权 `bg.order.amount.query` API 后，在同步时自动获取并更新订单金额
2. **实时同步**：支持 Webhook 事件，实时更新订单状态
3. **数据导出**：支持导出统计数据为 Excel/CSV 格式
4. **自定义报表**：支持用户自定义统计维度和指标
5. **数据可视化**：提供更丰富的图表展示（折线图、柱状图、饼图等）

