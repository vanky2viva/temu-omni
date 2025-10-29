# Docker 快速启动指南

## 🚀 三步启动

### 1️⃣ 配置环境变量

```bash
# 复制环境变量模板
cp env.docker.template .env.docker

# 编辑文件，填入您的Temu API密钥
vim .env.docker
```

需要修改的内容：
```bash
TEMU_APP_KEY=your_actual_app_key        # 改为您的实际App Key
TEMU_APP_SECRET=your_actual_app_secret  # 改为您的实际App Secret
```

### 2️⃣ 启动服务

```bash
# 方式一：使用 Makefile（推荐）
make dev

# 方式二：使用 docker-compose
docker-compose up -d
```

### 3️⃣ 初始化数据库

```bash
# 方式一：使用 Makefile
make db-init

# 方式二：使用 docker-compose
docker-compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## ✅ 访问服务

- 🌐 **前端界面**: http://localhost:5173
- 📡 **后端API**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs
- 🗄️ **数据库**: localhost:5432 (用户名: temu_user, 密码: temu_password)

## 📋 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
make dev-logs
# 或
docker-compose logs -f

# 重启服务
make dev-restart

# 停止服务
make dev-down

# 完全清理（包括数据）
make clean
```

## 🔧 本地调试

### 代码热更新
- **后端**：修改 Python 代码会自动重载
- **前端**：修改 React 代码会自动刷新浏览器

### 查看实时日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 只看后端日志
docker-compose logs -f backend

# 只看前端日志
docker-compose logs -f frontend
```

### 进入容器调试
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库
docker-compose exec postgres psql -U temu_user -d temu_omni

# 进入Redis
docker-compose exec redis redis-cli
```

## 🐛 常见问题

### 端口已被占用
```bash
# 查看端口占用
lsof -i :5173  # 前端端口
lsof -i :8000  # 后端端口

# 停止占用端口的进程或修改 docker-compose.yml 中的端口映射
```

### 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U temu_user

# 查看数据库日志
docker-compose logs postgres
```

### 前端访问后端失败
检查 CORS 配置是否包含了 http://localhost:5173

### 完全重置环境
```bash
# 停止并删除所有容器和数据
make clean

# 重新启动
make dev
make db-init
```

## 📖 详细文档

完整的Docker使用文档请查看：[docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)

## 🎯 Makefile 命令速查

| 命令 | 说明 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make dev` | 启动开发环境（后台） |
| `make dev-up` | 启动开发环境（前台） |
| `make dev-down` | 停止开发环境 |
| `make dev-logs` | 查看日志 |
| `make dev-restart` | 重启服务 |
| `make db-init` | 初始化数据库 |
| `make db-backup` | 备份数据库 |
| `make clean` | 清理所有容器和数据 |

## 🎊 开始使用

启动成功后：
1. 访问 http://localhost:5173
2. 在"店铺管理"中添加您的Temu店铺
3. 开始同步和分析数据！

