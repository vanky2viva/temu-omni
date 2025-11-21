# 🚀 Temu-Omni 生产环境部署指南

> **服务器**: 129.226.67.95  
> **域名**: echofrog.net  
> **更新时间**: 2024-11-21

---

## ✅ 部署前准备检查清单

- [ ] 服务器已安装 Docker 和 Docker Compose
- [ ] 已配置域名DNS解析
- [ ] 已获取Temu API密钥
- [ ] 已准备数据库强密码
- [ ] 已配置SSH密钥认证

---

## 📦 第一步：上传代码到服务器

### 方式1：Git Clone（推荐）

```bash
# 在服务器上执行
cd /opt
git clone https://github.com/YOUR_USERNAME/temu-omni.git
cd temu-omni
```

### 方式2：打包上传

```bash
# 在本地执行
cd /Users/vanky/code/temu-Omni

# 清理开发文件
chmod +x clean-dev-files.sh
./clean-dev-files.sh

# 打包代码
tar czf temu-omni-prod.tar.gz \
  --exclude=node_modules \
  --exclude=.git \
  --exclude=*.log \
  --exclude=__pycache__ \
  .

# 上传到服务器
scp temu-omni-prod.tar.gz ubuntu@129.226.67.95:/opt/

# 在服务器上解压
ssh ubuntu@129.226.67.95
cd /opt
mkdir -p temu-omni
tar xzf temu-omni-prod.tar.gz -C temu-omni/
cd temu-omni
```

---

## ⚙️ 第二步：配置环境变量

```bash
# 复制环境变量模板
cp env.production.example .env.production

# 编辑配置文件
vim .env.production
```

### 必须修改的配置项：

```bash
# 1. 生成数据库密码
openssl rand -base64 32

# 2. 生成Redis密码
openssl rand -base64 32

# 3. 生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# 4. 填入配置文件
POSTGRES_PASSWORD=生成的数据库密码
REDIS_PASSWORD=生成的Redis密码
SECRET_KEY=生成的密钥

# 5. 配置管理员账户（推荐修改）
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=YourStrongPassword123!
DEFAULT_ADMIN_EMAIL=admin@echofrog.net

# 6. 配置Temu API（从Temu Seller Center获取）
TEMU_APP_KEY=your_production_app_key
TEMU_APP_SECRET=your_production_app_secret
TEMU_API_PROXY_URL=http://172.236.231.45:8001

# 7. 配置域名
DOMAIN=echofrog.net
```

### 完整的 `.env.production` 示例：

```env
# 数据库配置
POSTGRES_DB=temu_omni
POSTGRES_USER=temu_user
POSTGRES_PASSWORD=xK9mP2nQ5vR8wT1zA4bC7eF0hG3jL6oN

# Redis配置
REDIS_PASSWORD=aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV

# 应用安全配置
SECRET_KEY=wX2yZ3aB4cD5eF6gH7iJ8kL9mN0oP1qR2sT3uV4wX5yZ6aB7cD8eF9gH0iJ

# 默认管理员账户
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=EchoFrog@2024!
DEFAULT_ADMIN_EMAIL=admin@echofrog.net

# Temu API配置
TEMU_APP_KEY=your_production_app_key
TEMU_APP_SECRET=your_production_app_secret
TEMU_API_PROXY_URL=http://172.236.231.45:8001

# 域名配置
DOMAIN=echofrog.net

# 其他配置
TIMEZONE=Asia/Shanghai
AUTO_SYNC_ENABLED=true
SYNC_INTERVAL_MINUTES=30
```

### 设置文件权限：

```bash
chmod 600 .env.production
chown $USER:$USER .env.production
```

### 验证环境变量配置（重要！）

```bash
# 给验证脚本添加执行权限
chmod +x verify-env.sh

# 运行验证
./verify-env.sh
```

**必须看到以下输出才能继续：**

```
✅ 所有环境变量配置正确！
🎉 环境变量验证通过！可以安全部署。
```

如果看到警告或错误，请按提示修复后再继续部署。

---

## 🚀 第三步：一键部署

```bash
# 确保脚本可执行
chmod +x deploy-production.sh

# 执行部署
./deploy-production.sh
```

### 部署脚本会自动执行：

1. ✅ 停止现有容器
2. ✅ 构建最新镜像
3. ✅ 清理虚拟数据
4. ✅ 启动所有服务
5. ✅ 初始化数据库
6. ✅ 创建管理员账户

