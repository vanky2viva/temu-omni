# 🚀 生产环境部署指南

本文档说明如何在生产服务器上部署 Temu-Omni，并清理虚拟数据、初始化真实数据库。

---

## 📋 部署前准备

### 1. 服务器要求

- **操作系统**: Ubuntu 20.04+ 或 Debian 10+
- **内存**: 最少 2GB RAM（推荐 4GB+）
- **磁盘**: 最少 20GB 可用空间
- **网络**: 可访问 Docker Hub 和 GitHub
- **权限**: sudo 权限

### 2. 必需的软件

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# 安装 Docker Compose v2
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

---

## 🔧 配置步骤

### 步骤 1: 准备环境变量

```bash
# 在服务器上克隆项目
cd /opt
sudo git clone <你的仓库地址> temu-Omni
cd temu-Omni

# 设置权限
sudo chown -R $USER:$USER .

# 复制环境变量模板
cp env.production.example .env.production
```

### 步骤 2: 编辑环境变量

```bash
nano .env.production
```

**必须修改以下配置：**

```env
# 数据库密码（生产环境必须使用强密码）
POSTGRES_PASSWORD=你的强密码123
REDIS_PASSWORD=你的强密码456

# 应用密钥（自动生成）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Temu API 配置（使用真实凭证或测试凭证）
TEMU_APP_KEY=你的App_Key
TEMU_APP_SECRET=你的App_Secret
```

### 步骤 3: 生成 SECRET_KEY

```bash
# 生成随机密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 将生成的密钥复制到 .env.production 的 SECRET_KEY 字段
```

---

## 🗑️ 清理虚拟数据并初始化真实数据库

### 选项 A: 完全重置数据库（推荐用于首次部署）

```bash
# 执行生产数据库初始化脚本
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_production_database.py
```

此脚本会：
- ✅ 删除所有现有表和虚拟数据
- ✅ 重新创建数据库表结构
- ✅ 初始化基础配置
- ❌ **不会**生成任何虚拟数据

### 选项 B: 仅清理虚拟数据（保留真实数据）

```bash
# 清理所有 DEMO_ 开头的店铺及其数据
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import SessionLocal
from app.models.shop import Shop

db = SessionLocal()
try:
    demo_shops = db.query(Shop).filter(Shop.shop_id.like('DEMO_%')).all()
    for shop in demo_shops:
        db.delete(shop)
    db.commit()
    print(f'✓ 已删除 {len(demo_shops)} 个演示店铺')
finally:
    db.close()
"
```

---

## 🚀 开始部署

### 步骤 1: 授予执行权限

```bash
chmod +x deploy.sh
```

### 步骤 2: 执行部署

```bash
./deploy.sh
```

部署脚本会自动：
1. 停止现有容器
2. 拉取最新镜像
3. 构建新镜像
4. 启动所有服务
5. 检查服务状态

### 步骤 3: 初始化数据库

```bash
# 等待容器启动完成（约30秒）
sleep 30

# 初始化生产数据库（不带虚拟数据）
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_production_database.py
```

---

## 📊 导入真实数据

数据库初始化完成后，有三种方式导入真实数据：

### 方式 1: API 同步（推荐）

如果你有 Temu 店铺的 API 凭证：

```bash
# 1. 通过前端界面添加店铺
# 访问 http://echofrog.net/shops

# 2. 点击"同步数据"按钮，或使用 API
curl -X POST "http://echofrog.net/api/sync/shops/{shop_id}/all"
```

### 方式 2: Excel 文件导入

```bash
# 1. 访问 http://echofrog.net/shops
# 2. 选择店铺 → 导入数据 → 选择Excel文件
# 3. 上传订单/商品/活动数据
```

### 方式 3: 在线表格导入

```bash
# 1. 访问 http://echofrog.net/shops
# 2. 选择店铺 → 导入数据 → 在线表格
# 3. 粘贴飞书表格链接
```

---

## ✅ 验证部署

### 1. 健康检查

```bash
# API 健康检查
curl http://echofrog.net/health

# 应该返回: {"status":"ok"}
```

### 2. 检查容器状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

所有服务应显示 `Up` 状态。

### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### 4. 访问前端

在浏览器中打开：
- **前端界面**: http://echofrog.net
- **API 文档**: http://echofrog.net/docs

---

## 🔄 更新部署

当有代码更新时：

```bash
# 1. 拉取最新代码
git pull

# 2. 重新部署
./deploy.sh

# 3. 如果需要，重新初始化数据库
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_production_database.py
```

---

## 🛠️ 常用运维命令

### 查看服务状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

### 停止服务

```bash
docker-compose -f docker-compose.prod.yml down
```

### 停止并清理数据（⚠️ 危险）

```bash
# 停止服务并删除所有数据卷
docker-compose -f docker-compose.prod.yml down -v
```

### 查看日志

```bash
# 实时查看所有日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看最近100行日志
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 进入数据库容器
docker-compose -f docker-compose.prod.yml exec postgres psql -U temu_user -d temu_omni
```

### 备份数据库

```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U temu_user temu_omni < backup_20240101_120000.sql
```

---

## 🔐 安全建议

### 1. 修改默认密码

确保 `.env.production` 中的所有密码都是强密码：
- 使用至少16位字符
- 包含大小写字母、数字和特殊字符
- 不要使用简单密码如 `123456` 或 `password`

### 2. 配置防火墙

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 启用 HTTPS

参考 [快速部署指南](DEPLOY_QUICKSTART.md) 中的 HTTPS 配置部分。

### 4. 定期备份

设置自动备份任务：

```bash
# 编辑 crontab
crontab -e

# 添加每日备份任务（每天凌晨2点）
0 2 * * * cd /opt/temu-Omni && docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U temu_user temu_omni > /var/backups/temu_omni_$(date +\%Y\%m\%d).sql
```

---

## 🐛 问题排查

### 问题 1: 容器启动失败

```bash
# 查看详细错误日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查端口是否被占用
sudo lsof -i :80
sudo lsof -i :443
```

### 问题 2: 数据库连接失败

```bash
# 检查数据库容器状态
docker-compose -f docker-compose.prod.yml ps postgres

# 重启数据库
docker-compose -f docker-compose.prod.yml restart postgres

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U temu_user -d temu_omni -c "SELECT 1;"
```

### 问题 3: 前端显示空白

```bash
# 检查前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 重启前端
docker-compose -f docker-compose.prod.yml restart frontend

# 检查浏览器控制台（F12）
```

### 问题 4: API 请求失败

```bash
# 检查后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 测试 API 连接
curl http://localhost/api/health
```

---

## 📞 获取帮助

- 查看完整文档: `docs/INDEX.md`
- API 文档: http://echofrog.net/docs
- 提交 Issue: GitHub

---

**部署完成后，恭喜！系统已准备就绪，可以开始导入真实数据了。** 🎉

