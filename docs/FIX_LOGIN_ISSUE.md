# 登录问题修复指南

## 问题症状

- 登录时返回 500 错误
- 浏览器开发者工具显示登录请求失败
- 后端日志显示数据库连接错误

## 常见原因

1. **PostgreSQL 数据库容器未运行**（最常见）
2. **Redis 容器未运行**
3. **数据库表未初始化**
4. **默认用户不存在**

## 快速修复

### 方法1：使用修复脚本（推荐）

```bash
./scripts/fix_login.sh
```

### 方法2：手动修复

#### 1. 启动数据库服务

```bash
docker compose up -d postgres redis
```

等待几秒让服务完全启动。

#### 2. 初始化数据库表（如果需要）

```bash
docker compose exec backend python -c "from app.core.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
```

#### 3. 创建默认用户（如果需要）

```bash
docker compose exec backend python scripts/init_default_user.py
```

#### 4. 验证修复

测试登录API：

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=luffyadmin&password=luffy123!@#"
```

如果返回包含 `access_token` 的JSON响应，说明修复成功。

## 默认登录信息

- **用户名**: `luffyadmin`
- **密码**: `luffy123!@#`

## 检查服务状态

```bash
# 查看所有容器状态
docker compose ps

# 查看后端日志
docker compose logs backend --tail=50

# 查看数据库日志
docker compose logs postgres --tail=50
```

## 预防措施

1. **使用 docker compose 启动所有服务**：
   ```bash
   docker compose up -d
   ```

2. **检查服务依赖**：
   确保 `docker-compose.yml` 中配置了正确的服务依赖关系。

3. **使用健康检查**：
   确保服务完全启动后再进行登录操作。

## 其他可能的问题

### 问题：数据库连接字符串错误

**症状**：后端日志显示 "could not translate host name"

**解决**：检查 `backend/.env` 文件中的 `DATABASE_URL` 配置是否正确。

### 问题：SECRET_KEY 未配置

**症状**：后端启动失败或JWT token生成失败

**解决**：确保 `backend/.env` 文件中配置了 `SECRET_KEY`。

### 问题：CORS 配置错误

**症状**：前端无法访问后端API

**解决**：检查 `backend/.env` 文件中的 `CORS_ORIGINS` 配置，确保包含前端地址。

## 联系支持

如果以上方法都无法解决问题，请：

1. 收集错误日志：
   ```bash
   docker compose logs > logs.txt
   ```

2. 检查服务状态：
   ```bash
   docker compose ps
   docker compose top
   ```

3. 查看系统资源：
   ```bash
   docker stats
   ```

