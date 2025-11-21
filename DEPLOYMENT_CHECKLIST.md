# ✅ 生产环境部署检查清单

> 在部署到生产环境前，请确保完成以下所有检查项

---

## 🔒 环境变量配置（最重要！）

- [ ] `.env.production` 文件已创建
- [ ] `POSTGRES_PASSWORD` 已修改为强密码（至少16位）
- [ ] `REDIS_PASSWORD` 已修改为强密码（至少16位）
- [ ] `SECRET_KEY` 已生成（至少32位）
- [ ] `DEFAULT_ADMIN_USERNAME` 已设置
- [ ] `DEFAULT_ADMIN_PASSWORD` 已设置为强密码
- [ ] `DEFAULT_ADMIN_EMAIL` 已设置
- [ ] `TEMU_APP_KEY` 已填写（生产环境密钥）
- [ ] `TEMU_APP_SECRET` 已填写（生产环境密钥）
- [ ] `DOMAIN` 已设置为正确的域名
- [ ] 运行 `./verify-env.sh` 验证通过 ✅

### 快速生成密码：

```bash
# 数据库密码
openssl rand -base64 32

# Redis密码
openssl rand -base64 32

# Secret Key
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 📦 代码准备

- [ ] 已拉取/上传最新代码到服务器
- [ ] 已运行 `./clean-dev-files.sh` 清理开发文件
- [ ] `docker-compose.prod.yml` 所有服务都有 `env_file` 配置
- [ ] 确认 `deploy-production.sh` 有执行权限

---

## 🔧 服务器环境

- [ ] Docker 已安装（`docker --version`）
- [ ] Docker Compose 已安装（`docker compose version`）
- [ ] 服务器有足够的磁盘空间（至少20GB可用）
- [ ] 服务器有足够的内存（至少4GB）
- [ ] 80和443端口未被占用

---

## 🌐 网络配置

- [ ] 域名DNS已解析到服务器IP
- [ ] 防火墙已开放80端口（HTTP）
- [ ] 防火墙已开放443端口（HTTPS）
- [ ] 防火墙已开放22端口（SSH）

---

## 🔐 安全配置

### SSH安全
- [ ] 已配置SSH密钥认证
- [ ] 已禁用密码登录（可选但推荐）
- [ ] 已禁用root登录（可选但推荐）

### 防火墙
- [ ] UFW已安装并启用
- [ ] 只开放必要的端口（22, 80, 443）

### SSL证书（部署后配置）
- [ ] 已准备SSL证书（Let's Encrypt或其他）
- [ ] 或计划在部署后立即配置HTTPS

---

## 📋 部署步骤确认

### 第一步：环境检查
```bash
# 检查Docker
docker --version
docker compose version

# 检查端口占用
sudo netstat -tlnp | grep -E '80|443|5432|6379|8000'

# 检查磁盘空间
df -h

# 检查内存
free -h
```

### 第二步：配置验证
```bash
# 验证环境变量
./verify-env.sh
```

### 第三步：执行部署
```bash
# 一键部署
./deploy-production.sh
```

### 第四步：验证部署
```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 测试访问
curl http://localhost/
curl http://localhost/docs
```

---

## 🎯 部署后必做

### 立即执行（5分钟内）

- [ ] 访问前端页面，确认可以打开
- [ ] 使用配置的管理员账户登录
- [ ] **立即修改管理员密码**
- [ ] 检查所有容器状态为 `Up (healthy)`
- [ ] 查看后端日志，确认无错误

```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 查看后端日志
docker compose -f docker-compose.prod.yml logs backend | tail -50

