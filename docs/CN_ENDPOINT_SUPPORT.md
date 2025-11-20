# CN 端点支持说明

## 概述

已为系统添加对 CN 区域 API 端点的支持，用于商品列表获取和发品相关操作。

## 功能说明

### 1. CN 端点配置

CN 区域使用独立的 API 端点和认证信息：

- **接口地址**: `https://openapi.kuajingmaihuo.com/openapi/router`
- **App Key**: `af5bcf5d4bd5a492fa09c2ee302d75b9`
- **App Secret**: `e4f229bb9c4db21daa999e73c8683d42ba0a7094`
- **API 类型**: `bg.goods.list.get`（与标准端点的 `bg.local.goods.list.query` 不同）

### 2. 数据库变更

在 `shops` 表中新增以下字段：

- `cn_access_token`: CN 区域访问令牌（**用户需要填写**）
- `cn_app_key`: CN 区域 App Key（**已内置在系统中**，默认值：`af5bcf5d4bd5a492fa09c2ee302d75b9`）
- `cn_app_secret`: CN 区域 App Secret（**已内置在系统中**，默认值：`e4f229bb9c4db21daa999e73c8683d42ba0a7094`）
- `cn_api_base_url`: CN 区域 API 基础 URL（**已内置在系统中**，默认值：`https://openapi.kuajingmaihuo.com/openapi/router`）

**注意**：CN 区域的 App Key 和 App Secret 已内置在系统中，用户无需在添加店铺时填写，只需要填写 CN Access Token。

### 3. 前端界面更新

在店铺创建/编辑界面中：

- 添加了 **CN Access Token** 输入框
- 提供了授权链接提示，指向：https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182
- CN Access Token 为可选字段，仅在需要时填写

### 4. 后端逻辑更新

#### TemuService.get_products()

商品列表获取逻辑已更新：

- 如果店铺配置了 `cn_access_token`，自动使用 CN 端点
- 使用 CN 端点时，调用 `bg.goods.list.get` API
- 响应格式自动适配（CN 端点返回 `data` 字段，标准端点返回 `goodsList` 字段）

#### 响应格式差异

**CN 端点响应格式**:
```json
{
  "data": [
    {
      "productId": 123456,
      "productName": "商品名称",
      "skcSiteStatus": 0,
      ...
    }
  ],
  "totalCount": 100
}
```

**标准端点响应格式**:
```json
{
  "goodsList": [
    {
      "goodsId": 123456,
      "goodsName": "商品名称",
      "goodsStatus": 1,
      ...
    }
  ],
  "totalItemNum": 100
}
```

## 使用方法

### 1. 添加店铺时配置 CN Access Token

1. 在"添加店铺"表单中，填写基本信息
2. 在 **CN Access Token** 字段中，粘贴从[指定地址](https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182)获取的访问令牌
3. **注意**：CN 区域的 App Key 和 App Secret 已内置在系统中，无需填写
4. 保存店铺

### 2. 编辑店铺时更新 CN Access Token

1. 点击店铺的"编辑"按钮
2. 在 **CN Access Token** 字段中更新令牌
3. 保存更改

### 3. 获取商品列表

配置了 CN Access Token 的店铺，在同步商品列表时会自动使用 CN 端点：

- 系统会自动检测是否配置了 `cn_access_token`
- 如果已配置，使用 CN 端点和对应的 API 类型
- 如果未配置，使用标准端点和 API 类型

## 数据库迁移

运行以下命令执行数据库迁移：

```bash
cd backend
alembic upgrade head
```

迁移脚本：`backend/alembic/versions/add_cn_api_fields_to_shops.py`

## ⚠️ 重要注意事项

### 区域凭证匹配规则

根据 [Temu 官方文档](https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182)，**必须保证接口地址、app_key、secret、access_token 来自同一个区域**，不能混用！

**错误示例**：
- ❌ 使用 US 的 app_key 和 access_token 调用 CN 的接口地址 → 接口会报错拦截
- ❌ 使用 CN 的 app_key 调用 US 的接口地址 → 接口会报错拦截

**正确做法**：
- ✅ CN 区域：使用 CN 的 app_key、secret、access_token 和接口地址
- ✅ US 区域：使用 US 的 app_key、secret、access_token 和接口地址
- ✅ EU 区域：使用 EU 的 app_key、secret、access_token 和接口地址
- ✅ GLOBAL 区域：使用 GLOBAL 的 app_key、secret、access_token 和接口地址

### 业务场景与区域对应关系

根据文档，不同业务场景需要使用不同的区域：

| 店铺类型 | 业务场景 | 使用区域 |
|---------|---------|---------|
| 全托 | 发品、库存、备货履约 | **CN** |
| 全托 | 合规资质 | **GLOBAL** |
| 半托 | 半托发品 | **CN** |
| 半托 | 半托库存、调价核价 | **PARTNER** |
| 半托 | 美国半托履约 | **US** |
| 半托 | 欧区半托履约 | **EU** |
| 本本 | 美国商品、履约 | **US** |
| 本本 | 欧区商品、履约 | **EU** |

### 系统实现说明

1. **商品列表、发品等操作**：
   - 如果配置了 `cn_access_token`，系统自动使用 CN 区域的配置
   - 使用 CN 的 app_key、secret、access_token 和接口地址
   - API 类型：`bg.goods.list.get`

2. **订单、履约等操作**：
   - 根据店铺的 `region` 字段（US/EU/GLOBAL）使用对应区域的配置
   - 使用店铺的 `app_key`、`app_secret`、`access_token` 和 `api_base_url`
   - 如果店铺未配置，使用全局配置（需确保区域匹配）

3. **CN Access Token 为可选**：如果店铺不需要使用 CN 端点，可以不填写

4. **CN App Key 和 Secret 已内置**：CN 区域的 App Key（`af5bcf5d4bd5a492fa09c2ee302d75b9`）和 App Secret（`e4f229bb9c4db21daa999e73c8683d42ba0a7094`）已内置在系统中，用户无需填写

5. **API URL 已内置**：CN 区域的接口地址（`https://openapi.kuajingmaihuo.com/openapi/router`）已内置在系统中

6. **API 类型不同**：CN 端点使用 `bg.goods.list.get`，标准端点使用 `bg.local.goods.list.query`

7. **响应格式不同**：系统已自动适配两种响应格式

## 测试

可以使用测试脚本验证 CN 端点：

```bash
cd backend
python3 scripts/test_cn_endpoint.py
```

## 相关文件

- 数据库模型: `backend/app/models/shop.py`
- Schema: `backend/app/schemas/shop.py`
- API: `backend/app/api/shops.py`
- 服务层: `backend/app/services/temu_service.py`
- 前端界面: `frontend/src/pages/ShopList.tsx`
- 迁移脚本: `backend/alembic/versions/add_cn_api_fields_to_shops.py`
- 测试脚本: `backend/scripts/test_cn_endpoint.py`