### 预计部署时间：5-10分钟

---

## ✅ 第四步：验证部署

### 1. 检查服务状态

```bash
docker compose -f docker-compose.prod.yml ps
```

**预期输出**（所有服务都应该是 `Up (healthy)`）：

```
NAME                 STATUS
temu-omni-backend    Up (healthy)
temu-omni-frontend   Up (healthy)
temu-omni-nginx      Up
temu-omni-postgres   Up (healthy)
temu-omni-redis      Up (healthy)
```

### 2. 检查日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs --tail=50

# 查看后端日志（应该看到 "Application startup complete"）
docker compose -f docker-compose.prod.yml logs backend | grep "startup"

# 查看前端日志
docker compose -f docker-compose.prod.yml logs frontend
```

### 3. 测试访问

```bash
# 测试前端（应返回200）
curl -I http://localhost/

# 测试API文档（应返回200）
curl -I http://localhost/docs

# 测试健康检查
curl http://localhost/health
```

### 4. 浏览器访问

- **前端首页**: http://129.226.67.95/ 或 http://echofrog.net/
- **API文档**: http://129.226.67.95/docs
- **健康检查**: http://129.226.67.95/health

### 5. 登录测试

使用您在 `.env.production` 中配置的管理员账户登录：

- 用户名: `admin` (或您自定义的)
- 密码: `EchoFrog@2024!` (或您自定义的)

⚠️ **首次登录后请立即修改密码！**

---

## 🔒 第五步：配置SSL/HTTPS（推荐）

### 1. 安装Certbot

```bash
sudo apt install -y certbot
```

### 2. 停止Nginx容器

```bash
cd /opt/temu-omni
docker compose -f docker-compose.prod.yml stop nginx
```

### 3. 获取SSL证书

```bash
sudo certbot certonly --standalone \
  -d echofrog.net \
  -d www.echofrog.net \
  --email admin@echofrog.net \
  --agree-tos \
  --no-eff-email
```

### 4. 复制证书到项目目录

```bash
sudo mkdir -p /opt/temu-omni/nginx/ssl
sudo cp /etc/letsencrypt/live/echofrog.net/fullchain.pem \
     /opt/temu-omni/nginx/ssl/echofrog.net.crt
sudo cp /etc/letsencrypt/live/echofrog.net/privkey.pem \
     /opt/temu-omni/nginx/ssl/echofrog.net.key
     
