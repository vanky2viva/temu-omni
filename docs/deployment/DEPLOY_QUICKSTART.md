# 🚀 快速部署到 echofrog.net

## 5分钟快速部署指南

---

## 📦 在服务器上执行以下命令

### 1️⃣ 克隆项目

```bash
cd /opt
sudo git clone <你的仓库地址> temu-Omni
cd temu-Omni
sudo chown -R $USER:$USER .
```

### 2️⃣ 安装 Docker（如未安装）

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

### 3️⃣ 配置环境变量

```bash
# 复制模板
cp env.production.example .env.production

# 编辑配置（重要！）
nano .env.production
```

**必须修改的配置：**
```env
POSTGRES_PASSWORD=你的强密码123
REDIS_PASSWORD=你的强密码456
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 4️⃣ 一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 5️⃣ 初始化沙盒店铺

```bash
docker exec -it temu-omni-backend python scripts/init_sandbox_shop.py
```

---

## ✅ 验证部署

```bash
# 健康检查
curl http://echofrog.net/health

# 访问前端
open http://echofrog.net

# 访问API文档
open http://echofrog.net/docs
```

---

## 🔍 常用命令

```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

---

## 📁 已创建的文件

### 生产环境配置
- ✅ `docker-compose.prod.yml` - 生产环境 Docker Compose 配置
- ✅ `deploy.sh` - 一键部署脚本
- ✅ `env.production.example` - 环境变量模板

### Nginx配置
- ✅ `nginx/nginx.conf` - Nginx主配置
- ✅ `nginx/conf.d/temu-omni.conf` - 站点配置（HTTP/HTTPS）

### Dockerfile
- ✅ `frontend/Dockerfile.prod` - 前端生产镜像
- ✅ `frontend/nginx.conf` - 前端Nginx配置
- ✅ `backend/Dockerfile.prod` - 后端生产镜像

### 文档
- ✅ `DEPLOYMENT_GUIDE.md` - 完整部署指南
- ✅ `DEPLOY_QUICKSTART.md` - 本文档（快速开始）

---

## 🌐 访问地址

部署成功后：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | http://echofrog.net | 主页面 |
| **后端API** | http://echofrog.net/api | API接口 |
| **API文档** | http://echofrog.net/docs | Swagger文档 |
| **ReDoc文档** | http://echofrog.net/redoc | ReDoc文档 |
| **健康检查** | http://echofrog.net/health | 健康状态 |

---

## 🔐 配置 HTTPS（可选）

```bash
# 1. 安装 Certbot
sudo apt install -y certbot

# 2. 停止 Nginx（临时）
docker-compose -f docker-compose.prod.yml stop nginx

# 3. 获取证书
sudo certbot certonly --standalone -d echofrog.net -d www.echofrog.net

# 4. 复制证书
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/echofrog.net/fullchain.pem nginx/ssl/echofrog.net.crt
sudo cp /etc/letsencrypt/live/echofrog.net/privkey.pem nginx/ssl/echofrog.net.key
sudo chown -R $USER:$USER nginx/ssl

# 5. 编辑 nginx/conf.d/temu-omni.conf，启用 HTTPS 部分

# 6. 重启
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 🔄 更新部署

```bash
# 拉取最新代码
git pull

# 重新部署
./deploy.sh
```

---

## 📊 当前架构

```
Internet (80/443)
       ↓
   Nginx (反向代理)
    ↙        ↘
Frontend   Backend API (8000)
            ↙     ↘
      PostgreSQL  Redis
```

---

## ⚡ 性能配置

### 推荐服务器配置
- **开发/测试**: 2核 2GB内存
- **小型生产**: 2核 4GB内存
- **中型生产**: 4核 8GB内存
- **大型生产**: 8核 16GB内存

### Docker资源限制

可在 `docker-compose.prod.yml` 中添加：

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

---

## 🐛 问题排查

### 端口被占用
```bash
# 查看80端口占用
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# 停止占用进程
sudo kill -9 <PID>
```

### 容器启动失败
```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
```

### 数据库连接失败
```bash
# 检查数据库状态
docker exec temu-omni-postgres psql -U temu_user -d temu_omni -c "SELECT 1;"
```

---

## 📞 获取帮助

- 完整文档: `DEPLOYMENT_GUIDE.md`
- API文档: http://echofrog.net/docs
- 项目仓库: GitHub

---

**现在你可以将项目同步到服务器并执行 `./deploy.sh` 开始部署！** 🎉

