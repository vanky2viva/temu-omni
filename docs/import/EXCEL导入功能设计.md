# Excel数据导入功能设计

## 📋 需求分析

由于API可能暂时不可用或数据不全，需要支持从Temu平台导出的Excel文件手动导入数据。

### 数据文件类型

1. **订单导出** (`订单导出20251031001.xlsx`)
   - 订单基本信息
   - 商品明细
   - 金额信息
   - 物流信息

2. **商品基础信息** (`商品基础信息.xlsx`)
   - 商品ID、名称
   - 价格、成本
   - 库存信息
   - 分类信息

3. **活动商品明细** (`活动商品明细.xlsx`)
   - 活动信息
   - 参与商品
   - 折扣/优惠信息

## 🎯 功能设计

### 1. 导入入口

**位置**：店铺管理页面 -> 每个店铺的操作栏

**按钮**：
- 📥 导入订单
- 📦 导入商品
- 🎁 导入活动

### 2. 导入流程

```
1. 用户点击导入按钮
   ↓
2. 弹出上传对话框，选择Excel文件
   ↓
3. 文件上传到服务器
   ↓
4. 后端解析Excel，验证数据
   ↓
5. 显示预览（前10条）
   ↓
6. 用户确认后开始导入
   ↓
7. 显示导入进度和结果
```

### 3. 数据映射

#### 订单数据映射
```
Excel字段 → 数据库字段
订单号 → order_sn
下单时间 → order_time
商品名称 → product_name
订单金额 → total_price
订单状态 → status
...
```

#### 商品数据映射
```
Excel字段 → 数据库字段
商品ID → product_id
商品名称 → product_name
售价 → current_price
成本 → cost_price
库存 → stock
...
```

#### 活动数据映射
```
Excel字段 → 数据库字段
活动名称 → activity_name
活动类型 → activity_type
开始时间 → start_time
结束时间 → end_time
...
```

### 4. 数据验证

- ✅ 必填字段检查
- ✅ 数据格式验证（日期、金额等）
- ✅ 重复数据检测
- ✅ 关联数据检查（店铺ID、商品ID等）

### 5. 错误处理

- 📋 显示详细的错误信息
- 💾 记录导入日志
- 🔄 支持部分成功导入
- 📊 提供错误数据下载

## 🛠 技术实现

### 后端API

```python
POST /api/shops/{shop_id}/import/orders
POST /api/shops/{shop_id}/import/products
POST /api/shops/{shop_id}/import/activities
GET /api/shops/{shop_id}/import/history
```

### 前端组件

```typescript
<ImportButton type="orders" shopId={shopId} />
<ImportDialog />
<ImportProgress />
<ImportResult />
```

### 数据库表

```sql
-- 导入历史记录
CREATE TABLE import_history (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER REFERENCES shops(id),
    import_type VARCHAR(20), -- orders/products/activities
    file_name VARCHAR(255),
    total_rows INTEGER,
    success_rows INTEGER,
    failed_rows INTEGER,
    status VARCHAR(20), -- processing/success/failed/partial
    error_log TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 📊 字段对应关系（待确认）

请提供以下信息：

### 订单导出文件
- [ ] 有哪些列？
- [ ] 订单号字段名
- [ ] 时间字段名
- [ ] 金额字段名
- [ ] 状态字段名

### 商品基础信息文件
- [ ] 有哪些列？
- [ ] 商品ID字段名
- [ ] 价格字段名
- [ ] 成本字段名

### 活动商品明细文件
- [ ] 有哪些列？
- [ ] 活动名称字段名
- [ ] 时间字段名

## 🎨 UI设计

### 导入按钮（店铺管理页面）

```
[同步] [导入数据▾] [编辑] [删除]
        ├─ 📥 导入订单
        ├─ 📦 导入商品
        └─ 🎁 导入活动
```

### 导入对话框

```
┌─────────────────────────────────────┐
│  导入订单数据                        │
├─────────────────────────────────────┤
│  1. 选择Excel文件                    │
│  [选择文件] 订单导出20251031001.xlsx│
│                                      │
│  2. 数据预览（前10条）               │
│  ┌───────────────────────────────┐  │
│  │ 订单号  | 时间  | 金额 | 状态 │  │
│  │ ...                            │  │
│  └───────────────────────────────┘  │
│                                      │
│  3. 导入选项                         │
│  □ 跳过重复订单                     │
│  □ 自动创建商品                     │
│                                      │
│  [取消]              [开始导入]     │
└─────────────────────────────────────┘
```

## 🔄 与API同步的区别

| 特性 | API同步 | Excel导入 |
|------|---------|-----------|
| 数据来源 | Temu API | 手动导出 |
| 实时性 | 实时 | 手动更新 |
| 完整性 | 完整 | 可能部分 |
| 使用场景 | 自动化 | 补充/备份 |
| 历史数据 | 最近30天 | 任意时间 |

## ✅ 实现优先级

1. **P0 - 必须**
   - 订单导入
   - 基本验证
   - 错误提示

2. **P1 - 重要**
   - 商品导入
   - 数据预览
   - 导入历史

3. **P2 - 可选**
   - 活动导入
   - 批量导入
   - 模板下载

---

**下一步**：请您打开这三个Excel文件，告诉我：
1. 每个文件有哪些列（列名）？
2. 前3行的示例数据是什么？
3. 哪些字段是必需的？

这样我可以准确地实现字段映射和数据导入功能。

