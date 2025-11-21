# 生产环境部署检查清单

## 📋 部署前检查

### 1. 环境配置

- [ ] 配置生产环境变量文件 `.env.production`
- [ ] 设置强密码的 `SECRET_KEY`
- [ ] 配置正确的数据库连接 `DATABASE_URL`
- [ ] 配置 Temu API 密钥（`TEMU_APP_KEY`, `TEMU_APP_SECRET`）
- [ ] 配置 Temu CN API 密钥（如需要）
- [ ] 配置代理服务器地址 `TEMU_API_PROXY_URL`
- [ ] 配置 CORS 允许的域名
- [ ] 设置 `DEBUG=False`

### 2. 数据库准备

- [ ] PostgreSQL 数据库已创建
- [ ] 数据库用户权限已配置
- [ ] 数据库备份策略已制定
- [ ] 执行数据库初始化脚本
- [ ] 创建默认管理员用户

### 3. 服务配置

- [ ] Docker 和 Docker Compose 已安装
- [ ] 代理服务器已部署并运行
- [ ] Nginx 配置已更新（如使用）
- [ ] SSL 证书已配置（如使用 HTTPS）

### 4. 定时任务

- [ ] 确认 `AUTO_SYNC_ENABLED=True`
- [ ] 配置合适的同步间隔 `SYNC_INTERVAL_MINUTES`
- [ ] 验证调度器在应用启动时正常启动

### 5. 安全设置

- [ ] 所有敏感信息已从代码中移除
- [ ] 环境变量文件已添加到 `.gitignore`
- [ ] 数据库密码使用强密码
- [ ] API 密钥已妥善保管
- [ ] 防火墙规则已配置

### 6. 监控和日志

- [ ] 日志目录已创建并配置权限
- [ ] 日志轮转策略已配置
- [ ] 监控告警已配置（如需要）

---

## 🚀 部署步骤

### 1. 准备环境

```bash
# 克隆代码
git clone <repository-url>
cd temu-Omni

# 配置环境变量
cp env.production.example .env.production
# 编辑 .env.production

cp backend/env.template backend/.env
# 编辑 backend/.env
```

### 2. 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 3. 初始化数据库

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 初始化数据库
python scripts/init_production_database.py

# 创建默认管理员用户
python scripts/init_default_user.py
```

### 4. 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查调度器状态
curl -X GET "http://localhost:8000/api/system/scheduler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 验证数据同步
python scripts/verify_order_amount_and_collection.py
```

---

## ✅ 部署后验证

### 功能验证

- [ ] 用户登录功能正常
- [ ] 店铺管理功能正常
- [ ] 订单列表可以正常显示
- [ ] 商品列表可以正常显示
- [ ] 数据同步功能正常
- [ ] 定时任务正常运行
- [ ] 订单成本计算正常
- [ ] 统计数据正常显示

### 性能验证

- [ ] API 响应时间正常
- [ ] 数据库查询性能正常
- [ ] 前端页面加载速度正常

---

## 🔧 维护操作

### 日常维护

```bash
# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 更新订单成本
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/update_order_costs.py
```

### 数据备份

```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U temu_user temu_omni > backup_$(date +%Y%m%d).sql
```

---

## 📞 故障处理

### 常见问题

1. **服务无法启动**
   - 检查 Docker 服务状态
   - 查看容器日志
   - 检查端口占用

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查网络连接

3. **定时任务未执行**
   - 检查调度器状态
   - 查看应用日志
   - 验证配置是否正确

---

*部署完成后，请定期检查系统运行状态和日志。*

