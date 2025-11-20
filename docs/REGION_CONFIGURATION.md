# Temu API 区域配置说明

## 概述

根据 [Temu 官方文档](https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182)，Temu 开放平台接口分为四个区域（CN/US/EU/GLOBAL），每个区域覆盖的能力、接口地址均不相同。

## ⚠️ 核心原则

**必须保证接口地址、app_key、secret、access_token 来自同一个区域，不能混用！**

### 错误示例
- ❌ 使用 US 的 app_key 和 access_token 调用 CN 的接口地址 → 接口会报错拦截
- ❌ 使用 CN 的 app_key 调用 US 的接口地址 → 接口会报错拦截

### 正确做法
- ✅ CN 区域：使用 CN 的 app_key、secret、access_token 和接口地址
- ✅ US 区域：使用 US 的 app_key、secret、access_token 和接口地址
- ✅ EU 区域：使用 EU 的 app_key、secret、access_token 和接口地址
- ✅ GLOBAL 区域：使用 GLOBAL 的 app_key、secret、access_token 和接口地址

## 区域地址配置

| 区域 | 开平地址 | 接口地址 | 卖家中心授权地址 |
|------|---------|---------|----------------|
| **CN** | https://partner.kuajingmaihuo.com/<br>https://agentpartner.temu.com/ | `https://openapi.kuajingmaihuo.com/openapi/router` | https://agentseller.temu.com/open/system-manage/client-manage |
| **PARTNER** | https://partner.kuajingmaihuo.com/<br>https://agentpartner.temu.com/ | `https://openapi-b-partner.temu.com/openapi/router` | https://agentseller.temu.com/open/system-manage/client-manage |
| **US** | https://partner-us.temu.com | `https://openapi-b-us.temu.com/openapi/router` | https://agentseller-us.temu.com/open-platform/system-manage/client-manage |
| **EU** | https://partner-eu.temu.com | `https://openapi-b-eu.temu.com/openapi/router` | https://agentseller-eu.temu.com/open-platform/system-manage/client-manage |
| **GLOBAL** | https://partner.temu.com | `https://openapi-b-global.temu.com/openapi/router` | https://agentseller.temu.com/open-platform/system-manage/client-manage |

## 业务场景与区域对应关系

### 全托店铺

| 业务场景 | 使用区域 |
|---------|---------|
| 发品、库存、备货履约 | **CN** |
| 合规资质 | **GLOBAL** |

### 半托店铺

| 业务场景 | 使用区域 |
|---------|---------|
| 半托发品 | **CN** |
| 半托库存、半托调价核价 | **PARTNER** |
| 美国半托履约 | **US** |
| 欧区半托履约 | **EU** |
| 全球(除美国站、欧区)半托履约、合规资质 | **GLOBAL** |

### 本本店铺

| 业务场景 | 使用区域 |
|---------|---------|
| 美国商品、履约 | **US** |
| 欧区商品、履约 | **EU** |
| 其他 | **GLOBAL** |

## 系统实现

### 1. 店铺配置字段

每个店铺可以配置以下字段：

#### 标准区域配置（US/EU/GLOBAL）
- `app_key`: 对应区域的 App Key
- `app_secret`: 对应区域的 App Secret
- `access_token`: 对应区域的 Access Token
- `api_base_url`: 对应区域的接口地址（根据 `region` 字段自动设置）

#### CN 区域配置（商品列表、发品等）
- `cn_access_token`: CN 区域的 Access Token（**用户需要填写**）
- `cn_app_key`: CN 区域的 App Key（**已内置**：`af5bcf5d4bd5a492fa09c2ee302d75b9`）
- `cn_app_secret`: CN 区域的 App Secret（**已内置**：`e4f229bb9c4db21daa999e73c8683d42ba0a7094`）
- `cn_api_base_url`: CN 区域的接口地址（**已内置**：`https://openapi.kuajingmaihuo.com/openapi/router`）

**注意**：CN 区域的 App Key 和 App Secret 已内置在系统中，用户无需在添加店铺时填写，只需要填写 CN Access Token。

### 2. 自动选择逻辑

#### 商品列表、发品等操作
- 如果配置了 `cn_access_token`，系统自动使用 CN 区域的配置
- 使用 `cn_app_key`、`cn_app_secret`、`cn_access_token` 和 `cn_api_base_url`
- API 类型：`bg.goods.list.get`

#### 订单、履约等操作
- 根据店铺的 `region` 字段（US/EU/GLOBAL）使用对应区域的配置
- 使用店铺的 `app_key`、`app_secret`、`access_token` 和 `api_base_url`
- 如果店铺未配置，使用全局配置（需确保区域匹配）

### 3. 配置建议

1. **每个区域需要单独注册账号、申请应用**
2. **确保每个区域的凭证都正确配置**
3. **不要混用不同区域的凭证**
4. **CN 区域配置为可选**，仅在需要商品列表、发品等功能时配置

## 配置示例

### 示例 1：全托店铺（需要发品功能）

```json
{
  "shop_name": "全托店铺",
  "region": "us",
  "access_token": "US区域的access_token",
  "app_key": "US区域的app_key",
  "app_secret": "US区域的app_secret",
  "cn_access_token": "CN区域的access_token",
  "cn_app_key": "CN区域的app_key（可选，有默认值）",
  "cn_app_secret": "CN区域的app_secret（可选，有默认值）"
}
```

### 示例 2：本本店铺（仅订单功能）

```json
{
  "shop_name": "本本店铺",
  "region": "us",
  "access_token": "US区域的access_token",
  "app_key": "US区域的app_key",
  "app_secret": "US区域的app_secret"
}
```

## 常见问题

### Q: 为什么商品列表获取失败？
A: 检查是否配置了 `cn_access_token`，以及 CN 区域的 app_key、secret 是否正确。

### Q: 为什么订单获取失败？
A: 检查店铺的 `region` 字段是否正确，以及对应区域的 app_key、secret、access_token 是否匹配。

### Q: 可以混用不同区域的凭证吗？
A: **不可以**。必须保证接口地址、app_key、secret、access_token 来自同一个区域。

## 参考文档

- [Temu 分区说明文档](https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182)
- [CN 端点支持说明](./CN_ENDPOINT_SUPPORT.md)

