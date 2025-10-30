# Temu Open API 开发者文档

Temu Open API 为独立软件开发商（ISV）提供了一套面向卖家的接口，允许应用与 Temu 市场的数据交互。通过这些接口可以实现商品管理、订单管理、物流信息同步、价格调整、广告推广等功能，从而帮助卖家自动化管理在 Temu 平台上的业务。

---

## 1. 开发者准备

### 1.1 创建应用并获取凭据

1. 登录 Temu Seller Center（卖家中心），创建开发者应用。
2. 在「Apps and Services → Manage your apps」中新建「Add a self‑developed app」。
3. 获取 `App Key` 与 `App Secret`，用于接口签名与身份验证。
4. 设置 `Redirect URL`（授权回调地址）。授权完成后 Temu 将携带 `code` 参数跳转至该地址。

### 1.2 开发环境说明

- 请求协议：HTTPS  
- 基础 URL：`https://openapi‑b‑{region}.temu.com/openapi/router`（region 为 global、us、eu 等）  
- 数据格式：POST + JSON  
- 所有请求必须签名（MD5 + App Secret）。

---

## 2. 授权流程

Temu API 的授权流程如下：

1. 卖家授权应用，Temu 重定向到 `redirect_url` 并附带授权码 `code`。
2. 通过接口 `bg.open.accesstoken.create` 将 `code` 换取 `access_token` 与 `refresh_token`。
3. 存储 `access_token`（有效期 12 小时）并在调用业务接口时附带。
4. 若需查看或验证 token，可调用 `bg.open.accesstoken.info.get`。

> ⚠️ 注意：Temu 授权回调不直接返回 token，必须通过 `code` 换取。

---

## 3. 通用请求格式

所有 Temu API 接口均通过相同路由调用，通过 `type` 参数区分。

| 参数名 | 必填 | 说明 |
|--------|------|------|
| `type` | 是 | 接口名称（如 `bg.open.accesstoken.create`） |
| `app_key` | 是 | 应用 App Key |
| `access_token` | 部分必填 | 授权令牌，获取 token 时无需传 |
| `timestamp` | 是 | Unix 时间戳（±300 秒） |
| `sign` | 是 | 按照 Temu 签名算法计算的 MD5 大写值 |
| `version` | 否 | 默认为 V1 |
| `data_type` | 否 | 默认 JSON |

业务参数放在 `request` 对象中。

---

## 4. 获取访问令牌：`bg.open.accesstoken.create`

**用途**：用授权码换取访问令牌。

- **URL**：`https://openapi‑b‑{region}.temu.com/openapi/router`
- **请求体参数**：
  ```json
  {
    "type": "bg.open.accesstoken.create",
    "app_key": "your_app_key",
    "timestamp": 1730000000,
    "sign": "xxxxxx",
    "request": {
      "code": "授权回调获得的code"
    }
  }
  ```

- **响应示例**：
  ```json
  {
    "success": true,
    "errorCode": 0,
    "result": {
      "access_token": "xxxx",
      "refresh_token": "yyyy",
      "expires_in": 43200,
      "mallId": "123456"
    }
  }
  ```

---

## 5. 查询访问令牌信息：`bg.open.accesstoken.info.get`

**用途**：查询 token 状态与绑定店铺。

- **请求示例**：
  ```json
  {
    "type": "bg.open.accesstoken.info.get",
    "app_key": "your_app_key",
    "access_token": "xxxx",
    "timestamp": 1730000000,
    "sign": "zzzz"
  }
  ```

- **响应**：返回 token 信息及授权店铺数据。

---

## 6. 接口分类概览

| 分类 | 功能 |
|------|------|
| Product | 查询/上架/更新商品信息 |
| Price | 提交或获取价格调整 |
| Order | 获取订单、发货、售后（V2 版本） |
| Logistics | 查询物流、上传运单号、追踪 |
| Fulfillment | 履约单创建与发货确认 |
| Return & Refund | 退货申请、退款审核 |
| Promotion | 优惠券与促销活动 |
| Webhook | 事件订阅与推送 |
| Ads | 广告报表与活动管理 |

---

## 7. 错误码与限制

| 错误码 | 说明 |
|--------|------|
| 1000000 | 系统繁忙，请重试 |
| 1000001 | 签名错误 |
| 1000002 | 参数缺失或格式错误 |

- 常见速率限制：每分钟 60 次（视接口而定）。

---

## 8. 最佳实践

1. **缓存 token**：用 `refresh_token` 定时刷新，避免频繁授权。  
2. **签名正确性**：严格按字典序拼接参数并使用 App Secret 生成 MD5。  
3. **Webhook**：推荐使用事件订阅实现实时数据同步。  
4. **日志与重试机制**：记录失败调用与错误码。  
5. **关注版本更新**：Temu 会定期升级接口（如 Order V2）。

---

© 2025 Temu Partner OpenAPI Integration Guide — internal developer reference.
