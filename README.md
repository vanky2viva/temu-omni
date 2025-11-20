# Temu Omni - Temu 多店铺管理系统

> **项目状态**: 开发中  
> **最后更新**: 2025-11-20

---

## 📋 项目概述

Temu Omni 是一个 Temu 电商平台管理系统，提供订单管理、商品管理、数据分析等功能，支持多店铺管理。

---

## ✨ 主要功能

### 1. 订单管理
- ✅ 订单列表查询
- ✅ 订单详情查看
- ✅ 订单状态跟踪
- ✅ 订单数据同步

### 2. 商品管理
- ✅ 商品列表查看
- ⏸️ 商品数据同步（等待 API 权限）

### 3. 数据同步
- ✅ 订单数据同步
- ✅ 支持增量同步和全量同步
- ✅ 自动同步任务

### 4. API 代理服务器
- ✅ 独立的 API 代理服务器
- ✅ 支持多区域（US/EU/Global）
- ✅ 白名单 IP 支持
- ✅ Docker 容器化部署

---

## 🏗️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL（统一使用，不再支持 SQLite）
- **ORM**: SQLAlchemy
- **异步**: asyncio, httpx

### 前端
- **框架**: React + TypeScript
- **UI 库**: Ant Design

### 部署
- **容器化**: Docker, Docker Compose
- **代理服务器**: FastAPI (独立服务)

---

## 📁 项目结构

```
temu-Omni/
├── backend/              # 后端应用
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务服务
│   │   └── temu/        # Temu API 客户端
│   └── requirements.txt
├── frontend/            # 前端应用
├── proxy-server/        # API 代理服务器
│   ├── app/
│   │   └── main.py
│   └── README.md
├── docs/                # 项目文档
│   ├── ORDER_LIST_FIELDS.md
│   ├── PROJECT_PROGRESS.md
│   └── API_INTEGRATION_PLAN.md
└── README.md
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 18+
- Docker (可选)

### 2. 数据库初始化

**重要**：项目统一使用 PostgreSQL 数据库。

```bash
# 启动 PostgreSQL（如果使用 Docker Compose）
docker-compose up -d postgres

# 初始化数据库（创建表结构并添加 CN 字段）
cd backend
python3 scripts/init_postgres_with_cn_fields.py
```

### 3. 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 5. 代理服务器部署

```bash
cd proxy-server
docker-compose up -d
```

详细部署说明请参考 `proxy-server/README.md`

---

## 📚 文档

- **项目进度**: [docs/PROJECT_PROGRESS.md](docs/PROJECT_PROGRESS.md)
- **系统集成 API 计划**: [docs/API_INTEGRATION_PLAN.md](docs/API_INTEGRATION_PLAN.md)
- **订单字段说明**: [docs/ORDER_LIST_FIELDS.md](docs/ORDER_LIST_FIELDS.md)
- **代理服务器文档**: [proxy-server/README.md](proxy-server/README.md)
- **清理总结**: [docs/CLEANUP_SUMMARY.md](docs/CLEANUP_SUMMARY.md)

---

## 🔑 配置

### 环境变量

创建 `.env` 文件：

```bash
# 应用配置
SECRET_KEY=your_secret_key
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///./temu_omni.db

# Temu API 配置
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret
TEMU_API_BASE_URL=https://openapi-b-us.temu.com/openapi/router

# 代理服务器配置（可选）
TEMU_API_PROXY_URL=http://172.236.231.45:8001
```

---

## 🧪 测试

### API 测试

```bash
# 测试代理服务器
curl http://172.236.231.45:8001/health

# 测试订单同步
curl -X POST http://localhost:8000/api/sync/shops/1/orders
```

---

## 📊 当前状态

### ✅ 已完成
- API 代理服务器部署
- 订单管理 API
- 订单数据同步
- 后端基础框架
- 前端基础框架

### ⏸️ 暂时搁置
- 商品列表 API（等待应用配置解决）

### 📋 进行中
- 系统集成 API 开发
- 数据同步优化
- Webhook 集成

---

## 🔗 相关链接

- **Temu 合作伙伴平台**: https://partner-us.temu.com
- **API 文档**: `temu-partner-documentation.md`

---

## 📝 更新日志

### 2025-11-20
- ✅ 完成项目清理和归档
- ✅ 创建项目进度文档
- ✅ 创建系统集成 API 开发计划
- ✅ 代理服务器支持多区域

---

*更多信息请查看 [docs/PROJECT_PROGRESS.md](docs/PROJECT_PROGRESS.md)*
