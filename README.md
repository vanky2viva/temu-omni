# Luffy store Omni - 多店铺管理系统

一个功能完整的Temu跨境电商多店铺管理系统，支持多地区、多主体店铺的数据统一管理和分析。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [API配置说明](#api配置说明)
- [数据导入](#数据导入)
- [功能模块](#功能模块)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [完整文档](#完整文档)

## ✨ 功能特性

### 核心功能
- ✅ **多店铺管理** - 支持管理多个地区、多个经营主体的店铺
- ✅ **订单管理** - 统一查看和管理所有店铺的订单
- ✅ **商品管理** - 商品信息管理，支持成本录入和利润计算
- ✅ **数据统计** - 多维度数据统计和趋势分析
- ✅ **GMV分析** - 按日/周/月查看GMV、利润等财务数据
- ✅ **SKU分析** - SKU销量对比和排行榜
- ✅ **爆单榜** - 负责人业绩排行，SKU与人员绑定管理

### 数据获取方式
- ✅ **API同步** - 从Temu OpenAPI自动同步订单、商品、活动数据
- ✅ **Excel导入** - 支持本地Excel文件批量导入
- ✅ **在线表格导入** - 支持飞书在线表格实时同步（支持密码保护）
- ✅ **智能字段映射** - 自动识别多种列名格式

### 系统特性
- ✅ **应用级API配置** - App Key和App Secret全局配置
- ✅ **店铺级授权** - 每个店铺独立配置Access Token
- ✅ **演示数据** - 内置演示数据生成器，快速体验系统功能
- ✅ **Docker部署** - 一键启动，包含前端、后端、数据库、Redis
- ✅ **响应式设计** - 适配各种屏幕尺寸

## 🛠 技术栈

### 后端
- **框架**: FastAPI (Python 3.9+)
- **数据库**: PostgreSQL 13
- **ORM**: SQLAlchemy
- **缓存**: Redis
- **数据分析**: Pandas
- **日志**: Loguru

### 前端
- **框架**: React 18 + TypeScript
- **UI组件**: Ant Design
- **图表**: ECharts
- **状态管理**: React Query + Zustand
- **构建工具**: Vite

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Vite开发服务器（开发）/ Nginx（生产）

## 🚀 快速开始

### 前置要求
- Docker Desktop 或 Docker Engine + Docker Compose
- 至少2GB可用内存

### 1. 启动系统

```bash
cd /path/to/temu-Omni

# 启动所有服务
docker compose up -d

# 等待服务启动（约30秒）
sleep 30

# 初始化数据库（首次启动）
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 生成演示数据
docker compose exec backend python scripts/generate_demo_data.py
```

### 2. 访问系统

- **前端界面**: http://localhost:8001
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 3. 配置应用凭证（首次使用）

1. 访问 http://localhost:8001/settings
2. 填写Temu应用的App Key和App Secret
3. 点击"保存配置"

> **注意**: 如果暂时没有真实凭证，可以跳过此步骤，不影响查看演示数据。

### 4. 添加店铺

1. 访问 http://localhost:8001/shops
2. 点击"添加店铺"
3. 填写店铺信息和Access Token
4. 点击"确定"

## 🔑 API配置说明

### 两级配置架构

本系统采用**应用级 + 店铺级**的两级配置架构：

#### 1. 应用级配置（全局）
- **配置位置**: 系统设置（/settings）
- **配置内容**: 
  - App Key
  - App Secret
- **说明**: 从Temu开放平台申请的应用凭证，一个应用可以管理多个店铺

#### 2. 店铺级配置（独立）
- **配置位置**: 店铺管理 - 添加/编辑店铺
- **配置内容**:
  - Access Token（店铺授权令牌）
- **说明**: 每个店铺需要单独授权获取Token

### 配置流程

```
1. Temu开放平台申请应用
   ↓
2. 获得 App Key + App Secret
   ↓
3. 在【系统设置】中配置应用凭证
   ↓
4. 店铺授权获得 Access Token
   ↓
5. 在【店铺管理】中添加店铺并填写Token
   ↓
6. 开始同步数据
```

### 获取凭证

访问 [Temu开放平台](https://agentpartner.temu.com/) 进行：
1. 应用注册 - 获取App Key和App Secret
2. 店铺授权 - 获取Access Token

## 📥 数据导入

除了API同步外，系统还支持通过Excel文件和在线表格导入数据。

### 支持的数据类型

1. **订单列表** - 订单编号、商品名称、数量、金额等
2. **活动列表** - 活动名称、折扣信息、时间周期等  
3. **商品基础信息** - 商品名称、价格、成本、SKU等

### 导入方式

#### 方式一：Excel文件上传
```
店铺管理 → 选择店铺 → 导入数据 → 选择Excel文件 → 上传
```

#### 方式二：在线表格导入（推荐）
```
店铺管理 → 选择店铺 → 导入数据 → 在线表格 → 粘贴飞书表格链接
```

**在线表格优势**：
- ✅ 实时同步 - 数据更新后无需重新上传
- ✅ 团队协作 - 多人可以共同维护数据
- ✅ 密码保护 - 支持密码保护敏感数据
- ✅ 操作简单 - 只需粘贴分享链接

### 详细文档

- [三种表格字段映射说明](docs/import/三种表格字段映射说明.md) ⭐⭐⭐
- [Excel导入功能使用指南](docs/import/Excel导入功能使用指南.md)
- [在线表格导入功能说明](docs/import/在线表格导入功能说明.md)
- [密码保护功能说明](docs/import/密码保护功能说明.md)

## 📊 功能模块

### 1. 仪表板 (`/dashboard`)
- 总订单量、GMV、利润、利润率等核心指标
- 近30天销售趋势图
- 店铺业绩对比图

### 2. 店铺管理 (`/shops`)
- 店铺列表查看
- 添加/编辑/删除店铺
- Token授权状态显示
- 店铺启用/禁用控制

### 3. 订单管理 (`/orders`)
- 订单列表查看
- 按店铺、状态、时间筛选
- 订单详情查看
- 成本和利润计算

### 4. 商品管理 (`/products`)
- 商品列表查看
- 商品成本录入
- 成本历史记录
- SKU管理

### 5. 数据统计 (`/statistics`)
- 日/周/月数据统计
- 销售趋势分析
- 店铺对比分析
- 可视化图表展示

### 6. GMV表格 (`/gmv-table`)
- 表格形式展示GMV数据
- 支持按日/周/月切换
- 自定义周期选择（7天、30天、6月、12月等）
- GMV、成本、利润、利润率详细展示
- 支持排序和筛选

### 7. SKU分析 (`/sku-analysis`)
- SKU销量排行榜
- 销量柱状图 + GMV柱状图
- 详细数据表格
- Top 10/20/50/100可选

### 8. 爆单榜 (`/hot-seller`)
- 负责人销量排行
- 金银铜牌展示
- 按月查看历史数据
- 点击查看负责人的SKU详情
- GMV横向对比图

### 9. 系统设置 (`/settings`)
- 全局App Key配置
- 全局App Secret配置
- 配置状态显示
- 帮助说明

## 📁 项目结构

```
temu-Omni/
├── backend/                # 后端服务
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── shops.py   # 店铺管理
│   │   │   ├── orders.py  # 订单管理
│   │   │   ├── products.py # 商品管理
│   │   │   ├── statistics.py # 统计分析
│   │   │   ├── analytics.py # 高级分析
│   │   │   ├── system.py  # 系统配置
│   │   │   └── sync.py    # 数据同步
│   │   ├── core/          # 核心模块
│   │   │   ├── config.py  # 配置
│   │   │   └── database.py # 数据库
│   │   ├── models/        # 数据模型
│   │   │   ├── shop.py    # 店铺模型
│   │   │   ├── order.py   # 订单模型
│   │   │   ├── product.py # 商品模型
│   │   │   ├── activity.py # 活动模型
│   │   │   └── system_config.py # 系统配置模型
│   │   ├── schemas/       # Pydantic模式
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 应用入口
│   ├── scripts/
│   │   └── generate_demo_data.py # 演示数据生成器
│   ├── requirements.txt   # Python依赖
│   └── Dockerfile         # 后端镜像
├── frontend/              # 前端服务
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   │   ├── Dashboard.tsx # 仪表板
│   │   │   ├── ShopList.tsx # 店铺管理
│   │   │   ├── OrderList.tsx # 订单管理
│   │   │   ├── ProductList.tsx # 商品管理
│   │   │   ├── Statistics.tsx # 数据统计
│   │   │   ├── GmvTable.tsx # GMV表格
│   │   │   ├── SkuAnalysis.tsx # SKU分析
│   │   │   ├── HotSellerPage.tsx # 爆单榜
│   │   │   └── SystemSettings.tsx # 系统设置
│   │   ├── layouts/       # 布局组件
│   │   ├── components/    # 通用组件
│   │   ├── services/      # API服务
│   │   └── App.tsx        # 应用入口
│   ├── package.json       # Node依赖
│   └── Dockerfile         # 前端镜像
├── docker-compose.yml     # Docker编排配置
├── Makefile              # 快捷命令
├── README.md             # 本文件
└── QUICKSTART.md         # 快速启动指南
```

## 🔧 常用命令

### Docker操作

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart frontend

# 重建并启动
docker compose up -d --build
```

### 数据库操作

```bash
# 初始化数据库
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 生成演示数据
docker compose exec backend python scripts/generate_demo_data.py

# 连接数据库
docker compose exec postgres psql -U temu_user -d temu_omni
```

### Makefile命令（如果有）

```bash
# 开发环境启动
make dev

# 初始化数据库
make db-init

# 生成演示数据
make demo-data

# 查看日志
make dev-logs

# 停止服务
make dev-down
```

## 🎯 演示数据说明

系统内置演示数据生成器，生成的数据包括：

- **3个演示店铺**: 美国、英国、德国店铺
- **45个商品**: 每个店铺15个商品，包含价格和成本
- **450个订单**: 最近90天的订单数据
- **15个活动**: 营销活动数据
- **10位负责人**: 张三、李四、王五等
- **完整的财务数据**: GMV约$74,000，利润约$33,000

### 重新生成演示数据

```bash
docker compose exec backend python scripts/generate_demo_data.py
```

## ❓ 常见问题

### 1. 端口冲突
**问题**: 5173端口被占用  
**解决**: 系统已改为使用8001端口，如需修改：
- 修改 `docker-compose.yml` 中的端口映射
- 重启服务

### 2. 前端显示空白或500错误
**解决方案**:
```bash
# 强制刷新浏览器
Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)

# 或重启前端服务
docker compose restart frontend
```

### 3. API请求失败
**可能原因**: 代理配置问题  
**解决**: 确认 `frontend/vite.config.ts` 中的proxy配置正确：
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true,
  },
}
```

### 4. 数据库连接失败
**解决**:
```bash
# 检查PostgreSQL服务
docker compose ps postgres

# 重启数据库
docker compose restart postgres

# 重新初始化
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 5. 店铺列表为空
**解决**:
```bash
# 生成演示数据
docker compose exec backend python scripts/generate_demo_data.py

# 刷新浏览器
```

## 📝 环境变量

主要环境变量（在docker-compose.yml中配置）：

```yaml
# 后端
DATABASE_URL: postgresql://temu_user:temu_password@postgres:5432/temu_omni
REDIS_URL: redis://redis:6379/0
CORS_ORIGINS: ["http://localhost:8001"]

# 前端
VITE_API_BASE_URL: http://localhost:8000
DOCKER_ENV: true
```

## 🔒 安全建议

1. **生产环境部署**:
   - 修改数据库默认密码
   - 使用环境变量管理敏感信息
   - 启用HTTPS
   - 配置防火墙规则

2. **API凭证管理**:
   - App Secret采用加密存储
   - Access Token定期轮换
   - 不要将凭证提交到版本控制

3. **访问控制**:
   - 添加用户认证系统
   - 实现权限管理
   - 记录操作日志

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📖 完整文档

本项目包含完整的文档体系，涵盖系统架构、API集成、数据导入、部署运维等各个方面。

### 📑 文档索引

**[完整文档索引 → docs/INDEX.md](docs/INDEX.md)** ⭐

### 快速导航

#### 📖 核心文档
- [系统架构设计](docs/ARCHITECTURE.md)
- [数据库表结构](docs/DATABASE_SCHEMA.md)
- [项目当前状态](docs/PROJECT_STATUS.md)
- [功能特性列表](docs/FEATURES.md)

#### 🚀 部署与运维
- [快速部署指南](docs/deployment/DEPLOY_QUICKSTART.md)
- [详细部署说明](docs/deployment/DEPLOYMENT_GUIDE.md)
- [Docker使用指南](docs/DOCKER_GUIDE.md)

#### 🔌 API集成
- [API快速接入](docs/api/QUICKSTART_API.md)
- [Temu API完整指南](docs/TEMU_API_GUIDE.md)
- [API接口文档](docs/API.md)
- [API数据映射关系](docs/API_DATA_MAPPING.md)

#### 📥 数据导入
- [三种表格字段映射说明](docs/import/三种表格字段映射说明.md) ⭐⭐⭐
- [Excel导入功能使用指南](docs/import/Excel导入功能使用指南.md)
- [在线表格导入功能说明](docs/import/在线表格导入功能说明.md)
- [密码保护功能说明](docs/import/密码保护功能说明.md)

#### 🎯 开发指南
- [快速入门教程](docs/guides/QUICKSTART.md)
- [前端集成指南](docs/guides/FRONTEND_INTEGRATION.md)
- [集成开发指南](docs/guides/INTEGRATION_GUIDE.md)

### 文档结构

```
docs/
├── INDEX.md                # 📑 文档索引（推荐起点）
├── api/                    # 🔌 API相关文档
├── import/                 # 📥 数据导入文档
├── deployment/             # 🚀 部署相关文档
├── guides/                 # 🎯 开发指南
├── ARCHITECTURE.md         # 系统架构
├── DATABASE_SCHEMA.md      # 数据库结构
└── ...                     # 更多文档
```

## 📞 联系方式

如有问题，请通过以下方式联系：
- 提交 Issue
- 发送邮件

---

**最后更新**: 2025-10-30  
**当前版本**: v2.0.0  
**系统状态**: ✅ 生产就绪
