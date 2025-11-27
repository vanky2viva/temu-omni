# Temu API 集成指南

## 获取API凭证

1. 访问 [Temu开放平台](https://agentpartner.temu.com/)
2. 注册并创建应用
3. 获取 `app_key` 和 `app_secret`
4. 在后端 `.env` 文件中配置这些凭证

## API签名机制

Temu API使用HMAC-SHA256签名算法来确保请求的安全性。

### 签名步骤

1. 将所有请求参数按键名排序
2. 拼接参数字符串：`key1value1key2value2...`
3. 在字符串前后加上 `app_secret`
4. 使用HMAC-SHA256算法计算签名
5. 将签名转换为大写十六进制字符串

示例代码已在 `backend/app/temu/client.py` 中实现。

## 主要API接口

### 1. 获取订单列表

```python
from app.temu import TemuAPIClient

client = TemuAPIClient()
orders = await client.get_orders(
    access_token="your_access_token",
    start_time=1704067200,  # Unix时间戳
    end_time=1704153600,
    page=1,
    page_size=100
)
```

### 2. 获取订单详情

```python
order_detail = await client.get_order_detail(
    access_token="your_access_token",
    order_sn="ORDER123456"
)
```

### 3. 获取商品列表

**重要：商品列表同步使用CN区域配置**

商品列表同步必须使用CN区域的配置（`cn_app_key`, `cn_app_secret`, `cn_access_token`）和CN端点。

#### API端点配置

- **端点URL**: 使用店铺配置的 `cn_api_base_url` 或默认 `https://openapi.kuajingmaihuo.com/openapi/router`
- **API接口**: `bg.glo.goods.list.get`
- **认证**: 使用CN区域的 `cn_app_key`, `cn_app_secret`, `cn_access_token`

#### 请求参数

```python
request_data = {
    "page": 1,           # 页码（从1开始）
    "pageSize": 100,     # 每页数量
    "skcSiteStatus": 1   # 可选：SKC站点状态（0=未加入站点，1=已加入站点/在售）
}
```

#### 响应格式

```json
{
    "data": [...],        // 商品列表
    "totalCount": 100     // 商品总数
}
```

#### 使用示例

```python
from app.services.temu_service import TemuService

# 通过TemuService获取商品列表（自动使用CN配置）
temu_service = TemuService(shop=shop)
products = await temu_service.get_products(
    page_number=1,
    page_size=100,
    skc_site_status=1  # 可选：只获取在售商品
)
```

#### 配置要求

1. **店铺配置**（Shop表）：
   - `cn_app_key`: CN区域App Key
   - `cn_app_secret`: CN区域App Secret
   - `cn_access_token`: CN区域Access Token
   - `cn_api_base_url`: CN区域API端点（可选，默认：`https://openapi.kuajingmaihuo.com/openapi/router`）

2. **环境变量**（可选，作为店铺配置的备用）：
   - `TEMU_CN_APP_KEY`: CN区域App Key
   - `TEMU_CN_APP_SECRET`: CN区域App Secret

#### 注意事项

- ⚠️ **必须使用CN区域配置**：商品列表同步不支持使用标准区域的配置
- ⚠️ **接口选择**：仅使用 `bg.glo.goods.list.get` 接口，`bg.goods.list.get` 在Partner端点上不存在
- ⚠️ **代理设置**：CN端点不需要通过代理，直接访问

### 4. 获取活动列表

```python
activities = await client.get_activities(
    access_token="your_access_token",
    start_time=1704067200,
    end_time=1704153600
)
```

## 授权流程

### OAuth2授权

1. **引导用户授权**

用户需要访问Temu授权页面并授权您的应用。

2. **获取授权码**

授权成功后，Temu会重定向到您的回调URL，并携带授权码。

3. **换取Access Token**

使用授权码换取访问令牌。

4. **存储Token**

将访问令牌和刷新令牌存储在数据库中（Shop表）。

## 数据同步策略

### 定时同步

系统支持自动定时同步订单数据。在配置文件中设置：

```env
AUTO_SYNC_ENABLED=True
SYNC_INTERVAL_MINUTES=30
```

### 手动同步

通过管理界面手动触发同步。

### 增量同步

建议使用增量同步，只同步新增或更新的订单：

```python
# 获取最后同步时间
last_sync = shop.last_sync_at
# 只同步此时间之后的订单
orders = await client.get_orders(
    access_token=shop.access_token,
    start_time=int(last_sync.timestamp()),
    end_time=int(datetime.now().timestamp())
)
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 1001 | 签名错误 | 检查app_key和app_secret |
| 1002 | token过期 | 使用refresh_token刷新 |
| 1003 | 参数错误 | 检查请求参数 |
| 2001 | 订单不存在 | 确认订单号是否正确 |
| 5001 | 系统错误 | 稍后重试 |

### 重试机制

对于网络错误或临时性错误，建议实现重试机制：

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def sync_orders_with_retry(client, access_token):
    return await client.get_orders(access_token, ...)
```

## 最佳实践

### 1. Token管理

- 定期检查token过期时间
- 提前刷新即将过期的token
- 安全存储token（加密）

### 2. 请求频率控制

- 遵守API调用频率限制
- 使用队列管理批量请求
- 实现指数退避策略

### 3. 数据一致性

- 使用事务确保数据一致性
- 记录同步日志便于问题排查
- 定期校验数据完整性

### 4. 性能优化

- 批量获取数据而非单条请求
- 使用异步请求提高并发
- 合理使用缓存减少API调用

## 示例：完整同步流程

```python
async def sync_shop_orders(shop_id: int, db: Session):
    """同步店铺订单"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop or not shop.access_token:
        raise ValueError("店铺不存在或未授权")
    
    client = TemuAPIClient()
    
    # 计算同步时间范围
    end_time = int(datetime.now().timestamp())
    start_time = int((shop.last_sync_at or datetime.now() - timedelta(days=30)).timestamp())
    
    try:
        # 获取订单
        page = 1
        while True:
            result = await client.get_orders(
                access_token=shop.access_token,
                start_time=start_time,
                end_time=end_time,
                page=page,
                page_size=100
            )
            
            orders = result.get("orders", [])
            if not orders:
                break
            
            # 保存订单
            for order_data in orders:
                order = db.query(Order).filter(
                    Order.order_sn == order_data["order_sn"]
                ).first()
                
                if order:
                    # 更新现有订单
                    for key, value in order_data.items():
                        setattr(order, key, value)
                else:
                    # 创建新订单
                    order = Order(**order_data, shop_id=shop.id)
                    db.add(order)
            
            db.commit()
            page += 1
        
        # 更新同步时间
        shop.last_sync_at = datetime.now()
        db.commit()
        
    finally:
        await client.close()
```

## 测试API连接

使用以下脚本测试Temu API连接：

```python
import asyncio
from app.temu import TemuAPIClient
from app.core.config import settings

async def test_connection():
    client = TemuAPIClient()
    try:
        # 测试API（需要有效的access_token）
        result = await client.get_orders(
            access_token="your_test_token",
            start_time=1704067200,
            end_time=1704153600,
            page=1,
            page_size=1
        )
        print("API连接成功！")
        print(result)
    except Exception as e:
        print(f"API连接失败: {e}")
    finally:
        await client.close()

asyncio.run(test_connection())
```

