# 502 Bad Gateway 错误修复指南

## 🔴 问题症状

访问网站时显示 **502 Bad Gateway** 错误，这表示 Nginx 无法连接到后端或前端服务。

## 🔍 快速排查步骤

### 步骤1: 检查容器状态

在服务器上执行：

```bash
cd /path/to/temu-Omni
docker-compose -f docker-compose.prod.yml ps
```

**预期结果**: 所有容器应该显示 "Up" 状态
- ✅ `temu-omni-postgres` - Up
- ✅ `temu-omni-redis` - Up  
- ✅ `temu-omni-backend` - Up
- ✅ `temu-omni-frontend` - Up
- ✅ `temu-omni-nginx` - Up

**如果容器未运行**:
```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看启动日志
docker-compose -f docker-compose.prod.yml logs
```

### 步骤2: 检查后端服务

```bash
# 查看后端日志
docker-compose -f docker-compose.prod.yml logs backend

# 检查后端是否正常响应
docker-compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health
```

**常见问题**:
- 数据库连接失败 → 检查 `DATABASE_URL` 配置
- 应用启动失败 → 查看日志中的错误信息

### 步骤3: 检查前端服务

```bash
# 查看前端日志
docker-compose -f docker-compose.prod.yml logs frontend

# 检查前端是否正常响应
docker-compose -f docker-compose.prod.yml exec frontend curl http://localhost:80
```

### 步骤4: 检查Nginx配置

```bash
# 测试Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 查看Nginx错误日志
docker-compose -f docker-compose.prod.yml logs nginx | grep error
```

### 步骤5: 检查容器网络

```bash
# 从Nginx容器测试后端连接
docker-compose -f docker-compose.prod.yml exec nginx wget -O- http://backend:8000/health

# 从Nginx容器测试前端连接
docker-compose -f docker-compose.prod.yml exec nginx wget -O- http://frontend:80
```

**如果连接失败**: 检查 Docker 网络配置

---

## 🛠️ 常见修复方法

### 修复1: 重启所有服务

```bash
# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 重新启动
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动（约30秒）
sleep 30

# 检查状态
docker-compose -f docker-compose.prod.yml ps
```

### 修复2: 检查环境变量

```bash
# 检查后端环境变量
docker-compose -f docker-compose.prod.yml exec backend env | grep -E 'DATABASE_URL|SECRET_KEY'

# 确保所有必需的环境变量都已设置
```

### 修复3: 重新构建容器

```bash
# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 查看构建日志
docker-compose -f docker-compose.prod.yml logs --tail=50
```

### 修复4: 检查端口占用

```bash
# 检查80端口是否被占用
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# 如果被占用，停止占用端口的服务或修改Nginx端口
```

### 修复5: 检查防火墙

```bash
# 检查防火墙状态
sudo ufw status

# 开放端口（如果防火墙开启）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果使用云服务器，还需要在云控制台配置安全组
```

---

## 🔧 详细诊断命令

运行以下命令收集诊断信息：

```bash
# 1. 容器状态
echo "=== 容器状态 ==="
docker-compose -f docker-compose.prod.yml ps

# 2. 后端健康检查
echo "=== 后端健康检查 ==="
docker-compose -f docker-compose.prod.yml exec backend curl -s http://localhost:8000/health || echo "后端无法访问"

# 3. 前端健康检查
echo "=== 前端健康检查 ==="
docker-compose -f docker-compose.prod.yml exec frontend curl -s http://localhost:80 || echo "前端无法访问"

# 4. Nginx测试后端连接
echo "=== Nginx -> 后端连接 ==="
docker-compose -f docker-compose.prod.yml exec nginx wget -qO- http://backend:8000/health || echo "Nginx无法连接后端"

# 5. Nginx测试前端连接
echo "=== Nginx -> 前端连接 ==="
docker-compose -f docker-compose.prod.yml exec nginx wget -qO- http://frontend:80 || echo "Nginx无法连接前端"

# 6. 查看错误日志
echo "=== 后端错误日志（最后20行）==="
docker-compose -f docker-compose.prod.yml logs --tail=20 backend | grep -i error

echo "=== Nginx错误日志（最后20行）==="
docker-compose -f docker-compose.prod.yml logs --tail=20 nginx | grep -i error
```

---

## 📋 检查清单

请按顺序检查：

- [ ] 所有Docker容器都在运行
- [ ] 后端服务可以访问（`http://backend:8000/health`）
- [ ] 前端服务可以访问（`http://frontend:80`）
- [ ] Nginx可以连接到后端和前端
- [ ] 端口80和443未被其他服务占用
- [ ] 防火墙已开放80和443端口
- [ ] 云服务器安全组已配置
- [ ] 环境变量配置正确

---

## 🚨 紧急修复

如果以上方法都不行，尝试完全重置：

```bash
# 1. 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 2. 清理网络（可选）
docker network prune -f

# 3. 重新启动
docker-compose -f docker-compose.prod.yml up -d

# 4. 等待启动完成
sleep 60

# 5. 检查状态
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=50
```

---

## 📞 需要帮助？

如果问题仍未解决，请提供以下信息：

1. `docker-compose ps` 的输出
2. `docker-compose logs backend` 的最后50行
3. `docker-compose logs nginx` 的最后50行
4. `docker-compose exec nginx nginx -t` 的输出

---

*最后更新: 2025-11-21*


