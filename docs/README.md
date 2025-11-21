# Temu Omni 项目文档

## 📚 文档索引

### 🚀 快速开始
- [快速开始指南](guides/QUICKSTART.md) - 项目快速启动指南
- [部署指南](deployment/PRODUCTION_DEPLOYMENT.md) - 生产环境部署指南
- [Docker 部署指南](DOCKER_GUIDE.md) - Docker 容器化部署

### 📖 核心文档
- [系统架构](ARCHITECTURE.md) - 系统整体架构设计
- [数据库设计](DATABASE_SCHEMA.md) - 数据库表结构设计
- [API 文档](API.md) - API 接口文档
- [Temu API 集成指南](TEMU_API_GUIDE.md) - Temu API 集成说明

### 🔄 数据同步
- [数据同步策略](SYNC_STRATEGY.md) - 订单和商品同步策略
- [数据更新机制](DATA_UPDATE_STRATEGY.md) - 数据自动更新说明
- [数据验证指南](VERIFY_ORDER_AMOUNT_AND_COLLECTION.md) - 数据验证方法

### 💰 订单成本
- [订单成本计算](ORDER_COST_CALCULATION.md) - 订单成本计算逻辑
- [订单商品匹配](backend/docs/ORDER_PRODUCT_MATCHING.md) - 订单与商品匹配规则

### 📊 功能说明
- [Excel 导入功能](import/Excel导入功能使用指南.md) - Excel 数据导入使用指南
- [代理服务器配置](PROXY_SETUP.md) - API 代理服务器配置

### 🔧 开发文档
- [API 数据映射](API_DATA_MAPPING.md) - Temu API 数据字段映射
- [CN 端点支持](CN_ENDPOINT_SUPPORT.md) - 中国区 API 端点支持

### 📝 更新日志
- [更新日志](CHANGELOG.md) - 项目更新历史

---

## 📁 文档结构

```
docs/
├── README.md                    # 文档索引（本文件）
├── guides/                      # 快速开始指南
│   ├── QUICKSTART.md
│   └── INTEGRATION_GUIDE.md
├── deployment/                  # 部署相关文档
│   ├── PRODUCTION_DEPLOYMENT.md
│   └── DEPLOYMENT_GUIDE.md
├── import/                      # 导入功能文档
│   └── Excel导入功能使用指南.md
├── api/                         # API 相关文档
│   └── README_API_INTEGRATION.md
└── backend/docs/                # 后端技术文档
    ├── ORDER_PRODUCT_MATCHING.md
    └── MATCHING_STRATEGY_FINAL.md
```

---

## 🔍 快速查找

### 部署相关
- 生产环境部署 → [deployment/PRODUCTION_DEPLOYMENT.md](deployment/PRODUCTION_DEPLOYMENT.md)
- Docker 部署 → [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- 代理服务器 → [PROXY_SETUP.md](PROXY_SETUP.md)

### 数据相关
- 数据同步 → [SYNC_STRATEGY.md](SYNC_STRATEGY.md)
- 数据验证 → [VERIFY_ORDER_AMOUNT_AND_COLLECTION.md](VERIFY_ORDER_AMOUNT_AND_COLLECTION.md)
- 订单成本 → [ORDER_COST_CALCULATION.md](ORDER_COST_CALCULATION.md)

### 开发相关
- API 集成 → [TEMU_API_GUIDE.md](TEMU_API_GUIDE.md)
- 系统架构 → [ARCHITECTURE.md](ARCHITECTURE.md)
- 数据库设计 → [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

---

*最后更新: 2025-11-21*
