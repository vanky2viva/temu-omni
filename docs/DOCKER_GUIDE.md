# Docker 使用指南

## 快速开始（本地调试）

### 1. 前置要求

确保已安装：
- Docker Desktop (macOS/Windows) 或 Docker Engine (Linux)
- Docker Compose

验证安装：
```bash
docker --version
docker-compose --version
```

### 2. 配置环境变量

编辑 `.env.docker` 文件，填入您的Temu API密钥：

```bash
# 打开文件
vim .env.docker

# 修改以下内容
TEMU_APP_KEY=your_actual_app_key
TEMU_APP_SECRET=your_actual_app_secret
```

### 3. 启动服务

#### 方法一：使用Makefile（推荐）

```bash
# 启动开发环境（后台运行）
make dev

# 查看日志
make dev-logs

# 初始化数据库
make db-init
```

#### 方法二：使用docker-compose命令

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 初始化数据库
docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 4. 访问服务

服务启动后，访问以下地址：

- **前端界面**: http://localhost:5173
- **后端API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432 (用户名: temu_user, 密码: temu_password)
- **Redis**: localhost:6379

## 服务说明

### 服务列表

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| frontend | temu-omni-frontend | 5173 | React前端应用 |
| backend | temu-omni-backend | 8000 | FastAPI后端服务 |
| postgres | temu-omni-postgres | 5432 | PostgreSQL数据库 |
| redis | temu-omni-redis | 6379 | Redis缓存 |

### 数据持久化

数据存储在Docker卷中，即使停止容器数据也不会丢失：

```bash
# 查看数据卷
docker volume ls | grep temu-omni

# 输出：
# temu-omni_postgres_data
# temu-omni_redis_data
```

## 常用操作

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# 查看最近100行日志
docker-compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend

# 使用Makefile
make dev-restart
```

### 停止服务

```bash
# 停止所有服务（保留数据）
docker-compose down

# 停止并删除数据卷（清空所有数据）
docker-compose down -v

# 使用Makefile
make dev-down
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U temu_user -d temu_omni

# 进入Redis容器
docker-compose exec redis redis-cli
```

### 代码热更新

开发环境已配置代码热更新：

- **后端**：修改Python代码后自动重载
- **前端**：修改React代码后自动刷新浏览器

代码通过volume挂载，无需重启容器。

## 数据库管理

### 初始化数据库

```bash
# 方式一：使用Makefile
make db-init

# 方式二：手动执行
docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 备份数据库

```bash
# 方式一：使用Makefile
make db-backup

# 方式二：手动备份
docker-compose exec postgres pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
# 从备份文件恢复
cat backup_20240101.sql | docker-compose exec -T postgres psql -U temu_user -d temu_omni
```

### 连接数据库

```bash
# 使用docker-compose
docker-compose exec postgres psql -U temu_user -d temu_omni

# 使用本地客户端
psql -h localhost -p 5432 -U temu_user -d temu_omni
```

## 调试技巧

### 查看容器状态

```bash
# 查看所有容器
docker-compose ps

# 查看容器详细信息
docker-compose ps -a
```

### 查看资源使用

```bash
# 查看实时资源使用
docker stats

# 查看特定容器
docker stats temu-omni-backend
```

### 重新构建镜像

```bash
# 重新构建所有服务
docker-compose build

# 重新构建特定服务
docker-compose build backend
docker-compose build frontend

# 强制重新构建（不使用缓存）
docker-compose build --no-cache
```

### 清理Docker资源

```bash
# 清理未使用的镜像
docker image prune

# 清理未使用的容器
docker container prune

# 清理未使用的数据卷
docker volume prune

# 一键清理所有未使用资源
docker system prune -a
```

## 生产环境部署

### 构建生产镜像

```bash
# 使用Makefile
make prod-build

# 或使用docker-compose
docker-compose -f docker-compose.prod.yml build
```

### 启动生产环境

```bash
# 配置生产环境变量
cp .env.docker .env.prod
vim .env.prod  # 修改为生产环境配置

# 启动生产环境
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 使用Makefile
make prod-up
```

### 生产环境注意事项

1. **修改数据库密码**：不要使用默认密码
2. **设置强密钥**：修改 `SECRET_KEY` 为随机字符串
3. **配置CORS**：修改 `CORS_ORIGINS` 为实际域名
4. **启用HTTPS**：配置SSL证书
5. **监控日志**：设置日志收集和监控

## 故障排查

### 前端无法访问后端

检查网络配置：
```bash
# 查看网络
docker network ls

# 检查容器网络连接
docker network inspect temu-omni_temu-network
```

### 数据库连接失败

```bash
# 检查数据库是否就绪
docker-compose exec postgres pg_isready -U temu_user

# 查看数据库日志
docker-compose logs postgres
```

### 端口被占用

```bash
# 查看端口占用
lsof -i :5173
lsof -i :8000
lsof -i :5432

# 修改端口（编辑docker-compose.yml）
```

### 容器启动失败

```bash
# 查看容器日志
docker-compose logs backend

# 检查配置文件
docker-compose config

# 验证环境变量
docker-compose exec backend env
```

## 性能优化

### 限制资源使用

编辑 `docker-compose.yml`：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 优化镜像大小

- 使用 `.dockerignore` 排除不必要的文件
- 使用多阶段构建
- 使用Alpine基础镜像

## Makefile命令速查

```bash
make help          # 显示帮助信息
make dev           # 启动开发环境（后台）
make dev-up        # 启动开发环境（前台）
make dev-down      # 停止开发环境
make dev-logs      # 查看日志
make dev-restart   # 重启服务
make db-init       # 初始化数据库
make db-backup     # 备份数据库
make clean         # 清理所有容器和数据
make prod-build    # 构建生产镜像
make prod-up       # 启动生产环境
make prod-down     # 停止生产环境
```

## 常见问题

### Q: 如何更新代码？

A: 开发环境使用volume挂载，直接修改代码即可，无需重启容器。

### Q: 如何完全重置环境？

A: 
```bash
make clean
make dev
make db-init
```

### Q: 数据库数据丢失了？

A: 确保使用 `docker-compose down` 而不是 `docker-compose down -v`，后者会删除数据卷。

### Q: 前端修改后不生效？

A: 检查浏览器缓存，或使用无痕模式访问。

### Q: 如何切换到生产模式？

A: 使用 `docker-compose.prod.yml` 配置文件和生产环境Dockerfile。