# 设置权限
sudo chown -R $USER:$USER /opt/temu-omni/nginx/ssl
sudo chmod 600 /opt/temu-omni/nginx/ssl/*.key
```

### 5. 编辑Nginx配置启用HTTPS

```bash
vim /opt/temu-omni/nginx/conf.d/temu-omni.conf
```

取消HTTPS部分的注释，并启用HTTP到HTTPS的重定向。

### 6. 重启Nginx

```bash
docker compose -f docker-compose.prod.yml start nginx
```

### 7. 配置自动续期

```bash
# 创建续期脚本
sudo cat > /etc/cron.monthly/renew-cert.sh << 'EOF'
#!/bin/bash
cd /opt/temu-omni
docker compose -f docker-compose.prod.yml stop nginx
certbot renew --quiet
cp /etc/letsencrypt/live/echofrog.net/fullchain.pem /opt/temu-omni/nginx/ssl/echofrog.net.crt
cp /etc/letsencrypt/live/echofrog.net/privkey.pem /opt/temu-omni/nginx/ssl/echofrog.net.key
docker compose -f docker-compose.prod.yml start nginx
EOF

sudo chmod +x /etc/cron.monthly/renew-cert.sh
```

---

## 📊 第六步：导入真实数据

部署完成后数据库是空的，需要导入真实数据：

### 方式1：API同步（推荐）

1. 访问 http://echofrog.net/shops
2. 点击"添加店铺"
3. 填写店铺信息和Access Token
4. 点击"同步数据"

### 方式2：Excel导入

1. 准备订单数据Excel文件
2. 访问店铺管理页面
3. 选择"导入数据" → 上传Excel文件

---

## 🛠️ 常用运维命令

### 查看服务状态

```bash
cd /opt/temu-omni
docker compose -f docker-compose.prod.yml ps
```

### 查看日志

```bash
# 实时查看所有日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# 查看最近100行日志
docker compose -f docker-compose.prod.yml logs --tail=100
```

### 重启服务

```bash
# 重启所有服务
docker compose -f docker-compose.prod.yml restart

# 重启特定服务
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart nginx
```

### 停止服务

```bash
# 停止所有服务（保留数据）
docker compose -f docker-compose.prod.yml stop

# 停止并删除容器（保留数据卷）
docker compose -f docker-compose.prod.yml down

# ⚠️ 停止并删除所有内容（包括数据）
docker compose -f docker-compose.prod.yml down -v
```

### 更新应用

```bash
cd /opt/temu-omni

# 拉取最新代码
git pull origin main

# 重新部署
./deploy-production.sh
```

### 备份数据库

```bash
# 手动备份
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U temu_user temu_omni | gzip > \
  backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 恢复数据库
gunzip < backup_20241121_120000.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U temu_user -d temu_omni
```

### 查看资源使用

```bash
# 查看容器资源使用情况
docker stats

# 查看磁盘使用
df -h
docker system df
```

---

## 🚨 故障排查

### 问题1：容器启动失败

```bash
# 1. 查看详细日志
docker compose -f docker-compose.prod.yml logs [服务名]

# 2. 检查配置
cat .env.production

# 3. 检查端口占用
sudo netstat -tlnp | grep -E '80|443|5432|6379|8000'

# 4. 重启服务
docker compose -f docker-compose.prod.yml restart
```

### 问题2：数据库连接失败

```bash
# 重启数据库
docker compose -f docker-compose.prod.yml restart postgres

# 测试连接
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U temu_user -d temu_omni -c "SELECT 1;"
```

### 问题3：前端502错误

```bash
# 重新构建前端
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### 问题4：权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER /opt/temu-omni
chmod 600 .env.production
```

### 问题5：磁盘空间不足

```bash
# 清理Docker未使用的资源
docker system prune -af --volumes

# 清理日志
find /var/lib/docker/containers -name "*.log" -exec truncate -s 0 {} \;
```

---

## 📈 性能优化建议

### 1. 数据库优化

```bash
# 进入数据库容器
docker compose -f docker-compose.prod.yml exec postgres psql -U temu_user -d temu_omni

# 创建索引（如果还没有）
CREATE INDEX IF NOT EXISTS idx_orders_shop_id ON orders(shop_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_time ON orders(order_time);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
```

### 2. 日志轮转

```bash
# Docker日志已通过docker-compose.prod.yml配置自动轮转
# 每个容器最多保留3个10MB的日志文件
```

### 3. 定期清理

```bash
# 创建清理脚本
cat > /opt/cleanup.sh << 'EOF'
#!/bin/bash
# 清理30天前的日志
find /opt/temu-omni -name "*.log" -mtime +30 -delete

# 清理Docker
docker system prune -af --volumes --filter "until=168h"
EOF

chmod +x /opt/cleanup.sh

# 添加到crontab（每周日执行）
(crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/cleanup.sh") | crontab -
```

---

## ⚠️ 安全注意事项

### 1. 密码安全

- ✅ 使用强密码（至少16位，包含大小写字母、数字和特殊字符）
- ✅ 定期更换密码（建议90天）
- ✅ 不要将 `.env.production` 提交到Git
- ✅ 妥善保管密码文件

### 2. 防火墙配置

```bash
# 安装UFW
sudo apt install -y ufw

# 配置防火墙规则
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 3. SSH安全

```bash
# 禁用密码登录，只允许密钥认证
sudo vim /etc/ssh/sshd_config

# 修改以下配置：
# PasswordAuthentication no
# PermitRootLogin no

# 重启SSH
sudo systemctl restart ssh
```

### 4. 定期更新

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# Docker镜像更新
cd /opt/temu-omni
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## 📞 获取帮助

如遇到问题，请提供以下信息：

1. 错误日志：
   ```bash
   docker compose -f docker-compose.prod.yml logs > error.log
   ```

2. 服务状态：
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

3. 系统信息：
   ```bash
   uname -a
   docker version
   docker compose version
   ```

---

**部署完成后记得：**

1. ✅ 修改默认管理员密码
2. ✅ 配置SSL/HTTPS证书
3. ✅ 设置数据库定期备份
4. ✅ 配置防火墙规则
5. ✅ 设置监控告警

**祝部署顺利！** 🎉

