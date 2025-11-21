# 快速诊断指南

## 🚀 一键诊断

在服务器上运行诊断脚本：

```bash
cd /home/ubuntu/temu-omni
./scripts/diagnose_server.sh
```

脚本会自动检查：
- ✅ Docker服务状态
- ✅ 容器运行状态
- ✅ 环境变量配置
- ✅ 端口占用情况
- ✅ 防火墙配置
- ✅ 后端服务健康
- ✅ 前端服务状态
- ✅ Nginx配置和连接
- ✅ 数据库连接
- ✅ Docker网络
- ✅ 错误日志
- ✅ 本地访问测试

---

## 📋 常见问题快速修复

### 问题1: 容器未运行

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

### 问题2: 502 Bad Gateway

```bash
# 检查后端服务
docker-compose -f docker-compose.prod.yml logs backend

# 检查Nginx连接
docker-compose -f docker-compose.prod.yml exec nginx wget -O- http://backend:8000/health

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

### 问题3: 环境变量未设置

```bash
# 创建环境变量文件
cp env.production.example .env.production
nano .env.production

# 重启服务
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 问题4: 端口被占用

```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo ss -tlnp | grep :80

# 如果被其他服务占用，停止该服务或修改Nginx端口
```

### 问题5: 防火墙阻止

```bash
# 检查防火墙
sudo ufw status

# 开放端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 🔍 手动检查步骤

### 1. 检查服务状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

所有容器应该显示 "Up" 状态。

### 2. 检查日志

```bash
# 查看所有日志
docker-compose -f docker-compose.prod.yml logs --tail=50

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs nginx
```

### 3. 测试服务连接

```bash
# 测试后端
curl http://localhost:8000/health

# 测试前端
curl http://localhost:80

# 测试API
curl http://localhost/api/health
```

### 4. 检查网络

```bash
# 检查Docker网络
docker network ls
docker network inspect temu-omni_temu-network

# 从Nginx测试后端连接
docker-compose -f docker-compose.prod.yml exec nginx wget -O- http://backend:8000/health
```

---

## 📞 获取帮助

如果诊断脚本无法解决问题，请提供以下信息：

1. 诊断脚本的完整输出
2. 容器状态: `docker-compose -f docker-compose.prod.yml ps`
3. 错误日志: `docker-compose -f docker-compose.prod.yml logs | tail -100`

---

*运行诊断脚本后，根据输出结果进行相应的修复。*


