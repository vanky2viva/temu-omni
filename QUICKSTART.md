# 🚀 快速启动指南

5分钟快速启动Luffy store Omni多店铺管理系统。

## 📋 前置要求

- ✅ Docker Desktop（Mac/Windows）或 Docker Engine（Linux）
- ✅ 至少2GB可用内存
- ✅ 端口 8001、8000、5432、6379 未被占用

## 🎯 快速启动（3步）

### 步骤1：启动服务

```bash
cd /path/to/temu-Omni

# 启动所有服务（后端、前端、数据库、Redis）
docker compose up -d

# 等待服务启动完成（约30秒）
sleep 30
```

### 步骤2：初始化数据

```bash
# 初始化数据库表结构
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 生成演示数据（可选但推荐）
docker compose exec backend python scripts/generate_demo_data.py
```

### 步骤3：访问系统

打开浏览器访问：**http://localhost:8001**

🎉 完成！现在可以使用系统了！

---

## 📊 演示数据说明

如果执行了演示数据生成，系统会包含：

- **3个演示店铺** (US、UK、DE)
- **45个商品** (包含价格和成本)
- **450个订单** (最近90天)
- **15个活动**
- **10位负责人** (张三、李四、王五等)
- **完整财务数据** (GMV $74K+, 利润 $33K+)

## 🔑 API配置流程（可选）

如果需要连接真实的Temu店铺数据：

### 1. 配置应用凭证（一次性）

1. 访问 **http://localhost:8001/settings**
2. 填写从Temu开放平台获取的：
   - App Key
   - App Secret
3. 点击"保存配置"

### 2. 添加店铺

1. 访问 **http://localhost:8001/shops**
2. 点击"添加店铺"
3. 填写店铺信息：
   ```
   店铺ID: YOUR_SHOP_ID
   店铺名称: 店铺名称
   地区: US/UK/DE等
   经营主体: 公司名称（可选）
   Access Token: 店铺授权后获得的Token
   ```
4. 点击"确定"

### 3. 同步数据

添加店铺后，系统会自动同步：
- 订单数据
- 商品数据
- 销售数据

## 🗂 系统页面导航

| 页面 | 路径 | 功能 |
|------|------|------|
| 仪表板 | `/dashboard` | 总览数据、趋势图表 |
| 店铺管理 | `/shops` | 添加/管理店铺、配置Token |
| 订单管理 | `/orders` | 查看订单、筛选、详情 |
| 商品管理 | `/products` | 管理商品、录入成本 |
| 数据统计 | `/statistics` | 多维度统计分析 |
| GMV表格 | `/gmv-table` | 表格形式查看GMV |
| SKU分析 | `/sku-analysis` | SKU销量对比排行 |
| 爆单榜 | `/hot-seller` | 负责人业绩排行 |
| 系统设置 | `/settings` | 配置App Key/Secret |

## 🔧 常用操作

### 查看服务状态

```bash
docker compose ps
```

应该看到4个服务都是"Up"状态：
```
temu-omni-backend    Up
temu-omni-frontend   Up
temu-omni-postgres   Up (healthy)
temu-omni-redis      Up (healthy)
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 只看后端日志
docker compose logs -f backend

# 只看前端日志
docker compose logs -f frontend

# 查看最近20条日志
docker compose logs --tail=20
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart frontend
docker compose restart backend
```

### 停止服务

```bash
# 停止所有服务（保留数据）
docker compose stop

# 停止并删除容器（保留数据）
docker compose down

# 停止并删除所有数据
docker compose down -v
```

### 完全重置

```bash
# 停止并删除所有内容
docker compose down -v

# 重新启动
docker compose up -d

# 重新初始化
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
docker compose exec backend python scripts/generate_demo_data.py
```

## 🐛 故障排查

### 问题1：端口被占用

**错误提示**: `port is already allocated`

**解决方案**:
```bash
# 修改 docker-compose.yml 中的端口映射
# 例如将 8001:5173 改为 8002:5173

# 或停止占用端口的程序
lsof -i :8001  # 查找占用8001端口的进程
kill -9 <PID>  # 停止该进程
```

### 问题2：前端页面空白或报错

**解决方案**:
```bash
# 1. 强制刷新浏览器
Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)

# 2. 清除浏览器缓存

# 3. 使用无痕模式访问

# 4. 重启前端服务
docker compose restart frontend
```

### 问题3：无数据显示

**解决方案**:
```bash
# 重新生成演示数据
docker compose exec backend python scripts/generate_demo_data.py

# 刷新浏览器
```

### 问题4：数据库连接失败

**解决方案**:
```bash
# 检查PostgreSQL状态
docker compose ps postgres

# 重启数据库
docker compose restart postgres

# 等待30秒后重新初始化
sleep 30
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 问题5：API返回500错误

**解决方案**:
```bash
# 查看后端日志
docker compose logs backend --tail=50

# 重启后端
docker compose restart backend

# 检查数据库表是否创建
docker compose exec postgres psql -U temu_user -d temu_omni -c "\dt"
```

## 📱 访问地址汇总

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:8001 | 主要使用界面 |
| 后端API | http://localhost:8000 | API服务 |
| API文档 | http://localhost:8000/docs | Swagger文档 |
| 数据库 | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | 缓存服务 |

## 💡 使用建议

### 首次使用

1. ✅ 先查看演示数据了解系统功能
2. ✅ 熟悉各个页面和功能模块
3. ✅ 测试筛选、排序、查询等功能
4. ✅ 再配置真实的API凭证

### 日常使用

1. 📊 每天查看仪表板了解整体业绩
2. 🏆 查看爆单榜了解团队表现
3. 📈 使用GMV表格分析趋势
4. 🎯 通过SKU分析优化选品

### 数据管理

1. 💾 定期备份数据库
2. 🔄 及时更新店铺Token
3. 📝 为商品录入准确成本
4. 👥 维护负责人与SKU的绑定关系

## 🔄 更新系统

```bash
# 停止服务
docker compose down

# 拉取最新代码（如果使用Git）
git pull

# 重新构建镜像
docker compose build

# 启动服务
docker compose up -d

# 更新数据库结构（如果有变更）
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## 📚 更多文档

- **完整文档**: 查看 [README.md](README.md)
- **API文档**: http://localhost:8000/docs
- **Docker指南**: [README_DOCKER.md](README_DOCKER.md)
- **功能说明**: [FEATURES.md](FEATURES.md)

## ✅ 检查清单

使用前确认：

- [ ] Docker服务正常运行
- [ ] 端口8001、8000、5432、6379未被占用
- [ ] 至少2GB可用内存
- [ ] 执行了 `docker compose up -d`
- [ ] 执行了数据库初始化
- [ ] 生成了演示数据（推荐）
- [ ] 浏览器访问 http://localhost:8001 正常

## 🎯 下一步

系统启动成功后，建议：

1. 浏览各个功能模块
2. 查看演示数据了解系统能力
3. 阅读完整README了解详细功能
4. 准备Temu API凭证用于真实数据同步

---

**需要帮助？** 查看 [常见问题](#-故障排查) 或提交 Issue

**最后更新**: 2025-10-29
