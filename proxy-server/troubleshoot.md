# 代理服务器故障排查指南

## 问题：Empty reply from server

当 `curl http://172.236.231.45:8001/health` 返回 "Empty reply from server" 时，可能的原因和解决方法：

### 1. 检查容器状态

SSH 到服务器后执行：

```bash
# 检查容器是否运行
docker ps | grep temu-api-proxy

# 如果容器未运行，查看所有容器（包括停止的）
docker ps -a | grep temu-api-proxy

# 查看容器日志
docker logs temu-api-proxy --tail 50
```

**如果容器未运行**：
```bash
# 启动容器
docker start temu-api-proxy

# 或重新创建并启动
cd /opt/proxy-server
docker-compose up -d
```

### 2. 检查端口映射

```bash
# 检查端口是否监听
netstat -tlnp | grep 8001
# 或
ss -tlnp | grep 8001

# 检查容器端口映射
docker port temu-api-proxy
```

**如果端口未监听**，检查 `docker-compose.yml` 或启动命令中的端口映射：
```yaml
ports:
  - "8001:8001"  # 确保格式正确
```

### 3. 检查容器内部服务

```bash
# 进入容器检查
docker exec -it temu-api-proxy /bin/bash

# 在容器内测试
curl http://localhost:8001/health

# 检查进程
ps aux | grep uvicorn
```

**如果容器内服务无响应**：
- 检查应用是否正常启动
- 查看容器日志：`docker logs temu-api-proxy`
- 检查环境变量是否正确设置

### 4. 检查防火墙

```bash
# CentOS/RHEL
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=8001/tcp --permanent
sudo firewall-cmd --reload

# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8001/tcp
```

### 5. 检查 Docker 网络

```bash
# 检查容器网络
docker inspect temu-api-proxy | grep -A 20 "NetworkSettings"

# 检查端口绑定
docker inspect temu-api-proxy | grep -A 10 "Ports"
```

### 6. 重新部署

如果以上方法都不行，尝试重新部署：

```bash
# 停止并删除容器
docker stop temu-api-proxy
docker rm temu-api-proxy

# 重新构建和启动
cd /opt/proxy-server
docker-compose down
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 7. 使用检查脚本

在服务器上运行检查脚本：

```bash
# 上传 check_status.sh 到服务器
scp proxy-server/check_status.sh root@172.236.231.45:/opt/proxy-server/

# SSH 到服务器执行
ssh root@172.236.231.45
cd /opt/proxy-server
chmod +x check_status.sh
./check_status.sh
```

## 常见错误和解决方案

### 错误 1: 容器启动后立即退出

**原因**：应用启动失败

**解决**：
```bash
# 查看详细日志
docker logs temu-api-proxy

# 检查环境变量
docker exec temu-api-proxy env | grep TEMU

# 手动启动测试
docker run -it --rm \
  -p 8001:8001 \
  -e TEMU_APP_KEY=your_key \
  -e TEMU_APP_SECRET=your_secret \
  temu-api-proxy:latest
```

### 错误 2: 端口被占用

**原因**：8001 端口已被其他服务使用

**解决**：
```bash
# 查找占用端口的进程
lsof -i :8001
# 或
netstat -tlnp | grep 8001

# 修改 docker-compose.yml 使用其他端口
ports:
  - "8002:8001"  # 使用 8002 端口
```

### 错误 3: 无法从外部访问

**原因**：防火墙或安全组未开放端口

**解决**：
1. 检查服务器防火墙规则
2. 检查云服务商安全组设置（如阿里云、腾讯云等）
3. 确保端口已开放

### 错误 4: 连接超时

**原因**：网络问题或服务未启动

**解决**：
```bash
# 测试本地连接
curl http://localhost:8001/health

# 测试容器内连接
docker exec temu-api-proxy curl http://localhost:8001/health

# 检查网络连接
ping 172.236.231.45
telnet 172.236.231.45 8001
```

## 快速修复命令

```bash
# 一键重启服务
docker restart temu-api-proxy

# 查看实时日志
docker logs -f temu-api-proxy

# 重新部署
cd /opt/proxy-server
docker-compose down
docker-compose up -d --build
docker-compose logs -f
```




