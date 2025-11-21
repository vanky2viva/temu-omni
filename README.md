# Temu Omni - Temu 多店铺管理系统

> **项目状态**: 生产就绪  
> **版本**: v1.0.0  
> **最后更新**: 2025-11-21

---

## 📋 项目概述

Temu Omni 是一个专业的 Temu 电商平台多店铺管理系统，提供订单管理、商品管理、数据分析、财务统计等功能，支持多店铺统一管理。

### 核心特性

- ✅ **多店铺管理** - 支持管理多个 Temu 店铺
- ✅ **订单管理** - 订单同步、状态跟踪、成本计算
- ✅ **商品管理** - 商品信息管理、成本价格管理
- ✅ **数据分析** - 销售统计、GMV 分析、利润分析
- ✅ **自动同步** - 定时自动同步订单和商品数据
- ✅ **成本计算** - 自动计算订单成本和利润
- ✅ **回款统计** - 自动统计回款金额和日期

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy
- **任务调度**: APScheduler
- **异步**: asyncio, httpx

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design
- **状态管理**: React Query
- **图表**: ECharts

### 部署
- **容器化**: Docker, Docker Compose
- **Web 服务器**: Nginx
- **代理服务器**: FastAPI (独立服务)

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Docker & Docker Compose (推荐)

### 1. 克隆项目

```bash
git clone <repository-url>
cd temu-Omni
```

### 2. 配置环境变量

复制环境变量模板并配置：

```bash
# 后端配置
cp backend/env.template backend/.env
# 编辑 backend/.env，配置数据库、API 密钥等

# 生产环境配置
cp env.production.example .env.production
# 编辑 .env.production，配置生产环境变量
```

### 3. 启动服务（Docker Compose）

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. 初始化数据库

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 初始化数据库
python scripts/init_production_database.py

# 创建默认管理员用户
python scripts/init_default_user.py
```

### 5. 访问系统

- **前端**: http://localhost:3000 (或配置的域名)
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 📁 项目结构

```
temu-Omni/
├── backend/                    # 后端应用
│   ├── app/                   # 应用代码
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心功能（数据库、配置、调度器）
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   └── utils/            # 工具函数
│   ├── scripts/              # 脚本工具
│   │   ├── init_*.py        # 初始化脚本
│   │   ├── update_*.py      # 更新脚本
│   │   └── sync_*.py        # 同步脚本
│   ├── requirements.txt      # Python 依赖
│   └── Dockerfile.prod       # 生产环境 Dockerfile
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   └── services/        # API 服务
│   └── Dockerfile.prod       # 生产环境 Dockerfile
├── proxy-server/             # API 代理服务器
├── docs/                     # 项目文档
│   ├── README.md            # 文档索引
│   ├── guides/              # 快速开始指南
│   ├── deployment/          # 部署文档
│   └── import/              # 功能文档
├── docker-compose.prod.yml   # 生产环境 Docker Compose
└── README.md                 # 项目说明（本文件）
```

---

## ⚙️ 配置说明

### 环境变量配置

#### 后端配置 (`backend/.env`)

```env
# 应用配置
APP_NAME=Temu-Omni
SECRET_KEY=your-secret-key-here
DEBUG=False

# 数据库配置
DATABASE_URL=postgresql://user:password@postgres:5432/temu_omni

# Temu API 配置
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret
TEMU_API_BASE_URL=https://agentpartner.temu.com/api

# Temu CN API 配置
TEMU_CN_APP_KEY=your_cn_app_key
TEMU_CN_APP_SECRET=your_cn_app_secret

# 代理服务器配置
TEMU_API_PROXY_URL=http://proxy-server:8001

# 自动同步配置
AUTO_SYNC_ENABLED=True
SYNC_INTERVAL_MINUTES=30

# CORS 配置
CORS_ORIGINS=["https://your-domain.com"]
```

### 定时任务配置

系统自动运行以下定时任务：

| 任务 | 频率 | 说明 |
|-----|------|------|
| 订单同步 | 每30分钟 | 增量同步新订单 |
| 商品同步 | 每60分钟 | 增量同步商品更新 |
| 成本计算 | 每30分钟 | 计算订单成本和利润 |

---

## 📚 文档

详细文档请查看 [docs/README.md](docs/README.md)

### 快速链接

- 📖 [快速开始指南](docs/guides/QUICKSTART.md)
- 🚀 [生产环境部署](PRODUCTION_README.md)
- ✅ [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)
- 🔄 [数据同步策略](docs/SYNC_STRATEGY.md)
- 💰 [订单成本计算](docs/ORDER_COST_CALCULATION.md)
- 📊 [系统架构](docs/ARCHITECTURE.md)

---

## 🔧 常用命令

### Docker 管理

```bash
# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 数据库管理

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 初始化数据库
python scripts/init_production_database.py

# 更新订单成本
python scripts/update_order_costs.py

# 同步订单数据
python scripts/sync_shop_cli.py --shop-id 1
```

### 数据验证

```bash
# 验证订单金额和回款统计
python scripts/verify_order_amount_and_collection.py
```

---

## 🔐 安全说明

- 生产环境必须设置强密码的 `SECRET_KEY`
- 数据库密码应使用强密码
- API 密钥应妥善保管，不要提交到代码仓库
- 定期更新依赖包以修复安全漏洞

详细安全说明请查看 [SECURITY.md](SECURITY.md)

---

## 📊 功能清单

### ✅ 已实现功能

- [x] 用户认证和授权
- [x] 多店铺管理
- [x] 订单管理（列表、详情、同步）
- [x] 商品管理（列表、成本价格）
- [x] 数据同步（订单、商品）
- [x] 订单成本计算
- [x] 销售统计分析
- [x] GMV 统计
- [x] 回款统计
- [x] 定时任务调度
- [x] Excel 数据导入
- [x] API 代理服务器

### 🔄 持续优化

- [ ] 性能优化
- [ ] 缓存机制
- [ ] 更多数据分析功能
- [ ] Webhook 支持

---

## 🐛 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 配置
   - 确认 PostgreSQL 服务已启动
   - 检查网络连接

2. **API 同步失败**
   - 检查 Temu API 密钥配置
   - 确认代理服务器运行正常
   - 查看应用日志了解详细错误

3. **定时任务未执行**
   - 检查 `AUTO_SYNC_ENABLED` 配置
   - 查看调度器状态：`GET /api/system/scheduler/status`
   - 查看应用启动日志

详细故障排查请查看相关文档。

---

## 📝 更新日志

### v1.0.0 (2025-11-21)

- ✅ 完成数据同步功能
- ✅ 实现订单成本自动计算
- ✅ 添加定时任务调度
- ✅ 完善数据验证功能
- ✅ 优化文档结构

完整更新日志请查看 [docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## 📄 许可证

[添加许可证信息]

---

## 👥 贡献

欢迎提交 Issue 和 Pull Request。

---

## 🔗 相关链接

- **Temu 合作伙伴平台**: https://partner-us.temu.com
- **项目文档**: [docs/README.md](docs/README.md)

---

*如有问题，请查看文档或提交 Issue。*
