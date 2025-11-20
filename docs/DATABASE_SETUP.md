# 数据库设置说明

## 统一使用 PostgreSQL

**重要**：项目统一使用 PostgreSQL 数据库，不再支持 SQLite，以避免数据库指向错误的问题。

## 数据库配置

### 本地开发环境

1. **启动 PostgreSQL 服务**

   如果使用 Docker Compose：
   ```bash
   docker-compose up -d postgres
   ```

   或者使用本地 PostgreSQL 服务：
   ```bash
   # macOS
   brew services start postgresql@13
   
   # Linux
   sudo systemctl start postgresql
   ```

2. **配置数据库连接**

   在 `backend/.env` 文件中设置：
   ```env
   DATABASE_URL=postgresql://temu_user:temu_password@localhost:5432/temu_omni
   ```

   Docker Compose 默认配置：
   - 数据库名: `temu_omni`
   - 用户名: `temu_user`
   - 密码: `temu_password`
   - 端口: `5432`

3. **初始化数据库**

   运行初始化脚本：
   ```bash
   cd backend
   python3 scripts/init_postgres_with_cn_fields.py
   ```

   这个脚本会：
   - 创建所有表结构
   - 添加 CN 相关字段（如果不存在）
   - 设置 CN 字段的默认值
   - 初始化默认管理员用户

### 生产环境

1. **创建数据库**

   ```sql
   CREATE DATABASE temu_omni;
   CREATE USER temu_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE temu_omni TO temu_user;
   ```

2. **配置环境变量**

   在生产环境的 `.env` 文件中设置：
   ```env
   DATABASE_URL=postgresql://temu_user:your_secure_password@your_db_host:5432/temu_omni
   ```

3. **运行迁移**

   ```bash
   cd backend
   python3 scripts/init_postgres_with_cn_fields.py
   ```

## 数据库字段说明

### shops 表 CN 字段

| 字段名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `cn_access_token` | TEXT | CN 区域访问令牌 | NULL |
| `cn_app_key` | VARCHAR(200) | CN 区域 App Key | `af5bcf5d4bd5a492fa09c2ee302d75b9` |
| `cn_app_secret` | TEXT | CN 区域 App Secret | `e4f229bb9c4db21daa999e73c8683d42ba0a7094` |
| `cn_api_base_url` | VARCHAR(200) | CN 区域 API 基础 URL | `https://openapi.kuajingmaihuo.com/openapi/router` |

## 迁移脚本

### 添加 CN 字段

如果数据库已经存在但缺少 CN 字段，可以运行：

```bash
cd backend
python3 scripts/add_cn_fields_to_postgres.py
```

或者使用 SQL 脚本：

```bash
psql -U temu_user -d temu_omni -f backend/scripts/add_cn_fields.sql
```

### 重建数据库

如果需要完全重建数据库（**会删除所有数据**）：

```bash
cd backend
python3 scripts/recreate_database.py
```

## 验证数据库连接

测试数据库连接和表结构：

```bash
cd backend
python3 -c "
from app.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('数据库表:', tables)
columns = inspector.get_columns('shops')
print('shops 表字段数:', len(columns))
"
```

## 常见问题

### Q: 如何切换到 PostgreSQL？

A: 更新 `backend/.env` 文件中的 `DATABASE_URL`，然后运行初始化脚本。

### Q: 数据库连接失败怎么办？

A: 
1. 检查 PostgreSQL 服务是否运行
2. 检查连接字符串是否正确
3. 检查数据库用户权限
4. 检查防火墙设置

### Q: 如何备份数据库？

A:
```bash
pg_dump -U temu_user -d temu_omni > backup.sql
```

### Q: 如何恢复数据库？

A:
```bash
psql -U temu_user -d temu_omni < backup.sql
```

## 相关文件

- 数据库配置: `backend/app/core/database.py`
- 环境变量模板: `backend/env.template`
- 初始化脚本: `backend/scripts/init_postgres_with_cn_fields.py`
- 添加字段脚本: `backend/scripts/add_cn_fields_to_postgres.py`
- SQL 脚本: `backend/scripts/add_cn_fields.sql`

