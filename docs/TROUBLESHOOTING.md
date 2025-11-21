# 故障排查指南

## 🔍 无法访问问题排查

### 1. 检查服务状态

```bash
# 检查所有容器是否运行
docker-compose -f docker-compose.prod.yml ps

# 应该看到所有服务都是 "Up" 状态
# - temu-omni-postgres
# - temu-omni-redis
# - temu-omni-backend
# - temu-omni-frontend
# - temu-omni-nginx
```

### 2. 检查端口监听

```bash
# 检查80和443端口是否被监听
sudo netstat -tlnp | grep -E ':(80|443)'

# 或使用 ss 命令
sudo ss -tlnp | grep -E ':(80|443)'

# 应该看到 nginx 在监听这些端口
```

### 3. 检查防火墙

```bash
# 检查防火墙状态
sudo ufw status

# 如果防火墙开启，需要开放端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果使用云服务器，还需要在云控制台配置安全组规则
# 开放 80 和 443 端口
```

### 4. 检查Nginx配置

```bash
# 检查Nginx配置是否正确
:docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 查看Nginx配置
cat nginx/nginx.conf
cat nginx/conf.d/*.conf
```

### 5. 查看服务日志

```bash
# 查看Nginx日志
docker-compose -f docker-compose.prod.yml logs nginx

# 查看后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 查看前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 查看所有日志
docker-compose -f docker-compose.prod.yml logs
```

### 6. 测试服务连通性

```bash
# 在服务器上测试本地访问
curl http://localhost/health
curl http://localhost/api/health

# 测试后端服务
curl http://localhost:8000/health

# 测试前端服务
curl http://localhost:80
```

### 7. 检查网络连接

```bash
# 从外部测试（在本地电脑上）
curl http://129.226.67.95/health
curl http://129.226.67.95/api/health

# 如果无法访问，可能是：
# 1. 防火墙未开放端口
# 2. 云服务器安全组未配置
# 3. 服务未正常启动
```

---

## 🛠️ 常见问题解决

### 问题1: 容器无法启动

**症状**: `docker-compose ps` 显示容器状态为 "Exited"

**解决方法**:
```bash
# 查看容器日志
docker-compose -f docker-compose.prod.yml logs <service_name>

# 常见原因：
# 1. 环境变量配置错误
# 2. 数据库连接失败
# 3. 端口被占用
```

### 问题2: Nginx 502 Bad Gateway

**症状**: 访问网站显示 502 错误

**解决方法**:
```bash
# 检查后端服务是否运行
docker-compose -f docker-compose.prod.yml ps backend

# 检查后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查Nginx配置中的后端地址
# 应该指向 backend:8000（容器名）
```

### 问题3: 404 Not Found

**症状**: 访问网站显示 404 错误

**解决方法**:
```bash
# 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx cat /etc/nginx/nginx.conf

# 检查前端文件是否存在
docker-compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html
```

### 问题4: 无法连接数据库

**症状**: 后端日志显示数据库连接错误

**解决方法**:
```bash
# 检查数据库容器状态
docker-compose -f docker-compose.prod.yml ps postgres

# 检查数据库连接字符串
# 应该使用容器名 postgres，而不是 localhost

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.core.database import engine; engine.connect()"
```

### 问题5: CORS 错误

**症状**: 前端无法访问后端API，浏览器控制台显示CORS错误

**解决方法**:
```bash
# 检查后端 CORS_ORIGINS 配置
# 应该包含前端访问的域名

# 在 backend/.env 中配置
CORS_ORIGINS=["http://129.226.67.95","https://your-domain.com"]
```

---

## 🔧 快速修复命令

### 重启所有服务

```bash
docker-compose -f docker-compose.prod.yml restart
```

### 重新构建并启动

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 查看实时日志

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 进入Nginx容器
docker-compose -f docker-compose.prod.yml exec nginx sh
```

---

## 📋 检查清单

在服务器上执行以下命令，收集信息：

```bash
# 1. 服务状态
docker-compose -f docker-compose.prod.yml ps

# 2. 端口监听
sudo netstat -tlnp | grep -E ':(80|443|8000)'

# 3. 防火墙状态
sudo ufw status

# 4. Nginx配置测试
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 5. 服务日志（最后50行）
docker-compose -f docker-compose.prod.yml logs --tail=50 nginx
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# 6. 本地测试
curl -I http://localhost
curl -I http://localhost/api/health
```

---

*将以上命令的输出结果发送给我，我可以帮你进一步诊断问题。*


