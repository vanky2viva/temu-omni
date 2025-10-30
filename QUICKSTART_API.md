# Temu API 快速开始指南

## 🎯 5分钟快速测试

### 步骤 1: 运行测试脚本

```bash
cd /Users/vanky/code/temu-Omni

# 最简单的测试
python3 api_test_complete.py
```

这将自动使用官方测试凭据进行完整测试。

### 步骤 2: 查看测试结果

测试脚本会显示：
- ✅ 成功的接口（显示绿色勾号）
- ❌ 失败的接口（显示红色叉号）
- 📊 测试统计信息

期望结果：**5/8 测试通过**

---

## 🚀 集成到项目中

### 方法 1: 使用环境变量（推荐）

```bash
# 复制测试配置
cp env.test.example .env.test

# 设置环境变量
export $(cat .env.test | xargs)

# 启动应用
cd backend
uvicorn app.main:app --reload
```

### 方法 2: 直接修改配置文件

编辑 `backend/app/core/config.py`，添加测试凭据：

```python
TEMU_APP_KEY = "4ebbc9190ae410443d65b4c2faca981f"
TEMU_APP_SECRET = "4782d2d827276688bf4758bed55dbdd4bbe79a79"
TEMU_ACCESS_TOKEN = "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7"
```

---

## 📝 使用后端API客户端

### 基本使用

```python
from app.temu.client import TemuAPIClient

# 创建客户端
client = TemuAPIClient()

# 设置access_token
access_token = "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7"

# 查询商品分类
categories = await client.get_product_categories(access_token)
print(categories)

# 查询订单列表（最近30天）
import time
end_time = int(time.time())
begin_time = end_time - (30 * 24 * 60 * 60)

orders = await client.get_orders(
    access_token=access_token,
    begin_time=begin_time,
    end_time=end_time,
    page_number=1,
    page_size=10
)
print(f"总订单数: {orders['totalItemNum']}")

# 查询Token信息
token_info = await client.get_token_info(access_token)
print(f"Mall ID: {token_info['mallId']}")

# 关闭客户端
await client.close()
```

### 常用API方法

```python
# 1. Token & 基础信息
token_info = await client.get_token_info(access_token)

# 2. 商品管理
categories = await client.get_product_categories(access_token, parent_cat_id=0)
products = await client.get_products(access_token, page_number=1, page_size=10)
product_detail = await client.get_product_detail(access_token, goods_id=123456)

# 3. 订单管理
orders = await client.get_orders(access_token, begin_time, end_time)
order_detail = await client.get_order_detail(access_token, order_sn="211-xxx")

# 4. 物流管理
warehouses = await client.get_warehouses(access_token)
```

---

## 🧪 测试特定接口

### 测试商品分类

```bash
python3 -c "
import asyncio
from backend.app.temu.client import TemuAPIClient

async def test():
    client = TemuAPIClient(
        app_key='4ebbc9190ae410443d65b4c2faca981f',
        app_secret='4782d2d827276688bf4758bed55dbdd4bbe79a79'
    )
    
    token = 'uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7'
    result = await client.get_product_categories(token)
    print(result)
    await client.close()

asyncio.run(test())
"
```

### 测试订单查询

```bash
python3 api_test_complete.py
```

---

## 📊 可用的测试工具

| 工具 | 用途 | 推荐度 |
|------|------|--------|
| `api_test.py` | 基础测试 | ⭐⭐ |
| `api_test_detailed.py` | 详细测试 | ⭐⭐⭐ |
| `api_test_complete.py` | 完整测试 | ⭐⭐⭐⭐ |
| `api_test_interactive.py` | 交互式测试 | ⭐⭐⭐⭐⭐ |

### 推荐使用

```bash
# 一键完整测试
python3 api_test_complete.py

# 或交互式测试（可以手动输入token）
python3 api_test_interactive.py
```

---

## ✅ 验证清单

测试成功后，你应该能看到：

- [x] ✅ API连接成功
- [x] ✅ 获取到24个商品分类
- [x] ✅ 查询到6019个订单
- [x] ✅ Token信息正确（Mall ID: 635517726820718）
- [x] ✅ 仓库列表显示正常

---

## 🐛 常见问题

### Q1: 出现签名错误
**A**: 确保使用的是MD5签名算法，不是HMAC-SHA256

### Q2: 提示缺少access_token
**A**: 检查环境变量或代码中是否正确设置了token

### Q3: 订单接口提示需要V2版本
**A**: 已更新，使用 `bg.order.list.v2.get`

### Q4: 部分接口返回业务错误
**A**: 可能是参数格式问题，参考测试脚本中的参数格式

---

## 📚 相关文档

- [完整测试结果](./TEMU_API_TEST_RESULTS.md)
- [详细测试指南](./TEMU_API_TEST_GUIDE.md)
- [API文档](./Temu_OpenAPI_开发者文档.md)
- [README - API测试](./README_API_TESTING.md)

---

## 🎓 下一步

完成快速测试后：

1. ✅ **验证通过** → 开始集成到项目
2. ❌ **遇到问题** → 查看 `TEMU_API_TEST_RESULTS.md`
3. 💡 **需要更多功能** → 查阅官方API文档

---

## 💻 代码示例

### 完整示例：查询并显示订单

```python
import asyncio
import time
from backend.app.temu.client import TemuAPIClient

async def main():
    # 初始化客户端
    client = TemuAPIClient(
        app_key='4ebbc9190ae410443d65b4c2faca981f',
        app_secret='4782d2d827276688bf4758bed55dbdd4bbe79a79'
    )
    
    # Access Token
    token = 'uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7'
    
    try:
        # 查询最近7天的订单
        end_time = int(time.time())
        begin_time = end_time - (7 * 24 * 60 * 60)
        
        print("查询订单中...")
        orders = await client.get_orders(
            access_token=token,
            begin_time=begin_time,
            end_time=end_time,
            page_number=1,
            page_size=10
        )
        
        print(f"总订单数: {orders['totalItemNum']}")
        print(f"本页订单: {len(orders['pageItems'])}")
        
        # 显示订单详情
        for item in orders['pageItems']:
            parent_order = item['parentOrderMap']
            print(f"\n订单号: {parent_order['parentOrderSn']}")
            print(f"订单状态: {parent_order['parentOrderStatus']}")
            print(f"订单时间: {parent_order['parentOrderTime']}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

保存为 `test_orders.py` 并运行：
```bash
python3 test_orders.py
```

---

**快速开始指南** | 更新于 2025-10-30 | 状态: ✅ 可用

