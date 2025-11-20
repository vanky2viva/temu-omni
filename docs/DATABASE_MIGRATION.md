# 数据库迁移指南：从 SQLite 到 PostgreSQL

## 概述

项目已统一使用 PostgreSQL 数据库，不再支持 SQLite。如果之前使用 SQLite，需要迁移到 PostgreSQL。

## 迁移步骤

### 1. 备份 SQLite 数据（可选）

如果需要保留现有数据：

```bash
cd backend
sqlite3 temu_omni.db .dump > sqlite_backup.sql
```

### 2. 启动 PostgreSQL

```bash
# 使用 Docker Compose
docker-compose up -d postgres

# 或使用本地 PostgreSQL 服务
brew services start postgresql@13  # macOS
sudo systemctl start postgresql    # Linux
```

### 3. 更新配置文件

编辑 `backend/.env` 文件，将 `DATABASE_URL` 改为：

```env
DATABASE_URL=postgresql://temu_user:temu_password@localhost:5432/temu_omni
```

### 4. 初始化 PostgreSQL 数据库

```bash
cd backend
python3 scripts/init_postgres_with_cn_fields.py
```

这个脚本会：
- 创建所有表结构
- 添加 CN 相关字段
- 设置默认值
- 初始化默认用户

### 5. 导入数据（如果有备份）

如果之前有 SQLite 数据需要迁移，可以使用数据导入脚本或手动导入。

### 6. 重启后端服务

```bash
# 如果使用 uvicorn 直接运行
# 停止当前服务（Ctrl+C），然后重新启动
cd backend
uvicorn app.main:app --reload

# 如果使用 Docker Compose
docker-compose restart backend
```

## 验证迁移

1. **检查数据库连接**：
   ```bash
   cd backend
   python3 -c "from app.core.database import engine; print('✅ 数据库连接成功')"
   ```

2. **检查表结构**：
   ```bash
   cd backend
   python3 -c "
   from app.core.database import engine
   from sqlalchemy import inspect
   inspector = inspect(engine)
   columns = inspector.get_columns('shops')
   print(f'shops 表有 {len(columns)} 个字段')
   cn_fields = ['cn_access_token', 'cn_app_key', 'cn_app_secret', 'cn_api_base_url']
   existing = [c['name'] for c in columns]
   missing = [f for f in cn_fields if f not in existing]
   if missing:
       print(f'❌ 缺少字段: {missing}')
   else:
       print('✅ 所有 CN 字段已存在')
   "
   ```

3. **测试 API**：
   - 访问前端页面
   - 检查店铺列表是否能正常加载
   - 检查是否还有 500 错误

## 常见问题

### Q: 迁移后数据丢失了？

A: 如果之前使用 SQLite，数据不会自动迁移。需要手动导出 SQLite 数据并导入到 PostgreSQL。

### Q: 如何确认使用的是 PostgreSQL？

A: 检查 `backend/.env` 文件中的 `DATABASE_URL`，应该以 `postgresql://` 开头。

### Q: PostgreSQL 连接失败？

A: 
1. 检查 PostgreSQL 服务是否运行
2. 检查连接字符串是否正确
3. 检查数据库用户权限
4. 检查端口是否被占用

## 相关文档

- [数据库设置说明](./DATABASE_SETUP.md)
- [CN 端点支持说明](./CN_ENDPOINT_SUPPORT.md)

