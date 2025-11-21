# 生产环境部署指南

> **重要**: 本文档用于生产环境部署，请仔细阅读并按照步骤操作。

---

## 📋 部署前准备

### 1. 服务器要求

- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **CPU**: 2核+
- **内存**: 4GB+
- **磁盘**: 20GB+ 可用空间
- **网络**: 稳定的互联网连接

### 2. 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 3. 域名和证书（可选）

- 域名已解析到服务器IP
- SSL证书已准备（如使用HTTPS）

---

## 🚀 快速部署

### 步骤1: 克隆代码

```bash
git clone <repository-url>
cd temu-Omni
```

### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp env.production.example .env.production
cp backend/env.template backend/.env

# 编辑配置文件
nano .env.production
nano backend/.env
```

**必须配置的变量**:
- `SECRET_KEY` - 应用密钥（使用强密码）
- `DATABASE_URL` - 数据库连接字符串
- `TEMU_APP_KEY` / `TEMU_APP_SECRET` - Temu API 密钥
- `TEMU_API_PROXY_URL` - 代理服务器地址
- `CORS_ORIGINS` - 允许的前端域名

### 步骤3: 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 步骤4: 初始化数据库

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 初始化数据库
python scripts/init_production_database.py

# 创建默认管理员用户
python scripts/init_default_user.py
```

### 步骤5: 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查API文档
curl http://localhost:8000/docs
```

---

## ⚙️ 配置说明

### 环境变量配置

详细配置说明请查看 [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)

### 定时任务配置

系统默认启用以下定时任务：

- **订单同步**: 每30分钟（增量同步）
- **商品同步**: 每60分钟（增量同步）
- **成本计算**: 每30分钟

如需调整，修改 `backend/.env` 中的 `SYNC_INTERVAL_MINUTES`。

---

## 🔧 日常维护

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
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

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build
```

### 数据备份

```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U temu_user temu_omni < backup_20251121_120000.sql
```

---

## 📊 监控和验证

### 检查定时任务状态

```bash
# 通过API检查
curl -X GET "http://localhost:8000/api/system/scheduler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 验证数据同步

```bash
# 运行验证脚本
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/verify_order_amount_and_collection.py
```

### 手动触发同步

```bash
# 同步指定店铺
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/sync_shop_cli.py --shop-id 1
```

---

## 🐛 故障排查

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 查看容器日志
   - 验证环境变量配置

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查网络连接

3. **定时任务未执行**
   - 检查调度器状态
   - 查看应用日志
   - 验证配置

详细故障排查请查看 [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)

---

## 📚 相关文档

- [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)
- [数据同步策略](docs/SYNC_STRATEGY.md)
- [系统架构](docs/ARCHITECTURE.md)
- [完整文档索引](docs/README.md)

---

*部署完成后，请定期检查系统运行状态和日志。*