# 测试登录
# 访问 http://YOUR_SERVER_IP/
# 使用 DEFAULT_ADMIN_USERNAME 和 DEFAULT_ADMIN_PASSWORD 登录
```

### 1小时内执行

- [ ] 配置SSL/HTTPS证书
- [ ] 测试HTTPS访问
- [ ] 配置自动证书续期

### 24小时内执行

- [ ] 设置数据库定期备份
- [ ] 配置监控和告警
- [ ] 测试完整的业务流程

---

## 📊 功能验证

### 基础功能
- [ ] 前端页面正常显示
- [ ] 用户登录正常
- [ ] API文档可访问（/docs）
- [ ] 健康检查正常（/health）

### 数据功能
- [ ] 可以添加店铺
- [ ] 可以同步订单
- [ ] 可以查看统计数据
- [ ] 可以导入数据（Excel/在线表格）

---

## 🔍 常见问题检查

### 如果前端无法访问

```bash
# 检查Nginx
docker compose -f docker-compose.prod.yml logs nginx

# 检查前端容器
docker compose -f docker-compose.prod.yml logs frontend

# 重启Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### 如果后端API报错

```bash
# 查看后端日志
docker compose -f docker-compose.prod.yml logs backend

# 检查数据库连接
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U temu_user -d temu_omni -c "SELECT 1;"

# 检查环境变量
docker compose -f docker-compose.prod.yml exec backend env | grep -E "SECRET_KEY|DATABASE_URL|ADMIN"
```

### 如果数据库连接失败

```bash
# 检查数据库状态
docker compose -f docker-compose.prod.yml ps postgres

# 查看数据库日志
docker compose -f docker-compose.prod.yml logs postgres

# 验证密码
docker compose -f docker-compose.prod.yml exec postgres env | grep POSTGRES_PASSWORD

# 对比 .env.production 中的密码
grep POSTGRES_PASSWORD .env.production
```

### 如果环境变量未生效

```bash
# 1. 确认 docker-compose.prod.yml 中有 env_file 配置
grep -n "env_file:" docker-compose.prod.yml
# 应该看到 4 处结果（postgres, redis, backend, frontend）

# 2. 检查 .env.production 文件权限
ls -la .env.production

# 3. 重新部署
./deploy-production.sh
```

---

## 📈 性能优化（可选）

部署稳定后，可以考虑以下优化：

- [ ] 配置CDN加速静态资源
- [ ] 启用HTTP/2
- [ ] 配置Gzip压缩（已在Nginx配置中）
- [ ] 数据库查询优化
- [ ] Redis缓存策略优化

---

## 🔄 定期维护

### 每日
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控磁盘使用

### 每周
- [ ] 备份数据库
- [ ] 检查SSL证书有效期
- [ ] 清理Docker未使用的资源

### 每月
- [ ] 更新系统和Docker
- [ ] 更新应用代码
- [ ] 审查安全配置
- [ ] 测试备份恢复

---

## 📞 问题反馈

如果部署过程中遇到问题：

1. **检查日志**：
   ```bash
   docker compose -f docker-compose.prod.yml logs > error.log
   ```

2. **运行诊断**：
   ```bash
   ./verify-env.sh
   ```

3. **收集信息**：
   - 服务状态：`docker compose -f docker-compose.prod.yml ps`
   - 系统信息：`uname -a`
   - Docker版本：`docker --version`

4. **参考文档**：
   - [生产环境部署指南](PRODUCTION_DEPLOYMENT.md)
   - [环境变量修复说明](ENV_VARIABLE_FIX.md)
   - [部署变更说明](DEPLOYMENT_CHANGES.md)

---

## ✅ 最终确认

在确认部署成功前，请验证：

- ✅ 所有容器状态为 `Up (healthy)`
- ✅ 前端页面可以正常访问
- ✅ 可以使用管理员账户登录
- ✅ API文档页面正常
- ✅ 数据库连接正常
- ✅ Redis缓存正常
- ✅ 环境变量正确读取
- ✅ 日志中无错误信息
- ✅ SSL/HTTPS已配置（或计划中）
- ✅ 备份策略已设置（或计划中）

---

**完成所有检查后，恭喜您成功部署到生产环境！** 🎉

