# Temu-Omni 多店铺管理系统

## 项目简介

Temu-Omni 是一个专为Temu跨境卖家设计的多店铺管理系统，支持多地区、多主体店铺的统一管理和数据分析。

## 核心功能

### 📊 数据总览
- **多店铺聚合视图**：统一查看所有店铺的运营数据
- **多维度统计**：支持每日、每周、每月的数据汇总
- **实时同步**：通过Temu API自动同步订单和销售数据

### 💰 财务分析
- **GMV统计**：自动计算固定周期的商品交易总额
- **利润分析**：基于销售价格和成本计算实际利润
- **成本管理**：支持手动录入和批量导入商品成本

### 📈 趋势分析
- **销量趋势**：可视化展示销量变化曲线
- **对比分析**：支持店铺间、时间段间的数据对比
- **活动效果**：跟踪营销活动对销售的影响

### 🛍️ 订单管理
- **订单列表**：查看所有店铺的订单详情
- **订单搜索**：支持多条件筛选和查询
- **订单导出**：支持导出为Excel格式

## 技术架构

### 后端
- **框架**：FastAPI
- **数据库**：PostgreSQL + SQLAlchemy
- **数据分析**：Pandas + NumPy
- **API集成**：Temu Open API

### 前端
- **框架**：React 18 + TypeScript
- **UI组件**：Ant Design 5.x
- **图表库**：Apache ECharts
- **状态管理**：React Query + Zustand

## 快速开始

### 🐳 使用 Docker（推荐）

最简单的方式！只需要安装 Docker Desktop。

```bash
# 1. 配置环境变量
cp env.docker.template .env.docker
vim .env.docker  # 填入您的Temu API密钥

# 2. 启动服务
make dev

# 3. 初始化数据库
make db-init

# 4. 访问应用
# 前端: http://localhost:5173
# API文档: http://localhost:8000/docs
```

详细文档：[README_DOCKER.md](README_DOCKER.md) | [Docker使用指南](docs/DOCKER_GUIDE.md)

---

### 💻 手动安装

如果您不想使用Docker，可以按照以下步骤手动安装：

#### 前置要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+

#### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入数据库和Temu API配置

# 初始化数据库
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload
```

后端服务将运行在 http://localhost:8000

### 前端安装

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 http://localhost:5173

## 配置说明

### Temu API配置

1. 登录 [Temu开放平台](https://agentpartner.temu.com/)
2. 创建应用并获取 `app_key` 和 `app_secret`
3. 在 `backend/.env` 中配置：

```env
TEMU_APP_KEY=your_app_key
TEMU_APP_SECRET=your_app_secret
TEMU_API_BASE_URL=https://agentpartner.temu.com/api
```

### 数据库配置

```env
DATABASE_URL=postgresql://username:password@localhost:5432/temu_omni
```

## 使用指南

### 1. 添加店铺

在系统中添加您的Temu店铺，填入店铺ID和授权信息。

### 2. 同步数据

系统会自动定时同步订单数据，也可手动触发同步。

### 3. 录入成本

在商品管理中录入各商品的成本价，用于利润计算。

### 4. 查看报表

在仪表板中查看各类统计报表和趋势图表。

## API文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
temu-Omni/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # Pydantic模型
│   │   ├── services/    # 业务逻辑
│   │   └── temu/        # Temu API集成
│   ├── alembic/         # 数据库迁移
│   └── tests/           # 测试
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # UI组件
│   │   ├── pages/       # 页面
│   │   ├── services/    # API服务
│   │   └── utils/       # 工具函数
└── docs/                # 文档
```

## 开发计划

- [x] 项目初始化
- [x] Temu API集成
- [x] 数据库设计
- [x] 订单管理模块
- [x] 财务分析模块
- [x] 数据可视化
- [ ] 多语言支持
- [ ] 移动端适配
- [ ] 数据导出优化
- [ ] 更多报表类型

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提Issue。

