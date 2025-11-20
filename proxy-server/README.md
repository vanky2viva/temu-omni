# Temu API 代理服务器

独立的 Temu API 代理服务器，用于通过白名单 IP 转发 API 请求。

## 快速开始

### 使用 Docker 部署（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 部署到远程服务器

### 方法 1: 使用部署脚本（在 proxy-server 文件夹内）

```bash
# 在 proxy-server 文件夹内执行
./deploy.sh
```

### 方法 2: 使用项目根目录的部署脚本

```bash
# 从项目根目录执行
cd ..
./deploy_proxy.sh
```

### 方法 3: 手动部署

1. 将整个 `proxy-server` 文件夹上传到服务器：
```bash
scp -r proxy-server root@172.236.231.45:/opt/
```

2. SSH 到服务器并启动：
```bash
ssh root@172.236.231.45
cd /opt/proxy-server
docker-compose up -d
```

## 测试

### 健康检查

```bash
curl http://localhost:8001/health
```

### 测试代理 API

```bash
curl -X POST http://localhost:8001/api/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "api_type": "bg.open.accesstoken.info.get",
    "access_token": "your_access_token",
    "app_key": "your_app_key",
    "app_secret": "your_app_secret"
  }'
```

## API 文档

启动服务后，访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 配置

### 环境变量配置

创建 `.env` 文件（或设置环境变量）：

```bash
# Temu API 凭证（默认值，如果客户端未提供则使用此配置）
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret
```

### 默认配置

- 端口: 8001
- Temu API URL: https://agentpartner.temu.com/api

### 使用方式

代理服务器支持两种调用方式：

**方式 1：简化调用（推荐）**
客户端只需提供 `access_token`，`app_key` 和 `app_secret` 从代理服务器环境变量读取：

```json
{
  "api_type": "bg.open.accesstoken.info.get",
  "access_token": "店铺的access_token"
}
```

**方式 2：完整调用**
客户端提供所有参数（适用于多应用场景）：

```json
{
  "api_type": "bg.open.accesstoken.info.get",
  "access_token": "店铺的access_token",
  "app_key": "应用key",
  "app_secret": "应用secret"
}
```

### 多店铺场景

由于不同店铺的 `access_token` 不同，客户端只需要：
1. 在请求中传入对应店铺的 `access_token`
2. `app_key` 和 `app_secret` 可以统一在代理服务器配置（如果所有店铺使用同一个应用）
3. 或者每次请求时传入不同的 `app_key`/`app_secret`（如果不同店铺使用不同应用）

## 文件结构

```
proxy-server/
  app/
    __init__.py
    main.py              # 主应用文件
  requirements.txt       # Python 依赖
  Dockerfile            # Docker 镜像定义
  docker-compose.yml    # Docker Compose 配置
  deploy.sh             # 部署脚本（部署到远程服务器）
  start.sh              # 本地启动脚本
  test_quick.py         # 快速测试脚本
  README.md             # 本文件
  .dockerignore
  .gitignore
```

## 故障排查

### 端口被占用

```bash
# 检查端口占用
lsof -i :8001

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8002:8001"  # 将主机端口改为 8002
```

### 查看日志

```bash
# Docker Compose
docker-compose logs -f

# Docker 容器
docker logs temu-api-proxy -f
```

