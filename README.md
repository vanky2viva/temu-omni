# Temu Omni - Temu 多店铺管理系统

> **项目状态**: 生产就绪  
> **版本**: v1.1.0  
> **最后更新**: 2025-01-XX

---

## 📋 项目概述

Temu Omni 是一个专业的 Temu 电商平台多店铺管理系统，提供订单管理、商品管理、数据分析、财务统计、AI运营助手等功能，支持多店铺统一管理。

### 核心特性

- ✅ **多店铺管理** - 支持管理多个 Temu 店铺，独立API配置
- ✅ **订单管理** - 订单同步、状态跟踪、成本计算、延误率分析
- ✅ **商品管理** - 商品信息管理、成本价格管理、SKU管理
- ✅ **数据分析** - 销售统计、GMV分析、利润分析、SKU排行、负责人业绩
- ✅ **财务统计** - 回款统计、成本利润分析、财务概览
- ✅ **AI运营助手 (FrogGPT)** - 智能数据分析、决策建议、备货计划制定
- ✅ **自动同步** - 定时自动同步订单和商品数据
- ✅ **成本计算** - 自动计算订单成本和利润
- ✅ **数据导入** - Excel/飞书表格批量导入商品成本数据

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy
- **任务调度**: APScheduler
- **异步**: asyncio, httpx
- **缓存**: Redis
- **AI集成**: OpenRouter API

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design + Ant Design X
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
- Redis 6+ (可选，用于缓存)
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
# 编辑 backend/.env，配置数据库、API密钥等

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
│   │   │   ├── frog_gpt.py   # FrogGPT AI模块
│   │   │   ├── inventory_planning.py  # 备货计划API
│   │   │   └── ...            # 其他API模块
│   │   ├── core/             # 核心功能（数据库、配置、调度器）
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   │   ├── frog_gpt_service.py  # AI服务
│   │   │   └── unified_statistics.py  # 统一统计服务
│   │   └── utils/            # 工具函数
│   ├── scripts/              # 脚本工具
│   ├── requirements.txt      # Python 依赖
│   └── Dockerfile.prod       # 生产环境 Dockerfile
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   │   ├── FrogGPT/    # FrogGPT AI助手页面
│   │   │   └── ...          # 其他页面
│   │   ├── components/      # 通用组件
│   │   └── services/        # API 服务
│   └── Dockerfile.prod       # 生产环境 Dockerfile
├── proxy-server/             # API 代理服务器
├── docs/                     # 项目文档
│   ├── README.md            # 文档索引
│   ├── FROGGPT.md           # FrogGPT使用指南
│   ├── guides/              # 快速开始指南
│   ├── deployment/          # 部署文档
│   └── import/              # 数据导入文档
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

# Redis配置（可选，用于缓存）
REDIS_URL=redis://redis:6379/0

# Temu API 配置
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret
TEMU_API_BASE_URL=https://agentpartner.temu.com/api

# Temu CN API 配置
TEMU_CN_APP_KEY=your_cn_app_key
TEMU_CN_APP_SECRET=your_cn_app_secret

# 代理服务器配置
TEMU_API_PROXY_URL=http://proxy-server:8001

# OpenRouter API配置（FrogGPT AI功能）
OPENROUTER_API_KEY=your_openrouter_api_key

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

## 🎯 核心功能

### 1. 订单管理
- 订单列表查看和筛选
- 订单状态跟踪
- 延误率分析
- 订单成本自动计算
- 订单详情查看

### 2. 商品管理
- 商品列表管理
- SKU管理（按extCode/SKU货号）
- 成本价格管理
- 商品状态管理

### 3. 数据分析
- 销售统计（GMV、订单数、利润）
- SKU销量排行
- 负责人业绩排行
- 每日/每周/每月趋势分析
- 延误率统计

### 4. 财务统计
- 回款统计（按日期、店铺）
- 成本利润分析
- 财务概览

### 5. AI运营助手 (FrogGPT) 🤖
- **智能对话**：自然语言交互，分析运营数据
- **数据分析**：深入分析GMV、订单、利润、延误率等关键指标
- **决策建议**：提供SKU优化、库存管理、价格策略等建议
- **备货计划**：根据回款和销量数据，自动生成未来一周/月的备货计划
- **文件上传**：支持上传图片、文档等文件进行分析
- **决策卡片**：可视化展示运营决策建议

详细使用指南请查看 [docs/FROGGPT.md](docs/FROGGPT.md)

### 6. 数据导入
- Excel批量导入商品成本
- 飞书表格在线导入
- 支持多种表格格式

---

## 📚 文档

详细文档请查看 [docs/README.md](docs/README.md)

### 快速链接

- 📖 [快速开始指南](docs/guides/QUICKSTART.md)
- 🚀 [生产环境部署](docs/deployment/PRODUCTION_DEPLOYMENT.md)
- ✅ [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md)
- 🤖 [FrogGPT使用指南](docs/FROGGPT.md)
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
- [x] 多店铺管理（独立API配置）
- [x] 订单管理（列表、详情、同步、延误率分析）
- [x] 商品管理（列表、成本价格、SKU管理）
- [x] 数据同步（订单、商品）
- [x] 订单成本计算
- [x] 销售统计分析
- [x] GMV 统计
- [x] 回款统计
- [x] SKU销量排行
- [x] 负责人业绩排行
- [x] 定时任务调度
- [x] Excel/飞书数据导入
- [x] API 代理服务器
- [x] **FrogGPT AI运营助手**
- [x] **备货计划制定**

### 🔄 持续优化

- [ ] 性能优化（缓存机制已部分实现）
- [ ] 更多数据分析功能
- [ ] Webhook 支持
- [ ] 移动端适配

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

4. **FrogGPT AI功能无法使用**
   - 检查 `OPENROUTER_API_KEY` 配置
   - 确认OpenRouter账户有足够余额
   - 查看后端日志了解详细错误

详细故障排查请查看相关文档。

---

## 📝 更新日志

### v1.1.0 (2025-01-XX)

- ✅ 新增 FrogGPT AI运营助手功能
- ✅ 新增备货计划制定功能（基于回款和销量数据）
- ✅ 统一数据统计服务，优化性能
- ✅ Redis缓存支持
- ✅ 优化数据一致性（统一统计口径）

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
- **OpenRouter**: https://openrouter.ai (FrogGPT AI功能)

---

*如有问题，请查看文档或提交 Issue。*
