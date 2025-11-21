# 环境变量检查指南

## 🔍 快速检查

在服务器上运行：

```bash
cd /home/ubuntu/temu-omni
./scripts/check_env_quick.sh
```

## 📋 必需的环境变量清单

### 已检查到的变量

从你的配置中看到：
- ✅ `SECRET_KEY` - 已设置
- ✅ `TEMU_APP_KEY` - 已设置

### 还需要检查的变量

请确认以下变量是否已设置：

```bash
# 检查所有必需变量
cat .env.production | grep -E "SECRET_KEY|POSTGRES_PASSWORD|REDIS_PASSWORD|TEMU_APP_KEY|TEMU_APP_SECRET|TEMU_API_PROXY_URL"
```

### 必需变量说明

| 变量名 | 状态 | 说明 |
|-------|------|------|
| `SECRET_KEY` | ✅ 已设置 | 应用密钥 |
| `POSTGRES_PASSWORD` | ⚠️ 需检查 | 数据库密码 |
| `REDIS_PASSWORD` | ⚠️ 需检查 | Redis密码 |
| `TEMU_APP_KEY` | ✅ 已设置 | Temu API密钥 |
| `TEMU_APP_SECRET` | ⚠️ 需检查 | Temu API密钥（重要！） |
| `TEMU_API_PROXY_URL` | ⚠️ 需检查 | 代理服务器地址 |

## 🔧 如果缺少变量

### 1. 检查当前配置

```bash
# 查看所有环境变量
cat .env.production

# 或只查看关键变量
cat .env.production | grep -v "^#" | grep -v "^$"
```

### 2. 添加缺失的变量

编辑 `.env.production` 文件：

```bash
nano .env.production
```

确保包含以下内容：

```env
# 应用密钥
SECRET_KEY=nM324ET1qW26VEzJoCXegK4d-h4AznEHCvVCggX3-nM

# 数据库密码
POSTGRES_PASSWORD=fX&aQPLaxNTRM%4^

# Redis密码
REDIS_PASSWORD=RebtbRZ^*l#j*QBm

# Temu API配置
TEMU_APP_KEY=798478197604e93f6f2ce4c2e833041u
TEMU_APP_SECRET=你的TEMU_APP_SECRET值

# 代理服务器
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

### 3. 重启服务

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重新启动（读取新的环境变量）
docker-compose -f docker-compose.prod.yml up -d

# 等待启动
sleep 30

# 检查状态
docker-compose -f docker-compose.prod.yml ps
```

## ⚠️ 特别注意

### TEMU_APP_SECRET 很重要

如果 `TEMU_APP_SECRET` 未设置，后端服务可能无法正常启动，导致 502 错误。

检查方法：

```bash
# 检查是否设置
grep "^TEMU_APP_SECRET=" .env.production

# 检查容器中的环境变量
docker-compose -f docker-compose.prod.yml exec backend env | grep TEMU_APP_SECRET
```

## ✅ 验证配置

配置完成后，验证：

```bash
# 1. 检查环境变量文件
./scripts/check_env_quick.sh

# 2. 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 3. 检查后端日志（不应该有环境变量相关错误）
docker-compose -f docker-compose.prod.yml logs backend | grep -i "error\|secret\|key"

# 4. 测试后端服务
curl http://localhost:8000/health
```

---

*配置完成后，请重启服务以使环境变量生效。*


