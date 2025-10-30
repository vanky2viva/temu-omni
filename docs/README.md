# 📚 Temu-Omni 文档中心

欢迎来到 Temu-Omni 项目文档中心！

## 🎯 快速导航

### 🌟 推荐起点
- **[📑 完整文档索引 (INDEX.md)](./INDEX.md)** ⭐⭐⭐ - 推荐从这里开始！
- **[📖 项目主页 (README.md)](../README.md)** - 项目概览和快速开始

---

## 📂 文档分类

### 🔌 API集成 (10个文档)
> API相关的集成、测试和开发文档

**快速入口**: [api/QUICKSTART_API.md](./api/QUICKSTART_API.md)

主要文档：
- API快速接入
- Temu API完整指南
- API测试指南
- 开发者文档

📁 **完整列表**: [docs/api/](./api/)

---

### 📥 数据导入 (7个文档)
> Excel和在线表格导入功能文档

**快速入口**: [import/三种表格字段映射说明.md](./import/三种表格字段映射说明.md) ⭐⭐⭐

主要文档：
- 三种表格字段映射说明
- Excel导入功能使用指南
- 在线表格导入功能说明
- 密码保护功能说明

📁 **完整列表**: [docs/import/](./import/)

---

### 🚀 部署运维 (4个文档)
> 部署、配置和运维相关文档

**快速入口**: [deployment/DEPLOY_QUICKSTART.md](./deployment/DEPLOY_QUICKSTART.md)

主要文档：
- 快速部署指南
- 详细部署说明
- 导入功能部署

📁 **完整列表**: [docs/deployment/](./deployment/)

---

### 🎯 开发指南 (5个文档)
> 面向开发者的使用和集成指南

**快速入口**: [guides/QUICKSTART.md](./guides/QUICKSTART.md)

主要文档：
- 快速入门教程
- 前端集成指南
- 集成开发指南
- Docker快速开始

📁 **完整列表**: [docs/guides/](./guides/)

---

### 📖 核心文档 (17个文档)
> 系统架构、数据库、API参考等核心文档

**主要文档**:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构设计
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - 数据库表结构
- [TEMU_API_GUIDE.md](./TEMU_API_GUIDE.md) - Temu API指南
- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) - Docker使用指南
- [API.md](./API.md) - API接口文档
- [API_DATA_MAPPING.md](./API_DATA_MAPPING.md) - API数据映射
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 生产环境部署
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - 项目状态
- [FEATURES.md](./FEATURES.md) - 功能特性
- [CHANGELOG.md](./CHANGELOG.md) - 版本更新日志

---

## 🎓 按用户类型推荐

### 👤 新用户
```
1. README.md - 了解项目
   ↓
2. deployment/DEPLOY_QUICKSTART.md - 快速部署
   ↓
3. guides/QUICKSTART.md - 快速入门
   ↓
4. import/Excel导入功能使用指南.md - 导入数据

### 🔑 授权与店铺配置（更新）
- 新增店铺时无需填写 Access Token，可先创建
- 在“店铺管理”列表中点击“授权/更新授权”按钮设置 Access Token
- 授权接口：`POST /api/shops/{shop_id}/authorize`（请求体：`{ access_token: "..." }`）
```

### 👨‍💻 开发者
```
1. ARCHITECTURE.md - 理解架构
   ↓
2. DATABASE_SCHEMA.md - 了解数据结构
   ↓
3. api/QUICKSTART_API.md - API接入
   ↓
4. guides/FRONTEND_INTEGRATION.md - 前端开发
```

### 🔧 运维人员
```
1. deployment/DEPLOYMENT_GUIDE.md - 部署配置
   ↓
2. DOCKER_GUIDE.md - Docker运维
   ↓
3. deployment/DEPLOYMENT_IMPORT.md - 功能部署
```

---

## 🔍 快速搜索

### 按功能
- **部署**: deployment/, DOCKER_GUIDE.md, DEPLOYMENT.md
- **API**: api/, TEMU_API_GUIDE.md, API.md
- **导入**: import/, 三种表格字段映射说明.md
- **数据库**: DATABASE_SCHEMA.md
- **架构**: ARCHITECTURE.md

### 按技术
- **Docker**: DOCKER_GUIDE.md, deployment/
- **PostgreSQL**: DATABASE_SCHEMA.md
- **FastAPI**: api/, ARCHITECTURE.md
- **React**: guides/FRONTEND_INTEGRATION.md
- **Excel/飞书**: import/

---

## 📊 文档统计

```
总计: 43个文档文件

分类:
├── api/         - 10个文档 (API集成)
├── import/      - 7个文档  (数据导入)
├── deployment/  - 4个文档  (部署运维)
├── guides/      - 5个文档  (开发指南)
└── 根目录        - 17个文档 (核心参考)
```

---

## 📝 文档维护

### 文档版本
- **文档体系版本**: v2.0
- **最后更新**: 2025-10-30
- **维护状态**: ✅ 活跃维护

### 贡献指南
1. 新文档放入相应分类目录
2. 在 INDEX.md 中添加索引
3. 重要文档标注 ⭐
4. 更新文档整理说明

### 相关文档
- [文档整理说明](./文档整理说明.md) - 文档整理过程记录
- [INDEX.md](./INDEX.md) - 完整文档索引

---

## 🆘 获取帮助

### 找不到需要的文档？
1. 查看 [INDEX.md](./INDEX.md) 完整索引
2. 使用关键词搜索
3. 查看 [PROJECT_STATUS.md](./PROJECT_STATUS.md) 了解项目状态

### 文档有问题？
1. 提交 Issue 反馈
2. 发送 Pull Request 改进
3. 联系项目维护者

---

## 📖 开始阅读

**[👉 查看完整文档索引 (INDEX.md)](./INDEX.md)**

---

*让我们开始探索 Temu-Omni 的文档吧！* 🚀

