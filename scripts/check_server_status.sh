#!/bin/bash
# 服务器状态检查脚本

echo "=========================================="
echo "🔍 服务器状态检查"
echo "=========================================="
echo ""

# 1. 检查Docker服务状态
echo "1. Docker 容器状态:"
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml ps
echo ""

# 2. 检查端口监听
echo "2. 端口监听状态:"
echo "----------------------------------------"
echo "检查 80 端口:"
sudo netstat -tlnp | grep :80 || ss -tlnp | grep :80
echo ""
echo "检查 443 端口:"
sudo netstat -tlnp | grep :443 || ss -tlnp | grep :443
echo ""
echo "检查 8000 端口（后端）:"
sudo netstat -tlnp | grep :8000 || ss -tlnp | grep :8000
echo ""

# 3. 检查防火墙
echo "3. 防火墙状态:"
echo "----------------------------------------"
sudo ufw status || echo "ufw 未安装或未启用"
echo ""

# 4. 检查Nginx配置
echo "4. Nginx 配置测试:"
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml exec nginx nginx -t 2>&1 || echo "Nginx 容器未运行"
echo ""

# 5. 检查服务日志（最后10行）
echo "5. Nginx 日志（最后10行）:"
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml logs --tail=10 nginx 2>&1 || echo "无法获取日志"
echo ""

echo "6. 后端服务日志（最后10行）:"
echo "----------------------------------------"
docker-compose -f docker-compose.prod.yml logs --tail=10 backend 2>&1 || echo "无法获取日志"
echo ""

# 6. 测试本地连接
echo "7. 本地连接测试:"
echo "----------------------------------------"
echo "测试 Nginx:"
curl -I http://localhost 2>&1 | head -5
echo ""
echo "测试后端 API:"
curl -I http://localhost/api/health 2>&1 | head -5
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="


