# Excel导入功能部署指南

## 快速部署步骤

### 1. 上传文件到服务器

将以下文件上传到服务器 `/root/temu-Omni` 目录：

```bash
scp 数据库迁移_导入历史表.sql root@your-server:/root/temu-Omni/
```

### 2. 执行数据库迁移

```bash
# SSH连接到服务器
ssh root@your-server

# 进入项目目录
cd /root/temu-Omni

# 执行数据库迁移
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d temu_omni < 数据库迁移_导入历史表.sql

# 验证表是否创建成功
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d temu_omni -c "\dt import_history"
```

预期输出：
```
             List of relations
 Schema |      Name       | Type  |  Owner   
--------+-----------------+-------+----------
 public | import_history  | table | postgres
```

### 3. 更新代码并重启服务

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动服务
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# 检查服务状态
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

### 4. 验证功能

1. 访问店铺管理页面：`https://your-domain.com/shops`
2. 找到任意店铺，点击「导入」按钮
3. 应该能看到导入数据的对话框
4. 尝试上传一个Excel文件测试导入功能

## 涉及的文件清单

### 后端文件

1. **模型文件**
   - `backend/app/models/import_history.py` - 导入历史记录模型
   - `backend/app/models/shop.py` - 更新Shop模型关联关系

2. **服务文件**
   - `backend/app/services/excel_import_service.py` - Excel导入服务

3. **API文件**
   - `backend/app/api/import_data.py` - 数据导入API接口
   - `backend/app/main.py` - 注册路由

### 前端文件

1. **组件文件**
   - `frontend/src/components/ImportDataModal.tsx` - 导入数据模态框组件

2. **页面文件**
   - `frontend/src/pages/ShopList.tsx` - 店铺列表页面（添加导入按钮）

3. **服务文件**
   - `frontend/src/services/api.ts` - 添加导入API调用

### 数据库文件

1. **迁移脚本**
   - `数据库迁移_导入历史表.sql` - 创建import_history表
   - `backend/alembic/versions/add_import_history_table.py` - Alembic迁移脚本（可选）

### 文档文件

1. **用户指南**
   - `Excel导入功能使用指南.md` - 功能使用说明

2. **部署指南**
   - `DEPLOYMENT_IMPORT.md` - 本文件

## 依赖说明

以下Python库已在`requirements.txt`中：
- `pandas==2.1.3` - 用于读取和处理Excel文件
- `openpyxl==3.1.2` - 用于处理.xlsx格式
- `python-multipart==0.0.6` - 用于处理文件上传

无需额外安装依赖。

## 配置说明

### 文件上传目录

文件上传后临时保存在容器的 `/tmp/uploads` 目录，导入完成后自动删除。

如需修改上传目录，编辑 `backend/app/api/import_data.py`：

```python
UPLOAD_DIR = "/tmp/uploads"  # 修改为其他路径
```

### 文件大小限制

当前限制为10MB，如需修改：

1. **前端限制**：编辑 `frontend/src/components/ImportDataModal.tsx`
```typescript
const isLt10M = file.size / 1024 / 1024 < 10  // 修改数字
```

2. **Nginx限制**：编辑 `nginx/conf.d/temu-omni.conf`
```nginx
client_max_body_size 10M;  # 修改大小
```

### 超时时间

当前导入超时为2分钟，如需修改，编辑 `frontend/src/services/api.ts`：

```typescript
timeout: 120000  // 毫秒，修改为需要的时间
```

## 故障排查

### 问题1：数据库迁移失败

错误信息：`type "importtype" already exists`

解决方法：
```sql
-- 删除已存在的类型
DROP TYPE IF EXISTS importtype CASCADE;
DROP TYPE IF EXISTS importstatus CASCADE;
DROP TABLE IF EXISTS import_history CASCADE;

-- 重新执行迁移脚本
```

### 问题2：导入按钮未显示

检查步骤：
1. 确认前端代码已更新：`docker compose -f docker-compose.prod.yml logs frontend`
2. 清除浏览器缓存并刷新页面
3. 检查浏览器控制台是否有JavaScript错误

### 问题3：文件上传失败

可能原因：
1. Nginx文件大小限制：检查 `client_max_body_size`
2. 后端容器磁盘空间不足：`docker compose -f docker-compose.prod.yml exec backend df -h`
3. 文件权限问题：确保 `/tmp/uploads` 目录可写

### 问题4：导入过程中出错

查看详细日志：
```bash
# 后端日志
docker compose -f docker-compose.prod.yml logs -f backend | grep -i "import"

# 数据库日志
docker compose -f docker-compose.prod.yml logs -f postgres
```

## 回滚方案

如果导入功能出现问题，需要回滚：

### 1. 删除import_history表

```sql
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d temu_omni -c "
DROP TABLE IF EXISTS import_history CASCADE;
DROP TYPE IF EXISTS importtype CASCADE;
DROP TYPE IF EXISTS importstatus CASCADE;
"
```

### 2. 回滚代码

```bash
# 检出之前的提交
git checkout <previous-commit-hash>

# 重新构建
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. 移除导入按钮

如果只想临时隐藏功能，可以在前端注释掉导入按钮：

编辑 `frontend/src/pages/ShopList.tsx`，注释掉导入按钮相关代码。

## 测试清单

部署后请验证以下功能：

- [ ] 店铺列表页面正常显示
- [ ] 导入按钮可以点击
- [ ] 导入对话框正常弹出
- [ ] 可以选择活动数据/商品数据标签页
- [ ] 可以上传Excel文件
- [ ] 文件大小和格式验证正常
- [ ] 点击「开始导入」后显示加载状态
- [ ] 导入成功后显示统计信息
- [ ] 导入的数据在相应页面正确显示
- [ ] 重复导入时跳过已存在的数据
- [ ] 导入历史记录正确保存到数据库

## 性能监控

建议监控以下指标：

1. **导入时间**
   - 小文件（<100行）：< 10秒
   - 中等文件（100-500行）：< 30秒
   - 大文件（500-1000行）：< 60秒

2. **数据库性能**
   ```sql
   -- 查看导入历史表大小
   SELECT pg_size_pretty(pg_total_relation_size('import_history'));
   
   -- 查看索引使用情况
   SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public' AND relname = 'import_history';
   ```

3. **磁盘使用**
   ```bash
   # 检查 /tmp 目录使用情况
   docker compose -f docker-compose.prod.yml exec backend du -sh /tmp/uploads
   ```

## 后续优化建议

1. **异步处理**：对于大文件导入，考虑使用Celery等异步任务队列

2. **进度显示**：实现实时进度条，显示导入进度

3. **批量操作**：支持一次性上传多个文件

4. **导入模板**：提供Excel模板下载，方便用户准备数据

5. **数据预览**：导入前显示数据预览，让用户确认

6. **更多数据类型**：支持订单物流信息等其他数据导入

## 联系支持

如有问题，请检查：
1. 本文档的「故障排查」部分
2. 系统日志：`docker compose -f docker-compose.prod.yml logs`
3. 项目文档：`docs/` 目录下的其他文档

