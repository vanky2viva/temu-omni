# Temu API 代理服务器快速开始

## 概述

Temu API 代理服务器已搭建完成，用于通过白名单 IP (172.236.231.45) 转发所有 API 请求。

## 已配置信息

- **API Key**: `798478197604e93f6f2ce4c2e833041u`
- **App Secret**: `776a96163c56c53e237f5456d4e14765301aa8aa`
- **Access Token**: `upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k`
- **代理服务器地址**: `http://172.236.231.45:8001`

## 快速开始

### 方法 1: 在 proxy-server 文件夹内操作（推荐）

```bash
# 进入代理服务器文件夹
cd proxy-server

# 使用 Docker Compose 启动（推荐）
docker-compose up -d

# 或使用本地启动脚本
./start.sh

# 测试连接
python test_quick.py http://localhost:8001
```

### 方法 2: 从项目根目录部署

```bash
# 部署到远程服务器
./deploy_proxy.sh

# 测试远程代理服务器
python test_proxy_quick.py http://172.236.231.45:8001
python test_proxy.py --mode proxy
```

### 手动部署到远程服务器

```bash
# 1. 将 proxy-server 文件夹上传到服务器
scp -r proxy-server root@172.236.231.45:/opt/

# 2. SSH 到服务器
ssh root@172.236.231.45

# 3. 在服务器上启动
cd /opt/proxy-server
docker-compose up -d

# 或使用部署脚本
./deploy.sh
```

## 配置客户端使用代理

### 方法 1: 环境变量

在 `.env` 文件中添加：

```env
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

### 方法 2: 代码中指定

```python
from app.temu.client import TemuAPIClient

client = TemuAPIClient(
    app_key="798478197604e93f6f2ce4c2e833041u",
    app_secret="776a96163c56c53e237f5456d4e14765301aa8aa",
    proxy_url="http://172.236.231.45:8001"
)

# 使用客户端
result = await client.get_token_info("upsfmfl9g5bbxpn8rvhols3c959kghjc0cvcripjfsmfzihkykxsaobrb3k")
```

## 文件结构

```
proxy-server/              # 独立的代理服务器文件夹（可单独部署）
  app/
    __init__.py
    main.py                # 代理服务器主应用
  requirements.txt         # Python 依赖
  Dockerfile              # Docker 镜像定义
  docker-compose.yml      # Docker Compose 配置
  deploy.sh               # 部署脚本（在 proxy-server 文件夹内使用）
  start.sh                # 本地启动脚本
  test_quick.py           # 快速测试脚本
  README.md               # 代理服务器说明文档
  .dockerignore
  .gitignore

项目根目录/
  deploy_proxy.sh         # 从项目根目录部署的脚本
  test_proxy.py           # 完整功能测试脚本
  test_proxy_quick.py     # 快速连接测试脚本
  PROXY_README.md         # 本文件
  docs/PROXY_SETUP.md     # 详细部署文档
```

## 下一步

1. ✅ 代理服务器代码已创建
2. ✅ 客户端已支持代理模式
3. ⏭️ 部署代理服务器到白名单 IP
4. ⏭️ 测试代理功能
5. ⏭️ 配置生产环境使用代理

## 故障排查

如果遇到问题，请查看 `docs/PROXY_SETUP.md` 中的故障排查部分。

