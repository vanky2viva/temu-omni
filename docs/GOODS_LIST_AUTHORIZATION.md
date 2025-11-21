# 商品列表 API 授权说明

## 问题

当前 access_token 无法调用 `bg.local.goods.list.query` API，返回错误：

```
error_code: 3000032
error_msg: access_token don't have this api access, please ask for seller to authorize this api in seller center first.and share the new access_token with you.
```

## 原因

access_token 的权限范围（apiScopeList）中不包含 `bg.local.goods.list.query` API。

### 当前已授权的商品相关 API

- ✅ `bg.goods.compliancelabel.get` - 商品合规标签
- ✅ `bg.goods.replenishment.*` - 补货相关 API
- ❌ `bg.local.goods.list.query` - **商品列表查询（未授权）**

## 解决方案

### 1. 在卖家中心授权商品列表 API

根据 [Temu 官方文档](https://partner.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=a5b48b3e2fd94d79a7a3fa42122e4727)，需要授权以下权限包：

**权限包**：
- `Local Product Management` (private, public)
- `WMS Local Product Management` (public)

### 2. 授权步骤

1. **登录卖家中心**
   - US 区域：https://agentseller.temu.com/
   - EU 区域：https://agentseller-eu.temu.com/
   - Global 区域：https://agentseller.temu.com/

2. **进入应用授权页面**
   - 路径：开放平台 → 系统管理 → 客户端管理
   - 或直接访问：https://agentseller.temu.com/open-platform/system-manage/client-manage

3. **授权商品管理权限**
   - 找到对应的应用
   - 勾选 `Local Product Management` 权限包
   - 保存授权

4. **获取新的 access_token**
   - 授权后，需要重新授权获取新的 access_token
   - 或者等待 token 刷新

### 3. 验证授权

授权后，使用新的 access_token 调用 `bg.open.accesstoken.info.get` API，检查 `apiScopeList` 中是否包含：

```
bg.local.goods.list.query
```

## API 使用说明

### 请求参数

根据文档，商品列表 API 需要以下参数：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `pageNo` | INTEGER | 是 | 页码 |
| `pageSize` | INTEGER | 是 | 每页大小（最大 100） |
| `goodsStatusFilterType` | INTEGER | 是 | 商品状态筛选（新版本字段） |
| `goodsSearchType` | INTEGER | 是 | 商品状态筛选（旧版本字段） |

**注意**：`goodsStatusFilterType` 和 `goodsSearchType` 至少需要提供一个。

### 商品状态筛选值

- `1` - 已上架/已下架
- `4` - 未发布
- `5` - 草稿
- `6` - 已删除

### 请求示例

```json
{
  "api_type": "bg.local.goods.list.query",
  "access_token": "your_access_token",
  "request_data": {
    "pageNo": 1,
    "pageSize": 10,
    "goodsStatusFilterType": 1
  }
}
```

### 响应示例

```json
{
  "success": true,
  "result": {
    "goodsList": [
      {
        "goodsId": 123456789,
        "goodsName": "商品名称",
        "outGoodsSn": "外部编号",
        "catId": 1001,
        "price": "19.99",
        "currency": "USD",
        "quantity": 100,
        "thumbUrl": "https://...",
        "skuInfoList": [...]
      }
    ],
    "pageNo": 1,
    "total": 100
  }
}
```

## 区域说明

根据文档，不同区域使用不同的 API URL：

| 区域 | API URL |
|------|---------|
| US | `https://openapi-b-us.temu.com/openapi/router` |
| EU | `https://openapi-b-eu.temu.com/openapi/router` |
| Global | `https://openapi-b-global.temu.com/openapi/router` |

**当前代理服务器配置**：使用 US 区域的 URL。

如果店铺在 Global 区域，可能需要：
1. 修改代理服务器的 API URL 为 Global
2. 或者根据店铺区域动态选择 API URL

## 测试命令

授权后，可以使用以下命令测试：

```bash
curl -X POST http://172.236.231.45:8001/api/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "api_type": "bg.local.goods.list.query",
    "access_token": "新的access_token",
    "request_data": {
      "pageNo": 1,
      "pageSize": 10,
      "goodsStatusFilterType": 1
    }
  }'
```

## 参考文档

- [Temu 官方文档 - 商品列表查询](https://partner.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=a5b48b3e2fd94d79a7a3fa42122e4727)
- [卖家授权指南](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a)




