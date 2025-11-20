# API 代理服务器配置说明

## 概述

订单API必须通过代理服务器访问。系统已配置代理服务器参数，默认使用远程代理服务器地址。

## 代理服务器地址

根据 `PROXY_README.md`，代理服务器地址为：
- **远程服务器**: `http://172.236.231.45:8001`
- **本地开发**: `http://localhost:8001`（如果代理服务器在本地运行）

## 配置方式

### 1. 环境变量配置（推荐）

#### 开发环境

在 `.env` 文件中添加：
```env
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

或者如果代理服务器在本地运行：
```env
TEMU_API_PROXY_URL=http://localhost:8001
```

#### 生产环境

在 `env.production` 文件中添加：
```env
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

### 2. Docker Compose 配置

#### 开发环境 (`docker-compose.yml`)

已配置环境变量：
```yaml
environment:
  - TEMU_API_PROXY_URL=${TEMU_API_PROXY_URL:-http://172.236.231.45:8001}
```

可以通过环境变量覆盖：
```bash
export TEMU_API_PROXY_URL=http://localhost:8001
docker-compose up -d
```

#### 生产环境 (`docker-compose.prod.yml`)

已配置环境变量：
```yaml
environment:
  - TEMU_API_PROXY_URL=${TEMU_API_PROXY_URL:-http://172.236.231.45:8001}
```

### 3. 本地运行（不使用Docker）

设置环境变量：
```bash
export TEMU_API_PROXY_URL=http://172.236.231.45:8001
# 或
export TEMU_API_PROXY_URL=http://localhost:8001
```

## 代理服务器部署

### 如果代理服务器在远程服务器运行

代理服务器地址：`http://172.236.231.45:8001`

确保：
1. 代理服务器已部署并运行
2. 网络可以访问该地址
3. 端口 8001 已开放

### 如果代理服务器在本地运行

#### 方式1：使用独立的代理服务器服务

```bash
cd proxy-server
docker-compose up -d
```

然后配置 `TEMU_API_PROXY_URL=http://localhost:8001`

#### 方式2：在主 docker-compose 中添加代理服务

取消注释 `docker-compose.yml` 中的代理服务器配置：
```yaml
temu-api-proxy:
  build:
    context: ./proxy-server
    dockerfile: Dockerfile
  container_name: temu-api-proxy
  ports:
    - "8001:8001"
  networks:
    - temu-network
```

然后配置 `TEMU_API_PROXY_URL=http://temu-api-proxy:8001`（在Docker网络内）

## 验证配置

### 检查环境变量

```bash
# 检查环境变量是否设置
echo $TEMU_API_PROXY_URL
```

### 测试代理服务器连接

```bash
# 测试代理服务器是否可访问
curl http://172.236.231.45:8001/health
```

### 检查后端日志

启动后端服务后，查看日志中是否有：
```
创建标准端点客户端 - 店铺: xxx, 使用代理: 是
```

## 配置优先级

1. **环境变量** `TEMU_API_PROXY_URL`（最高优先级）
2. **Docker Compose 环境变量** `${TEMU_API_PROXY_URL:-默认值}`
3. **配置文件** `.env` 文件中的值

## 注意事项

1. ⚠️ **订单API必须通过代理服务器**，未配置代理服务器会导致订单同步失败
2. ⚠️ **商品API**：如果使用CN端点，不需要代理；如果使用标准端点，需要代理
3. ⚠️ **分类API**：使用标准端点，需要代理
4. 代理服务器地址必须可访问，否则所有API请求都会失败

## 故障排查

### 错误：代理服务器未配置

**错误信息**：
```
代理服务器未配置。所有 API 请求必须通过代理服务器。
请在配置中设置 TEMU_API_PROXY_URL。
```

**解决方案**：
1. 检查环境变量 `TEMU_API_PROXY_URL` 是否设置
2. 检查 `.env` 文件或 Docker Compose 配置
3. 重启服务使配置生效

### 错误：无法连接到代理服务器

**错误信息**：
```
网络请求错误: Connection refused
```

**解决方案**：
1. 检查代理服务器是否运行：`curl http://代理地址:8001/health`
2. 检查网络连接和防火墙设置
3. 确认代理服务器地址和端口正确

### 本地开发时使用本地代理

如果代理服务器在本地运行，确保：
1. 代理服务器已启动（`cd proxy-server && docker-compose up -d`）
2. 配置 `TEMU_API_PROXY_URL=http://localhost:8001`
3. 如果使用Docker，可能需要使用 `host.docker.internal:8001` 或配置网络

## 相关文件

- `backend/env.template` - 环境变量模板
- `env.production.example` - 生产环境配置示例
- `env.docker.template` - Docker环境变量模板
- `docker-compose.yml` - 开发环境Docker配置
- `docker-compose.prod.yml` - 生产环境Docker配置
- `PROXY_README.md` - 代理服务器部署说明

