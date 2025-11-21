# 修复同步API未通过代理服务器的问题

## 🔍 问题描述

同步API时出现 `NOT_IN_IP_WHITE_LIST` 错误，说明请求没有通过代理服务器，而是直接访问了Temu API。

## ✅ 已修复

### 问题原因

配置类 `Settings` 中的 `TEMU_API_PROXY_URL` 字段没有正确加载，导致同步服务无法获取代理URL，从而直接访问Temu API。

### 修复内容

1. **更新配置类** (`backend/app/core/config.py`)
   - 确保 `TEMU_API_PROXY_URL` 字段正确定义
   - 添加了 `env_file_encoding = "utf-8"` 配置

2. **重新构建后端镜像**
   - 更新后的配置已包含在镜像中
   - 配置现在可以正确读取环境变量

### 验证修复

```bash
# 检查配置是否正确加载
docker-compose -f docker-compose.prod.yml exec backend python -c \
  "from app.core.config import settings; print('PROXY_URL:', settings.TEMU_API_PROXY_URL)"
```

应该输出：`PROXY_URL: http://172.236.231.45:8001`

## 🔧 工作原理

### 代理使用流程

1. **同步服务初始化**
   ```python
   sync_service = SyncService(db, shop)
   # SyncService 使用 get_temu_service(shop) 创建 TemuService
   ```

2. **TemuService 创建客户端**
   ```python
   # TemuService._get_standard_client() 方法
   proxy_url = settings.TEMU_API_PROXY_URL  # 从配置读取
   client = TemuAPIClient(
       app_key=app_key,
       app_secret=app_secret,
       proxy_url=proxy_url  # 传递代理URL
   )
   ```

3. **TemuAPIClient 发送请求**
   ```python
   # TemuAPIClient._request() 方法
   if self.proxy_url:
       return await self._request_via_proxy(...)  # 通过代理
   else:
       # 直接请求（不应该发生）
   ```

### 代理请求流程

当 `proxy_url` 存在时，所有请求都会：
1. 发送到代理服务器：`http://172.236.231.45:8001/api/proxy`
2. 代理服务器转发到 Temu API
3. 返回响应给应用

## 📋 配置要求

### 环境变量

确保 `.env` 文件中包含：

```env
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

### Docker Compose 配置

`docker-compose.prod.yml` 中已配置：

```yaml
environment:
  - TEMU_API_PROXY_URL=${TEMU_API_PROXY_URL:-http://172.236.231.45:8001}
```

## ✅ 验证步骤

1. **检查配置**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend \
     python -c "from app.core.config import settings; print(settings.TEMU_API_PROXY_URL)"
   ```

2. **测试同步**
   - 在前端点击"同步"按钮
   - 查看后端日志，应该看到代理相关的日志

3. **检查日志**
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend | grep -i proxy
   ```

## 🚨 注意事项

1. **代理服务器必须运行**
   - 确保代理服务器 `http://172.236.231.45:8001` 可访问
   - 代理服务器的IP必须在Temu的白名单中

2. **环境变量优先级**
   - Docker Compose 环境变量 > `.env` 文件
   - 确保环境变量正确传递到容器

3. **CN端点不使用代理**
   - CN端点的API请求直接访问，不使用代理
   - 只有标准端点（US/EU/GLOBAL）使用代理

---

*修复完成时间: 2025-11-21*


