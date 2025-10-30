# Excel导入功能使用指南

## 功能概述

由于API申请需要时间，且API数据可能不完整，系统现已支持通过Excel文件手动导入数据。

目前支持导入：
- **活动数据**：从Temu平台导出的「活动商品明细」Excel文件
- **商品数据**：从Temu平台导出的「商品基础信息」Excel文件

## 部署步骤

### 1. 数据库迁移

在生产服务器上执行数据库迁移，创建导入历史记录表：

```bash
# SSH连接到服务器后
cd /root/temu-Omni

# 进入PostgreSQL容器
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d temu_omni

# 执行SQL迁移脚本（在psql命令行中）
\i /path/to/数据库迁移_导入历史表.sql
```

或者直接执行：
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d temu_omni -f 数据库迁移_导入历史表.sql
```

验证表是否创建成功：
```sql
\dt import_history
SELECT * FROM import_history;
```

### 2. 重启服务

```bash
cd /root/temu-Omni
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

## 使用方法

### 1. 进入店铺管理页面

访问：https://temu.your-domain.com/shops

### 2. 点击「导入」按钮

在需要导入数据的店铺行，点击「导入」按钮。

### 3. 选择导入类型

在弹出的对话框中，选择导入类型：
- **活动数据**：导入活动推广相关数据
- **商品数据**：导入或更新商品基础信息

### 4. 上传Excel文件

- 点击上传区域或拖拽文件
- 支持的格式：`.xlsx` 和 `.xls`
- 文件大小限制：10MB

### 5. 开始导入

点击「开始导入」按钮，系统会：
1. 验证文件格式
2. 解析Excel数据
3. 导入到数据库
4. 显示导入结果统计

## 支持的Excel格式

### 活动数据（活动商品明细.xlsx）

必须包含以下列：
- 商品信息
- SPU ID
- 活动站点
- 活动销量
- 活动 GMV
- 活动商品曝光用户数
- 活动商品点击用户数
- 活动商品点击转化率
- 活动商品支付转化率

导入逻辑：
- ✅ 新活动会被创建
- ⏭️ 已存在的活动会被跳过（根据活动名称判断）
- 💰 GMV会作为活动预算和实际成本

### 商品数据（商品基础信息.xlsx）

必须包含以下列：
- 商品名称
- SKU ID
- SPU ID
- 申报价格（格式：999.00元）
- 类目
- 状态
- SKU货号

导入逻辑：
- ✅ 新商品会被创建
- 🔄 已存在的商品会更新价格信息（根据SKU ID判断）
- ⏭️ 无价格信息的商品会被跳过

## 导入结果说明

导入完成后会显示统计信息：

- **总行数**：Excel中的数据行数
- **成功**：成功导入/更新的记录数（绿色）
- **失败**：导入失败的记录数（红色）
- **跳过**：已存在或无需更新的记录数（黄色）

## 导入历史记录

系统会自动记录每次导入的详细信息：
- 导入时间
- 文件名和大小
- 导入统计
- 错误日志（如有）

后续可以通过API查询导入历史：
```
GET /api/import/shops/{shop_id}/history
```

## 注意事项

1. **数据重复处理**
   - 活动：相同名称的活动会被跳过
   - 商品：相同SKU ID的商品会更新价格

2. **文件格式要求**
   - 必须是Excel格式（.xlsx 或 .xls）
   - 列名必须与Temu导出的格式一致
   - 不支持修改列名或列顺序

3. **数据验证**
   - 价格字段会自动处理"元"等单位符号
   - 百分比字段会自动转换为小数（如 1.15% → 0.0115）
   - 空值和非法值会导致该行导入失败

4. **性能建议**
   - 建议单次导入不超过1000行数据
   - 大文件可以分批导入
   - 导入过程中请勿关闭浏览器

## 与API同步的关系

- **Excel导入** 和 **API同步** 可以同时使用
- Excel导入适合临时补充数据
- API同步是长期自动化方案
- 两种方式导入的数据会合并在一起

## 故障排查

### 导入失败：文件格式错误
- 检查文件是否是Excel格式
- 确认列名是否与Temu导出格式一致
- 尝试重新从Temu平台导出文件

### 导入失败：部分数据失败
- 查看导入结果中的错误日志
- 检查失败行的数据格式
- 修正后重新导入

### 导入成功但数据未显示
- 刷新页面
- 检查筛选条件（店铺、时间范围等）
- 查看导入历史记录确认导入状态

## API文档

完整的API文档请参考：`/docs/API.md`

导入相关的API端点：
- `POST /api/import/shops/{shop_id}/activities` - 导入活动数据
- `POST /api/import/shops/{shop_id}/products` - 导入商品数据
- `GET /api/import/shops/{shop_id}/history` - 获取导入历史
- `GET /api/import/shops/{shop_id}/history/{import_id}` - 获取导入详情

