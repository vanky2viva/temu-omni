# 🚀 生产环境部署说明

## 📦 已准备的文件

以下文件已为生产环境部署准备就绪：

### ✅ 部署脚本
- **`deploy-production.sh`** - 一键完整部署脚本（推荐使用）
  - 自动停止现有容器
  - 构建最新镜像
  - 启动所有服务
  - **自动清理虚拟数据**
  - **初始化生产数据库**

### ✅ 数据库脚本
- **`backend/scripts/init_production_database.py`** - 生产环境数据库初始化
  - 删除所有现有表和数据
  - 重新创建表结构
  - 初始化基础配置
  - **不生成任何虚拟数据**

### ✅ 配置文件
- **`docker-compose.prod.yml`** - 生产环境 Docker 编排
- **`env.production.example`** - 环境变量模板
- **`nginx/conf.d/temu-omni.conf`** - Nginx 站点配置

### ✅ 文档
- **`docs/deployment/PRODUCTION_DEPLOYMENT.md`** - 完整部署指南
- **`docs/deployment/DEPLOY_QUICKSTART.md`** - 快速部署指南

---

## 🎯 快速部署步骤

### 在服务器上执行：

```bash
# 1. 克隆或拉取最新代码
cd /opt/temu-Omni
git pull

# 2. 配置环境变量（首次部署）
cp env.production.example .env.production
nano .env.production  # 修改密码和密钥

# 3. 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 将输出的密钥复制到 .env.production 的 SECRET_KEY 字段

# 4. 一键部署（会自动清理虚拟数据）
./deploy-production.sh
```

### 部署完成后：

```bash
# 访问前端界面
# http://echofrog.net

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 健康检查
curl http://echofrog.net/health
```

---

## 📊 导入真实数据

部署完成后，数据库已清理所有虚拟数据，现在可以导入真实数据：

### 方式 1: API 同步（推荐）

1. 访问 http://echofrog.net/shops
2. 点击"添加店铺"
3. 填写店铺信息和 Access Token
4. 点击"同步数据"

### 方式 2: Excel 导入

1. 访问 http://echofrog.net/shops
2. 选择店铺 → 导入数据 → 选择文件
3. 上传 Excel 文件

### 方式 3: 在线表格导入

1. 访问 http://echofrog.net/shops
2. 选择店铺 → 导入数据 → 在线表格
3. 粘贴飞书表格链接

---

## 🔍 验证部署

### 检查服务状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

所有服务应显示 `Up (healthy)` 状态。

### 测试 API

```bash
# 健康检查
curl http://echofrog.net/health

# API 文档
open http://echofrog.net/docs
```

### 检查数据库

```bash
# 进入数据库容器
docker-compose -f docker-compose.prod.yml exec postgres psql -U temu_user -d temu_omni

# 查看表结构
\dt

# 检查数据（应该没有虚拟数据）
SELECT COUNT(*) FROM shops WHERE shop_id LIKE 'DEMO_%';
# 应该返回 0

# 退出
\q
```

---

## 🔄 重新部署（更新代码）

```bash
# 拉取最新代码
git pull

# 重新部署
./deploy-production.sh
```

---

## 🛠️ 常用运维命令

### 查看日志

```bash
# 所有服务
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
```

### 停止服务

```bash
docker-compose -f docker-compose.prod.yml down
```

### 备份数据库

```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U temu_user temu_omni < backup_20240101.sql
```

---

## ⚠️ 注意事项

### 1. 环境变量安全

- ✅ 使用强密码
- ✅ SECRET_KEY 应该是随机生成的
- ❌ 不要将 `.env.production` 提交到 Git

### 2. 数据库清理

- ⚠️ **`init_production_database.py`** 会删除所有数据
- ⚠️ 部署前请确保已备份重要数据
- ✅ 推荐使用真实 API 或文件导入数据

### 3. 网络配置

- 确保防火墙开放 80 和 443 端口
- 域名应正确解析到服务器 IP

### 4. 资源监控

```bash
# 查看容器资源使用情况
docker stats

# 查看磁盘使用
df -h
docker system df
```

---

## 📖 更多文档

- [完整部署指南](docs/deployment/PRODUCTION_DEPLOYMENT.md)
- [快速部署指南](docs/deployment/DEPLOY_QUICKSTART.md)
- [数据导入说明](docs/import/)
- [API 文档](docs/API.md)

---

## 🆘 问题排查

### 容器启动失败

```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查配置
cat .env.production
```

### 数据库连接失败

```bash
# 重启数据库
docker-compose -f docker-compose.prod.yml restart postgres

# 测试连接
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U temu_user -d temu_omni -c "SELECT 1;"
```

### 前端显示空白

```bash
# 检查前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 重启前端
docker-compose -f docker-compose.prod.yml restart frontend
```

---

**现在您已经准备好部署到生产环境了！** 🎉

按照上面的步骤，在服务器上执行 `./deploy-production.sh` 即可完成一键部署。

