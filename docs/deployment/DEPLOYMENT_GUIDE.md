# 🚀 Temu-Omni 生产环境部署指南

## 部署到 echofrog.net

---

## 📋 前置准备

### 1. 服务器要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 至少 2GB RAM（推荐 4GB+）
- **磁盘**: 至少 20GB 可用空间
- **CPU**: 2核心+

### 2. 安装必要软件

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git

# CentOS/RHEL
sudo yum install -y docker docker-compose git

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
```

### 3. 域名配置

确保域名 `echofrog.net` 已正确解析到服务器IP：

```bash
# 检查DNS解析
nslookup echofrog.net
# 或
dig echofrog.net
```

### 4. 防火墙配置

```bash
# 开放80和443端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# 或使用 iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

---

## 📦 部署步骤

### 步骤 1: 克隆项目到服务器

```bash
cd /opt
sudo git clone https://github.com/your-username/temu-Omni.git
cd temu-Omni
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp env.production.example .env.production

# 编辑配置文件
nano .env.production
```

**重要配置项：**

```env
# 修改数据库密码
POSTGRES_PASSWORD=强密码123456

# 修改Redis密码
REDIS_PASSWORD=强密码123456

# 生成并设置SECRET_KEY（必须是随机的）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Temu API凭据（使用沙盒或生产凭据）
TEMU_APP_KEY=你的APP_KEY
TEMU_APP_SECRET=你的APP_SECRET
TEMU_ACCESS_TOKEN=你的ACCESS_TOKEN
```

### 步骤 3: 一键部署

```bash
# 给部署脚本添加执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

### 步骤 4: 初始化数据库

部署成功后，需要初始化沙盒店铺：

```bash
# 进入后端容器
docker exec -it temu-omni-backend bash

# 运行初始化脚本
python scripts/init_sandbox_shop.py

# 退出容器
exit
```

---

## 🔍 验证部署

### 1. 检查服务状态

```bash
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 应该看到5个运行中的容器：
# - temu-omni-postgres
# - temu-omni-redis
# - temu-omni-backend
# - temu-omni-frontend
# - temu-omni-nginx
```

### 2. 测试访问

```bash
# 健康检查
curl http://echofrog.net/health

# API测试
curl http://echofrog.net/api/shops/

# 访问前端（在浏览器中打开）
open http://echofrog.net
```

### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

---

## 🔐 配置 HTTPS（可选但推荐）

### 使用 Let's Encrypt 免费证书

```bash
# 1. 安装 Certbot
sudo apt install -y certbot

# 2. 获取证书
sudo certbot certonly --standalone -d echofrog.net -d www.echofrog.net

# 3. 复制证书到项目目录
sudo cp /etc/letsencrypt/live/echofrog.net/fullchain.pem nginx/ssl/echofrog.net.crt
sudo cp /etc/letsencrypt/live/echofrog.net/privkey.pem nginx/ssl/echofrog.net.key
sudo chown $USER:$USER nginx/ssl/*

# 4. 编辑 Nginx 配置，启用 HTTPS
nano nginx/conf.d/temu-omni.conf

# 取消 HTTPS server 块的注释，并注释掉 HTTP 的 return 301

# 5. 重启 Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 自动续期证书

```bash
# 添加定时任务
sudo crontab -e

# 添加以下行（每天凌晨2点检查并续期）
0 2 * * * certbot renew --quiet && docker-compose -f /opt/temu-Omni/docker-compose.prod.yml restart nginx
```

---

## 🔄 数据同步

### 手动同步

```bash
# 通过API触发同步
curl -X POST http://echofrog.net/api/sync/shops/12/all
```

### 自动同步

在 `.env.production` 中配置：
```env
AUTO_SYNC_ENABLED=true
SYNC_INTERVAL_MINUTES=30
```

---

## 🛠️ 常用维护命令

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新部署
./deploy.sh
```

### 备份数据库

```bash
# 备份数据库
docker exec temu-omni-postgres pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i temu-omni-postgres psql -U temu_user temu_omni < backup_20251030.sql
```

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h
du -sh /var/lib/docker
```

### 清理无用数据

```bash
# 清理Docker缓存
docker system prune -a

# 清理旧的镜像
docker image prune -a
```

---

## 📊 性能优化

### 1. 数据库优化

编辑 `docker-compose.prod.yml`，添加 PostgreSQL 优化参数：

```yaml
postgres:
  command: 
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
    - "-c"
    - "maintenance_work_mem=64MB"
    - "-c"
    - "checkpoint_completion_target=0.9"
    - "-c"
    - "wal_buffers=16MB"
```

### 2. Redis 优化

```yaml
redis:
  command: 
    - "redis-server"
    - "--maxmemory"
    - "256mb"
    - "--maxmemory-policy"
    - "allkeys-lru"
```

### 3. 后端工作进程

根据CPU核心数调整：

```yaml
backend:
  environment:
    - WORKERS=4  # 推荐: CPU核心数 * 2 + 1
```

---

## 🐛 故障排查

### 问题 1: 无法访问网站

```bash
# 检查Nginx是否运行
docker-compose -f docker-compose.prod.yml ps nginx

# 检查端口占用
sudo netstat -tlnp | grep :80

# 检查防火墙
sudo ufw status
```

### 问题 2: API返回500错误

```bash
# 查看后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查数据库连接
docker exec temu-omni-backend python -c "from app.core.database import engine; print(engine.url)"
```

### 问题 3: 数据库连接失败

```bash
# 检查PostgreSQL状态
docker-compose -f docker-compose.prod.yml ps postgres

# 测试数据库连接
docker exec temu-omni-postgres psql -U temu_user -d temu_omni -c "SELECT 1;"
```

---

## 📞 技术支持

- **项目文档**: `/docs`
- **API文档**: `http://echofrog.net/docs`
- **问题反馈**: GitHub Issues

---

## ✅ 部署检查清单

- [ ] 服务器满足最低配置要求
- [ ] Docker 和 Docker Compose 已安装
- [ ] 域名 DNS 已正确配置
- [ ] 防火墙已开放 80 和 443 端口
- [ ] 环境变量已正确配置（`.env.production`）
- [ ] 数据库密码已修改为强密码
- [ ] Redis 密码已修改为强密码
- [ ] SECRET_KEY 已生成随机值
- [ ] 已运行 `./deploy.sh` 部署脚本
- [ ] 所有容器状态为 `Up`
- [ ] 健康检查通过
- [ ] 前端页面可以正常访问
- [ ] API 可以正常访问
- [ ] 沙盒店铺已初始化
- [ ] HTTPS 已配置（推荐）
- [ ] 证书自动续期已配置（如使用 HTTPS）

---

**部署完成后，你的 Temu-Omni 系统将在 http://echofrog.net 上运行！** 🎉

