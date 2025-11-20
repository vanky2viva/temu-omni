# Temu API 代理服务器部署指南

## 概述

Temu API 代理服务器用于通过白名单 IP 转发 API 请求。由于 Temu API 有 IP 白名单限制，我们需要在已加入白名单的服务器上部署代理服务，然后本地和远程服务器的请求都通过这个代理转发。

## 架构说明

```
本地/远程服务器 → 代理服务器（白名单 IP） → Temu API
```

- **代理服务器**: 部署在白名单 IP (172.236.231.45) 上，接收来自客户端的请求
- **客户端**: 本地开发环境或远程服务器，通过代理服务器发送请求

## 配置信息

- **API Key**: `798478197604e93f6f2ce4c2e833041u`
- **App Secret**: `776a96163c56c53e237f5456d4e14765301aa8aa`
- **Access Token**: `upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k`
- **白名单 IP**: `172.236.231.45`
- **代理服务器端口**: `8001`

## 部署步骤

### 1. 在本地测试代理服务器

首先在本地测试代理服务器是否正常工作：

```bash
# 启动本地代理服务器
./start_proxy_local.sh

# 在另一个终端测试
python test_proxy.py --mode proxy
```

### 2. 部署到白名单服务器

使用部署脚本将代理服务器部署到白名单 IP 服务器：

```bash
./deploy_proxy.sh
```

部署脚本会：
1. 构建 Docker 镜像
2. 上传到服务器
3. 在服务器上启动容器

### 3. 配置客户端使用代理

在客户端的 `.env` 文件中添加代理 URL：

```env
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

或者在代码中直接指定：

```python
from app.temu.client import TemuAPIClient

client = TemuAPIClient(
    app_key="your_app_key",
    app_secret="your_app_secret",
    proxy_url="http://172.236.231.45:8001"
)
```

## 测试

### 测试代理服务器

```bash
# 测试通过代理访问
python test_proxy.py --mode proxy

# 测试直接访问（应该失败，因为 IP 不在白名单）
python test_proxy.py --mode direct

# 测试两者
python test_proxy.py --mode both
```

### 手动测试代理 API

```bash
# 健康检查
curl http://172.236.231.45:8001/health

# 测试代理请求
curl -X POST http://172.236.231.45:8001/api/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "api_type": "bg.open.accesstoken.info.get",
    "access_token": "upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k",
    "app_key": "798478197604e93f6f2ce4c2e833041u",
    "app_secret": "776a96163c56c53e237f5456d4e14765301aa8aa"
  }'
```

## 代理服务器 API

### POST /api/proxy

代理 Temu API 请求

**请求体**:
```json
{
  "api_type": "bg.open.accesstoken.info.get",
  "request_data": {},
  "access_token": "your_access_token",
  "app_key": "your_app_key",
  "app_secret": "your_app_secret"
}
```

**响应**:
```json
{
  "success": true,
  "result": {
    // Temu API 返回的数据
  }
}
```

或错误响应:
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_msg": "错误信息"
}
```

## 故障排查

### 代理服务器无法启动

1. 检查端口是否被占用：
   ```bash
   lsof -i :8001
   ```

2. 查看容器日志：
   ```bash
   docker logs temu-api-proxy
   ```

### 代理请求失败

1. 检查代理服务器是否运行：
   ```bash
   curl http://172.236.231.45:8001/health
   ```

2. 检查网络连接：
   ```bash
   ping 172.236.231.45
   ```

3. 检查防火墙设置，确保端口 8001 已开放

### 仍然收到 IP 白名单错误

确保代理服务器确实部署在白名单 IP 上，并且请求确实通过代理发送。检查客户端配置中的 `TEMU_API_PROXY_URL` 是否正确设置。

## 安全建议

1. **限制访问**: 在生产环境中，建议限制代理服务器的访问来源，只允许信任的 IP 访问
2. **使用 HTTPS**: 在生产环境中使用 HTTPS 加密通信
3. **认证**: 可以考虑添加 API Key 认证，防止未授权访问
4. **日志**: 定期检查代理服务器的访问日志

## 文件结构

```
backend/
  app/
    proxy/
      __init__.py
      main.py              # 代理服务器主应用
      requirements.txt     # 代理服务器依赖
  Dockerfile.proxy        # 代理服务器 Dockerfile

docker-compose.proxy.yml  # 代理服务器 Docker Compose 配置
deploy_proxy.sh          # 部署脚本
start_proxy_local.sh     # 本地启动脚本
test_proxy.py            # 测试脚本
```

## 更新代理服务器

如果需要更新代理服务器代码：

```bash
# 重新构建并部署
./deploy_proxy.sh
```

部署脚本会自动停止旧容器并启动新容器。

