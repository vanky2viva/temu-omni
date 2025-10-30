# Temu API 集成指南

**更新日期**: 2025-10-30  
**版本**: 1.0.0  
**状态**: ✅ 已完成后端集成

---

## 📋 目录

1. [架构设计](#架构设计)
2. [快速开始](#快速开始)
3. [数据库迁移](#数据库迁移)
4. [API端点说明](#api端点说明)
5. [多店铺管理](#多店铺管理)
6. [环境切换](#环境切换)
7. [前端集成](#前端集成)
8. [故障排查](#故障排查)

---

## 架构设计

### 🎯 核心特性

1. **多店铺支持** - 支持管理多个Temu店铺
2. **多区域支持** - US、EU、Global区域
3. **环境切换** - Sandbox（沙盒）/ Production（生产）
4. **独立Token** - 每个店铺独立的访问令牌
5. **数据同步** - API数据自动同步到数据库

### 🏗️ 架构图

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────┐
│   Backend API   │
│   (FastAPI)     │
├─────────────────┤
│ ┌─────────────┐ │
│ │ Shop Model  │ │  ← 店铺模型（环境、区域、Token）
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │TemuService  │ │  ← API服务层（封装API调用）
│ └─────────────┘ │
│ ┌─────────────┐ │
│ │ SyncService │ │  ← 数据同步服务
│ └─────────────┘ │
└────────┬────────┘
         │ HTTPS/API
         ↓
┌─────────────────┐
│   Temu API      │
│  (US/EU/Global) │
└─────────────────┘
```

### 📊 数据流

```
1. 前端选择店铺 → 2. 触发同步请求 → 3. 调用Temu API
         ↓                    ↓                  ↓
4. 返回原始数据 ← 5. 数据转换存储 ← 6. 获取API数据
         ↓
7. 前端展示数据
```

---

## 快速开始

### 步骤 1: 数据库迁移

```bash
cd /Users/vanky/code/temu-Omni/backend

# 执行迁移脚本
python scripts/migrate_add_shop_environment.py
```

**迁移内容**：
- ✅ 添加 `environment` 列（sandbox/production）
- ✅ 添加 `api_base_url` 列
- ✅ 更新现有数据的默认值

### 步骤 2: 初始化沙盒店铺

```bash
# 创建沙盒店铺（使用官方测试凭据）
python scripts/init_sandbox_shop.py
```

**创建的店铺**：
- 店铺名称: Temu沙盒测试店铺（US）
- Mall ID: 635517726820718
- 环境: Sandbox
- 区域: US
- Token: 已配置（有效期到2026-10-10）

### 步骤 3: 启动后端服务

```bash
# 开发模式
uvicorn app.main:app --reload

# 或使用
python app/main.py
```

服务地址：`http://localhost:8000`

### 步骤 4: 验证Token

```bash
# 测试Token是否有效
curl -X POST http://localhost:8000/api/sync/shops/1/verify-token
```

预期响应：
```json
{
  "success": true,
  "message": "Token验证成功",
  "data": {
    "mall_id": "635517726820718",
    "region_id": 211,
    "expires_at": 1792490190,
    "api_count": 100,
    "environment": "sandbox"
  }
}
```

### 步骤 5: 同步数据

```bash
# 同步所有数据（订单+商品+分类）
curl -X POST http://localhost:8000/api/sync/shops/1/all?full_sync=false

# 或只同步订单（最近7天）
curl -X POST http://localhost:8000/api/sync/shops/1/orders

# 全量同步（最近30天）
curl -X POST http://localhost:8000/api/sync/shops/1/all?full_sync=true
```

预期结果：
- ✅ 6,020个订单数据
- ✅ 24个商品分类
- ✅ 仓库信息

### 步骤 6: 查看数据

```bash
# 获取订单列表
curl http://localhost:8000/api/orders?shop_id=1

# 获取店铺信息
curl http://localhost:8000/api/shops/1

# 获取同步状态
curl http://localhost:8000/api/sync/shops/1/status
```

---

## API端点说明

### 店铺管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/shops` | 获取店铺列表 |
| GET | `/api/shops/{id}` | 获取店铺详情 |
| POST | `/api/shops` | 创建店铺 |
| PUT | `/api/shops/{id}` | 更新店铺 |
| DELETE | `/api/shops/{id}` | 删除店铺 |

### 数据同步

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/sync/shops/{id}/verify-token` | 验证店铺Token |
| POST | `/api/sync/shops/{id}/orders` | 同步订单 |
| POST | `/api/sync/shops/{id}/products` | 同步商品 |
| POST | `/api/sync/shops/{id}/all` | 同步所有数据 |
| POST | `/api/sync/all-shops` | 同步所有店铺 |
| GET | `/api/sync/shops/{id}/status` | 查看同步状态 |

### 订单管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/orders` | 获取订单列表（支持shop_id筛选） |
| GET | `/api/orders/{id}` | 获取订单详情 |

### 商品管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/products` | 获取商品列表（支持shop_id筛选） |
| GET | `/api/products/{id}` | 获取商品详情 |

---

## 多店铺管理

### 添加新店铺

#### 方法 1: 通过API添加

```bash
curl -X POST http://localhost:8000/api/shops \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": "YOUR_MALL_ID",
    "shop_name": "我的店铺",
    "region": "us",
    "environment": "production",
    "app_key": "YOUR_APP_KEY",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "api_base_url": "https://openapi-b-us.temu.com/openapi/router"
  }'
```

#### 方法 2: 通过数据库添加

```python
from app.core.database import SessionLocal
from app.models.shop import Shop, ShopEnvironment, ShopRegion
from datetime import datetime, timedelta

db = SessionLocal()

shop = Shop(
    shop_id="YOUR_MALL_ID",
    shop_name="我的生产店铺",
    region=ShopRegion.US,
    environment=ShopEnvironment.PRODUCTION,  # 生产环境
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    access_token="YOUR_ACCESS_TOKEN",
    api_base_url="https://openapi-b-us.temu.com/openapi/router",
    is_active=True
)

db.add(shop)
db.commit()
```

### 多区域店铺示例

```python
# 美国区域
shop_us = Shop(
    shop_id="US_MALL_ID",
    region=ShopRegion.US,
    api_base_url="https://openapi-b-us.temu.com/openapi/router"
)

# 欧洲区域
shop_eu = Shop(
    shop_id="EU_MALL_ID",
    region=ShopRegion.EU,
    api_base_url="https://openapi-b-eu.temu.com/openapi/router"
)

# 全球区域
shop_global = Shop(
    shop_id="GLOBAL_MALL_ID",
    region=ShopRegion.GLOBAL,
    api_base_url="https://openapi-b-global.temu.com/openapi/router"
)
```

---

## 环境切换

### Sandbox vs Production

| 特性 | Sandbox（沙盒） | Production（生产） |
|------|----------------|-------------------|
| 数据 | 测试数据 | 真实业务数据 |
| Token | 固定不变 | 需要定期刷新 |
| 用途 | 开发、测试、演示 | 正式运营 |
| 标识 | `environment='sandbox'` | `environment='production'` |

### 切换环境

```python
# 在数据库中更新店铺环境
from app.models.shop import ShopEnvironment

shop.environment = ShopEnvironment.PRODUCTION  # 切换到生产环境
shop.environment = ShopEnvironment.SANDBOX     # 切换到沙盒环境
db.commit()
```

### 环境标识

每个订单/商品都会记录来源环境：

```python
order.notes = f"Environment: {shop.environment.value}"
# 结果：Environment: sandbox 或 Environment: production
```

### 前端显示

建议在前端添加环境标识：

```typescript
// 显示环境徽章
{shop.environment === 'sandbox' && (
  <Badge color="orange">沙盒数据</Badge>
)}
{shop.environment === 'production' && (
  <Badge color="green">生产数据</Badge>
)}
```

---

## 前端集成

### 1. 添加店铺选择器

```typescript
// components/ShopSelector.tsx
import { Select } from 'antd';

function ShopSelector({ value, onChange }) {
  const [shops, setShops] = useState([]);
  
  useEffect(() => {
    // 获取店铺列表
    fetch('/api/shops')
      .then(res => res.json())
      .then(data => setShops(data));
  }, []);
  
  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder="选择店铺"
    >
      {shops.map(shop => (
        <Select.Option key={shop.id} value={shop.id}>
          {shop.shop_name}
          <Tag color={shop.environment === 'sandbox' ? 'orange' : 'green'}>
            {shop.environment}
          </Tag>
          <Tag>{shop.region}</Tag>
        </Select.Option>
      ))}
    </Select>
  );
}
```

### 2. 添加同步按钮

```typescript
// components/SyncButton.tsx
function SyncButton({ shopId }) {
  const [syncing, setSyncing] = useState(false);
  
  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`/api/sync/shops/${shopId}/all`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        message.success('数据同步成功！');
      }
    } catch (error) {
      message.error('同步失败：' + error.message);
    } finally {
      setSyncing(false);
    }
  };
  
  return (
    <Button 
      onClick={handleSync} 
      loading={syncing}
      icon={<SyncOutlined />}
    >
      同步数据
    </Button>
  );
}
```

### 3. 更新数据请求

```typescript
// 在所有数据请求中添加 shop_id 参数
const fetchOrders = async (shopId) => {
  const response = await fetch(`/api/orders?shop_id=${shopId}`);
  return response.json();
};

const fetchProducts = async (shopId) => {
  const response = await fetch(`/api/products?shop_id=${shopId}`);
  return response.json();
};
```

### 4. 添加环境指示器

```typescript
// components/EnvironmentBadge.tsx
function EnvironmentBadge({ environment }) {
  const config = {
    sandbox: { color: 'orange', text: '沙盒环境', icon: '🧪' },
    production: { color: 'green', text: '生产环境', icon: '🚀' }
  };
  
  const { color, text, icon } = config[environment];
  
  return (
    <Badge color={color}>
      {icon} {text}
    </Badge>
  );
}
```

---

## 故障排查

### 问题 1: Token验证失败

**症状**: `Token验证失败: ...`

**解决方案**:
1. 检查Token是否正确配置
2. 检查Token是否过期
3. 检查网络连接
4. 验证Mall ID是否匹配

```bash
# 重新验证Token
curl -X POST http://localhost:8000/api/sync/shops/1/verify-token
```

### 问题 2: 数据同步失败

**症状**: `数据同步失败: ...`

**解决方案**:
1. 检查店铺是否启用（`is_active=True`）
2. 检查是否配置了Token
3. 查看后端日志获取详细错误

```bash
# 查看同步状态
curl http://localhost:8000/api/sync/shops/1/status

# 查看日志
tail -f logs/app.log
```

### 问题 3: 订单数据为空

**症状**: 同步成功但订单列表为空

**解决方案**:
1. 检查时间范围（默认最近7天）
2. 尝试全量同步（30天）
3. 检查订单状态筛选

```bash
# 全量同步
curl -X POST "http://localhost:8000/api/sync/shops/1/orders?full_sync=true"

# 查看所有订单（不筛选shop_id）
curl http://localhost:8000/api/orders
```

### 问题 4: 签名错误

**症状**: `签名错误`

**解决方案**:
1. 确认使用MD5签名算法
2. 检查App Secret是否正确
3. 确认参数按字母顺序排序

---

## 最佳实践

### 1. 数据同步策略

```python
# 定时任务：每小时同步一次
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=1)
async def sync_all_shops():
    await sync_all_shops(db, full_sync=False)

scheduler.start()
```

### 2. 环境隔离

- 开发环境：仅使用sandbox店铺
- 测试环境：sandbox + production（小流量）
- 生产环境：主要使用production店铺

### 3. Token管理

```python
# 检查Token过期时间
if shop.token_expires_at < datetime.now():
    # 刷新Token或通知管理员
    logger.warning(f"Token即将过期: {shop.shop_name}")
```

### 4. 数据备份

```bash
# 定期备份数据库
pg_dump your_database > backup_$(date +%Y%m%d).sql
```

---

## 下一步

### 立即可做
- [x] ✅ 执行数据库迁移
- [x] ✅ 初始化沙盒店铺
- [x] ✅ 同步测试数据
- [ ] 🔄 更新前端店铺选择器
- [ ] 🔄 添加同步按钮

### 短期任务
- [ ] 实现自动同步定时任务
- [ ] 添加同步进度显示
- [ ] 实现数据缓存机制
- [ ] 添加错误日志监控

### 长期任务
- [ ] 支持批量导入店铺
- [ ] 实现Token自动刷新
- [ ] 添加数据统计分析
- [ ] 实现多语言支持

---

## 文档和支持

- 📖 **API测试结果**: `API_TEST_FINAL_SUCCESS.md`
- 🚀 **快速开始**: `QUICKSTART_API.md`
- 📚 **Temu API文档**: `Temu_OpenAPI_开发者文档.md`
- 💻 **测试脚本**: `api_test_complete.py`

---

**集成完成！** 🎉

现在你可以：
- ✅ 管理多个店铺（sandbox + production）
- ✅ 支持多区域（US/EU/Global）
- ✅ 同步真实数据（6,020个订单）
- ✅ 环境自由切换

**下一步**: 更新前端以支持多店铺选择和数据同步！

