# 文档和脚本清理计划

## 📋 清理目标

为生产环境部署做准备，清理和整理项目文件。

## 🗂️ 脚本分类

### ✅ 保留的脚本（生产环境需要）

#### 初始化脚本
- `init_production_database.py` - 初始化生产数据库
- `init_default_user.py` - 创建默认管理员
- `init_postgres_with_cn_fields.py` - 数据库迁移

#### 同步脚本
- `sync_shop_cli.py` - 手动同步数据
- `resync_all_shops.py` - 全量同步
- `resync_single_shop.py` - 单店铺同步

#### 成本计算脚本
- `update_order_costs.py` - 更新订单成本
- `verify_order_amount_and_collection.py` - 数据验证

#### 维护脚本
- `reset_admin_password.py` - 重置密码
- `batch_update_prices.py` - 批量更新价格

### 📦 归档的脚本（测试/调试用）

#### 测试脚本 → `archive/scripts/test/`
- `test_*.py` - 所有测试脚本

#### 调试脚本 → `archive/scripts/debug/`
- `debug_*.py` - 所有调试脚本

#### 检查脚本 → `archive/scripts/check/`
- `check_*.py` - 检查脚本（除验证脚本外）
- `query_*.py` - 查询脚本
- `show_*.py` - 显示脚本
- `list_*.py` - 列表脚本
- `compare_*.py` - 比较脚本

### 🗑️ 可删除的脚本

- `clear_*.py` - 清理脚本（生产环境不需要）
- `force_clear_*.py` - 强制清理脚本

## 📚 文档整理

### ✅ 保留的核心文档

#### 快速开始
- `docs/guides/QUICKSTART.md`
- `docs/deployment/PRODUCTION_DEPLOYMENT.md`
- `docs/DOCKER_GUIDE.md`

#### 核心功能
- `docs/ARCHITECTURE.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/API.md`
- `docs/TEMU_API_GUIDE.md`

#### 数据相关
- `docs/SYNC_STRATEGY.md`
- `docs/DATA_UPDATE_STRATEGY.md`
- `docs/VERIFY_ORDER_AMOUNT_AND_COLLECTION.md`
- `docs/ORDER_COST_CALCULATION.md`

#### 功能文档
- `docs/import/Excel导入功能使用指南.md`
- `docs/PROXY_SETUP.md`

#### 技术文档
- `docs/API_DATA_MAPPING.md`
- `docs/CN_ENDPOINT_SUPPORT.md`
- `backend/docs/ORDER_PRODUCT_MATCHING.md`

### 📦 归档的文档（历史记录）

#### 测试相关 → `archive/docs/old/`
- `docs/api/API_TEST_*.md`
- `docs/api/TEMU_API_TEST_*.md`
- `docs/api/API_SUCCESS_SUMMARY.md`

#### 开发过程文档 → `archive/docs/old/`
- `docs/PROJECT_PROGRESS.md`
- `docs/PROJECT_STATUS.md`
- `docs/NEXT_STEPS.md`
- `docs/UPDATE_SUMMARY.md`
- `docs/CLEANUP_SUMMARY.md`
- `docs/FILES_CHANGED.md`
- `docs/MIGRATION_SUCCESS.md`

#### 重复/过时文档 → `archive/docs/old/`
- `docs/API_INTEGRATION_PLAN.md` (已整合到其他文档)
- `docs/API_INTEGRATION_CHANGES.md` (历史记录)
- `docs/DOCUMENTATION_REORGANIZATION.md` (临时文档)

### 🗑️ 可删除的文档

- `docs/文档整理说明.md` - 临时说明文件

## 🚀 执行清理

### 自动清理脚本

```bash
# 运行清理脚本
./scripts/cleanup_for_production.sh
```

### 手动清理步骤

1. **归档测试脚本**
   ```bash
   mkdir -p archive/scripts/{test,debug,check}
   mv backend/scripts/test_*.py archive/scripts/test/
   mv backend/scripts/debug_*.py archive/scripts/debug/
   ```

2. **归档文档**
   ```bash
   mkdir -p archive/docs/old
   mv docs/api/API_TEST_*.md archive/docs/old/
   mv docs/PROJECT_PROGRESS.md archive/docs/old/
   ```

3. **清理临时文件**
   ```bash
   rm -f *.db *.db-journal
   rm -f backend/*.db
   ```

## ✅ 清理后结构

```
temu-Omni/
├── backend/
│   ├── scripts/
│   │   ├── README.md              # 脚本说明
│   │   ├── init_*.py             # 初始化脚本
│   │   ├── sync_*.py             # 同步脚本
│   │   ├── update_*.py           # 更新脚本
│   │   └── verify_*.py           # 验证脚本
│   └── ...
├── docs/
│   ├── README.md                  # 文档索引
│   ├── guides/                    # 快速开始
│   ├── deployment/                # 部署文档
│   ├── import/                    # 功能文档
│   └── ...
├── archive/                       # 归档文件
│   ├── scripts/
│   │   ├── test/                 # 测试脚本
│   │   ├── debug/                # 调试脚本
│   │   └── check/                # 检查脚本
│   └── docs/old/                 # 历史文档
└── README.md                      # 项目说明
```

---

*清理完成后，项目结构将更加清晰，便于生产环境部署和维护。*

