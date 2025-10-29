# ⚡ 快速启动指南

## 🐳 Docker 方式（推荐）

### 第一次使用

```bash
# 1. 配置API密钥
cp env.docker.template .env.docker
vim .env.docker  # 填入 TEMU_APP_KEY 和 TEMU_APP_SECRET

# 2. 一键启动（自动安装依赖、启动服务、初始化数据库）
./start.sh

# 或者使用 Makefile
make dev
make db-init
```

### 日常使用

```bash
# 启动
./start.sh
# 或
make dev

# 停止
./stop.sh
# 或
make dev-down

# 查看日志
make dev-logs
```

### 访问地址

- 🌐 前端：http://localhost:5173
- 📡 API文档：http://localhost:8000/docs
- 🗄️ 数据库：localhost:5432 (temu_user/temu_password)

---

## 💻 本地开发方式

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 .env
cp env.template .env
vim .env

# 启动
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

---

## 📋 常用命令速查

### Docker 命令

| 命令 | 说明 |
|------|------|
| `./start.sh` | 启动所有服务 |
| `./stop.sh` | 停止服务 |
| `make dev` | 后台启动 |
| `make dev-logs` | 查看日志 |
| `make dev-restart` | 重启服务 |
| `make db-backup` | 备份数据库 |
| `make clean` | 完全清理 |

### Docker Compose 原生命令

```bash
docker-compose up -d              # 后台启动
docker-compose down               # 停止服务
docker-compose logs -f            # 查看日志
docker-compose ps                 # 查看状态
docker-compose restart backend    # 重启后端
docker-compose exec backend bash  # 进入后端容器
```

---

## 🔧 调试技巧

### 查看特定服务日志

```bash
docker-compose logs -f backend   # 后端
docker-compose logs -f frontend  # 前端
docker-compose logs -f postgres  # 数据库
```

### 进入容器调试

```bash
# 后端
docker-compose exec backend bash

# 数据库
docker-compose exec postgres psql -U temu_user -d temu_omni

# Redis
docker-compose exec redis redis-cli
```

### 重新构建镜像

```bash
docker-compose build            # 重建所有
docker-compose build backend    # 只重建后端
docker-compose up -d --build    # 重建并启动
```

---

## ❓ 常见问题

### Q: 启动失败？
A: 检查 Docker 是否运行，端口是否被占用（5173, 8000, 5432）

### Q: 数据库连接失败？
A: 等待几秒让数据库启动完成，或查看日志 `docker-compose logs postgres`

### Q: 代码修改不生效？
A: Docker已配置热更新，直接刷新浏览器即可。如果还不行，尝试 `make dev-restart`

### Q: 如何完全重置？
```bash
make clean      # 清空所有数据
make dev        # 重新启动
make db-init    # 初始化数据库
```

### Q: 端口被占用？
```bash
# 查看占用
lsof -i :5173
lsof -i :8000

# 修改端口（编辑 docker-compose.yml）
```

---

## 📚 完整文档

- [README.md](README.md) - 项目总览
- [README_DOCKER.md](README_DOCKER.md) - Docker详细说明
- [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md) - Docker完整指南
- [docs/API.md](docs/API.md) - API文档
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - 部署指南

---

## 🎯 下一步

1. ✅ 启动服务
2. 🔑 在"店铺管理"中添加店铺
3. 📊 同步数据
4. 📈 查看报表

**祝您使用愉快！** 🎉

