# 脚本工具说明

## 📋 脚本分类

### 🔧 初始化脚本

| 脚本 | 说明 | 使用场景 |
|-----|------|---------|
| `init_production_database.py` | 初始化生产数据库 | 首次部署时使用 |
| `init_default_user.py` | 创建默认管理员用户 | 首次部署时使用 |
| `init_postgres_with_cn_fields.py` | 初始化 PostgreSQL 并添加 CN 字段 | 数据库迁移时使用 |

### 🔄 同步脚本

| 脚本 | 说明 | 使用场景 |
|-----|------|---------|
| `sync_shop_cli.py` | 同步指定店铺数据 | 手动同步数据 |
| `resync_all_shops.py` | 重新同步所有店铺 | 数据修复时使用 |
| `resync_single_shop.py` | 重新同步单个店铺 | 单个店铺数据修复 |

### 💰 成本计算脚本

| 脚本 | 说明 | 使用场景 |
|-----|------|---------|
| `update_order_costs.py` | 批量更新订单成本 | 手动触发成本计算 |
| `verify_order_amount_and_collection.py` | 验证订单金额和回款统计 | 数据验证 |

### 🛠️ 维护脚本

| 脚本 | 说明 | 使用场景 |
|-----|------|---------|
| `reset_admin_password.py` | 重置管理员密码 | 忘记密码时使用 |
| `batch_update_prices.py` | 批量更新商品价格 | 批量价格更新 |

### 🧹 清理脚本

| 脚本 | 说明 | 使用场景 |
|-----|------|---------|
| `clear_orders.py` | 清理订单数据 | 测试环境清理 |
| `clear_all_data.py` | 清理所有数据 | 测试环境清理 |

---

## 🚀 常用脚本使用

### 初始化数据库

```bash
# 初始化生产数据库
python scripts/init_production_database.py

# 创建默认管理员用户
python scripts/init_default_user.py
```

### 同步数据

```bash
# 同步指定店铺的订单和商品
python scripts/sync_shop_cli.py --shop-id 1

# 全量同步所有店铺
python scripts/resync_all_shops.py --full-sync
```

### 更新订单成本

```bash
# 更新所有订单的成本
python scripts/update_order_costs.py

# 更新指定店铺的订单成本
python scripts/update_order_costs.py 1
```

### 数据验证

```bash
# 验证订单金额和回款统计
python scripts/verify_order_amount_and_collection.py
```

---

## ⚠️ 注意事项

1. **生产环境操作前请备份数据库**
2. **测试脚本请勿在生产环境运行**
3. **批量操作前请先在小范围测试**

---

*更多脚本说明请查看各脚本文件中的注释*

