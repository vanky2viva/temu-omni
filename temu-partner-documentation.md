# Temu 合作伙伴平台 API 文档

> **来源**: https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a  
> **提取日期**: 2025-01-27  
> **最后更新时间**: 2025-03-14 19:52:09  
> **文档版本**: v1.0

---

## 📋 文档大纲

本文档全面整理了 Temu 合作伙伴平台 Open API 的完整文档，包括开发者指南、API 参考、接口详细说明等内容。文档结构如下：

### 核心内容

1. **概述** - 介绍 Temu Open API 的主要功能模块和用途
2. **开发者指南** - 包含授权流程、API 调用方法、签名算法、错误码等开发必备信息
3. **授权管理** - OAuth 2.0 授权流程和 Access Token 管理
4. **API 接口文档** - 涵盖 9 大功能模块的完整 API 接口说明：
   - **产品管理** (Product) - 商品发布、查询、更新、删除等
   - **价格管理** (Price) - 价格查询、设置、协商等
   - **订单管理** (Order) - 订单查询、详情获取、状态跟踪等
   - **物流管理** (Logistics) - 物流信息查询、发货确认等
   - **履约管理** (Fulfillment) - 履约信息同步、包裹管理等
   - **退货退款** (Return and Refund) - 售后处理相关接口
   - **促销管理** (Promotion) - 促销活动查询、报名等
   - **Webhook** - 事件通知和消息更新
   - **广告管理** (Ads) - 广告创建、查询、报告等

### 文档特点

- ✅ **完整性** - 涵盖所有公开的 API 接口和指南页面
- ✅ **结构化** - 按功能模块分类，便于查找
- ✅ **实用性** - 包含详细的请求/响应示例、错误码说明
- ✅ **可追溯** - 每个接口都包含直达链接，方便查看最新文档
- ✅ **开发友好** - 提供 Python 代码示例和签名生成方法

### 快速导航

- 🚀 **新手入门** → [开发者指南](#开发者指南-developer-guide) → [卖家授权指南](#卖家授权指南)
- 📦 **产品发布** → [产品 (Product)](#产品-product) → [如何发布商品](#如何发布商品-how-to-release-product-)
- 📝 **API 调用** → [端点和请求方法](#端点和请求方法) → [API 请求签名方法](#api-请求签名方法)
- 🔍 **接口查找** → [API 范围列表](#api-范围列表)

---

## 目录

### 一、概述
- [概述](#概述)
  - [主要功能模块](#主要功能模块)

### 二、开发者指南 (Developer Guide)
- [开发者指南](#开发者指南-developer-guide)
  - [卖家授权指南](#卖家授权指南)
  - [端点和请求方法](#端点和请求方法)
  - [通用参数](#通用参数)
  - [API 请求签名方法](#api-请求签名方法)
  - [限流规则](#限流规则)
  - [通用错误码](#通用错误码)
  - [Temu Open API Python 请求示例（含签名生成）](#temu-open-api-python-请求示例含签名生成)
  - [使用 Postman 调用 API](#使用-postman-调用-api)
  - [沙箱测试店铺](#沙箱测试店铺)

### 三、授权 (Authorization)
- [授权 (Authorization)](#授权-authorization)
  - [授权和授权回调](#授权和授权回调)
  - [bg.open.accesstoken.create](#bgopenaccesstokencreate)
  - [bg.open.accesstoken.info.get](#bgopenaccesstokeninfoget)

### 四、产品 (Product)
- [产品 (Product)](#产品-product)
  - [如何发布商品 (How to release product ?)](#如何发布商品-how-to-release-product-)
  - [接口列表](#接口列表)
    - [商品分类和属性](#商品分类和属性)
    - [商品合规检查](#商品合规检查)
    - [商品模板和图片](#商品模板和图片)
    - [商品库存和状态](#商品库存和状态)
    - [商品查询](#商品查询)
    - [商品操作](#商品操作)
    - [商品外部编号](#商品外部编号)
    - [商品属性和关系](#商品属性和关系)
    - [Temu 特定接口](#temu-特定接口)
    - [其他](#其他)

### 五、价格 (Price)
- [价格 (Price)](#价格-price)
  - [价格指南 (Guide of price)](#价格指南-guide-of-price)
  - [接口列表](#接口列表-1)

### 六、订单 (Order)
- [订单 (Order)](#订单-order)
  - [接口列表](#接口列表-2)
    - [V2 版本接口](#v2-版本接口)
    - [其他订单接口](#其他订单接口)
    - [Temu 订单取消接口](#temu-订单取消接口)

### 七、物流 (Logistics)
- [物流 (Logistics)](#物流-logistics)
  - [接口列表](#接口列表-3)

### 八、履约 (Fulfillment)
- [履约 (Fulfillment)](#履约-fulfillment)
  - [指南页面](#指南页面)
  - [接口列表](#接口列表-4)
    - [履约信息同步](#履约信息同步)
    - [发货相关接口（V2）](#发货相关接口v2)
    - [包裹相关接口](#包裹相关接口)
    - [扫描表单相关接口](#扫描表单相关接口)
    - [取件预约相关接口](#取件预约相关接口)
    - [物流追踪接口](#物流追踪接口)
    - [其他发货接口](#其他发货接口)

### 九、退货退款 (Return and Refund)
- [退货退款 (Return and Refund)](#退货退款-return-and-refund)
  - [接口列表](#接口列表-5)

### 十、促销 (Promotion)
- [促销 (Promotion)](#促销-promotion)
  - [促销活动 API 概览](#促销活动-api-概览)
  - [接口列表](#接口列表-6)

### 十一、Webhook
- [Webhook](#webhook)
  - [Webhook 事件说明 (The event of webhook)](#webhook-事件说明-the-event-of-webhook)
  - [Webhook 事件列表](#webhook-事件列表)
  - [接口列表](#接口列表-7)

### 十二、广告 (Ads)
- [广告 (Ads)](#广告-ads)
  - [广告介绍](#广告介绍)
  - [接口列表](#接口列表-8)

### 十三、API 范围列表
- [API 范围列表](#api-范围列表)
  - [售后相关](#售后相关)
  - [运费相关](#运费相关)
  - [商品相关](#商品相关)
  - [物流相关](#物流相关)
  - [授权相关](#授权相关)
  - [订单相关](#订单相关)
  - [消息相关](#消息相关)

### 十四、Webhook 事件列表
- [Webhook 事件列表](#webhook-事件列表-1)

### 十五、相关链接
- [相关链接](#相关链接)
  - [平台链接](#平台链接)
  - [文档链接](#文档链接)
  - [政策链接](#政策链接)

### 十六、更新日志
- [更新日志](#更新日志)

---

## 概述

Temu 合作伙伴平台提供了一套完整的 Open API，允许 ERP 系统和第三方开发者与 Temu 平台进行集成，实现店铺管理、订单处理、物流跟踪等功能。

### 主要功能模块

- **授权管理**: OAuth 2.0 授权流程
- **产品管理**: 商品信息查询、添加、更新
- **价格管理**: 价格查询和设置
- **订单管理**: 订单查询、详情获取
- **物流管理**: 物流信息查询、发货确认
- **履约管理**: 履约相关操作
- **退货退款**: 售后处理
- **促销管理**: 促销活动管理
- **Webhook**: 事件通知
- **广告管理**: 广告相关功能

---

## 开发者指南 (Developer Guide)

> **来源**: [Developer Guide](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303)

### 卖家授权指南

**最后更新时间**: 2025-01-26 21:08:14  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303)

#### 介绍

对于跨境卖家（Crossborder sellers）和本地卖家（Local sellers），不同类型的卖家需要登录不同的后台进行操作授权。授权意味着卖家使用第三方 ISV（独立软件供应商）。在使用开放平台的 API 功能之前，必须提前获得卖家的授权权限。

#### 卖家授权

不同卖家类型的授权方式如下：

| 卖家类型 | 站点区域 | 授权类型 | 网站 URL |
|---------|---------|---------|---------|
| 跨境卖家 (Crossborder sellers) | US | 手动授权 (Manual) | [https://agentseller.temu.com/open-platform/system-manage/client-manage](https://agentseller.temu.com/open-platform/system-manage/client-manage) |
| 跨境卖家 (Crossborder sellers) | EU | 手动授权 (Manual) | [https://agentseller-eu.temu.com/open-platform/system-manage/client-manage](https://agentseller-eu.temu.com/open-platform/system-manage/client-manage) |
| 本地卖家 (Local sellers) | US | 手动授权 / 回调授权 (Manual / Callback) | [https://seller.temu.com/open-platform/client-manage](https://seller.temu.com/open-platform/client-manage) |
| 本地卖家 (Local sellers) | EU | 手动授权 / 回调授权 (Manual / Callback) | [https://seller-eu.temu.com/open-platform/client-manage](https://seller-eu.temu.com/open-platform/client-manage) |

#### 授权类型

一旦您的应用在应用商店发布，卖家就可以授权它。有两种授权类型：

1. **手动授权 (Manual Authorization)**: 
   - 用户在卖家中心手动授权应用，并选择要授予的权限（定义应用可以访问的 API 范围）。
   - 授权完成后，系统直接向用户显示 access_token。
   - 用户将 access_token 复制到应用中进行配置，开发者保存 access_token 以供后续程序调用。

2. **回调授权 (Callback Authorization)**: 
   - 用户在卖家中心授权应用，并选择要授予的权限（定义应用可以访问的 API 范围）。
   - 授权完成后，会将一个 code 发送到应用预先配置的 redirect_url。
   - 应用的前端获取 code 并传递给后端，后端使用 code 生成 access_token。
   - 此授权方法适用于从应用商店立即安装，提供更好的用户体验，是推荐的方法。

3. **应用内授权 (In-app Authorization)**: 即将推出 (Launch Soon)

#### 授权步骤

##### 本地卖家 (Local Seller)

本地卖家可以访问产品列表、订单列表、订单发货等权限。

授权步骤：

1. 登录本地卖家中心 - 系统管理 - 授权管理页面
   - 链接地址: [https://seller.temu.com/open-platform/client-manage](https://seller.temu.com/open-platform/client-manage)

2. 点击"授权新应用"（Authorize a new app），将显示可用系统列表。

3. 选择应用名称，将显示可以为当前店铺授予所选系统的权限。

4. 点击页面底部的"提交"（Submit），将出现以下屏幕。复制"访问令牌"（Access Token）并粘贴到软件页面以完成配置。

5. 如果应用是"回调授权"（Callback Authorization），点击确定后，您将跳转到应用页面并开始使用。

6. 授权成功后，授权列表中将显示已授权的权限和过期时间。您可以在列表中取消授权应用。

#### 端点和请求方法

**最后更新时间**: 2025-01-26 20:54:21  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=8311de2b2d434e4d805e88413ab815d8](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=8311de2b2d434e4d805e88413ab815d8)

##### 概述

Temu 开放平台基于 HTTPS 协议提供 API 访问。已加入开放平台的开发者（ISV）可以按照以下步骤发出请求并完成 API 调用。以下指南适用于独立实现 API 调用的开发者。

##### API 请求方法

为了整体调用的便利性和安全性，我们移除了许多调用方法，尽管这些方法在某些场景下更方便。目前，我们仅支持 POST 方法进行 API 交互，所有请求方法都使用 POST 方法执行。

##### API 请求端点

如果 Temu 店铺位于美国，请使用美国主机；如果店铺位于欧盟，请使用欧盟请求主机。

| 环境 | URI | 包含的 Temu 站点 |
|------|-----|----------------|
| 生产环境 (Production) | [https://openapi-b-us.temu.com/openapi/router](https://openapi-b-us.temu.com/openapi/router) | 美国 (United States) |
| 生产环境 (Production) | [https://openapi-b-eu.temu.com/openapi/router](https://openapi-b-eu.temu.com/openapi/router) | 德国、意大利、法国、西班牙、英国等 (Germany, Italy, France, Spain, United Kingdom, etc.) |
| 生产环境 (Production) | [https://openapi-b-global.temu.com/openapi/router](https://openapi-b-global.temu.com/openapi/router) | 墨西哥、日本等 (Mexico, Japan etc.) |

#### 通用参数

**最后更新时间**: 2025-01-26 20:58:41  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=6e2b879dff9c424cbde669bf7100d1b7](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=6e2b879dff9c424cbde669bf7100d1b7)

通用参数是调用任何开放 API 时必须传递的参数。当前的通用参数如下：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | STRING | 是 | API 接口名称，例如：bg.* |
| app_key | STRING | 是 | app_key 已成功创建。请联系运营人员发放 |
| timestamp | STRING | 是 | 时间戳，UNIX 时间格式（秒），长度为 10 位数字，当前时间 - 300 秒 <= 输入时间 <= 当前时间 + 300 秒 |
| sign | STRING | 是 | API 输入参数签名，签名值按照以下算法计算 |
| access_token | STRING | 是 | 用户授权令牌 access_token，可从卖家中心获取，运营将发放相应的在线店铺令牌 |
| data_type | STRING | 是 | 请求返回的数据格式，可选参数固定为 JSON |
| version | STRING | 否 | 默认 API 版本为 V1。如果不需要设置，则不传递此参数 |

##### 请求参数

除了通用参数外，如果 API 本身有请求级别的参数，API 请求还必须包含这些参数。有关每个 API 的请求参数的详细说明，请参阅相应的 API 文档。

#### API 请求签名方法

**最后更新时间**: 2025-01-26 20:58:09  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=4a821c90d06442a09e061b0d4316fbf3](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=4a821c90d06442a09e061b0d4316fbf3)

##### 签名方法

为了防止 API 调用过程中的恶意篡改，任何 API 调用都需要携带请求签名。开放平台服务器将根据请求参数验证签名，拒绝非法签名的请求。

当前支持的签名方法是：**MD5** (sign_method = md5)，签名过程如下：

1. 将此请求中的所有请求参数（包括通用参数和请求参数）按 ASCII 格式的首字母升序排序。对于相同的字母，使用下一个字母进行二级排序。字母顺序从左到右，依此类推。

2. 排序结果按照参数名 `$key` 参数值 `$value` 的顺序连接，连接不包含任何字符。

3. 将连接后的字符串进一步连接成一个字符串（包含所有 kv 字符串的长字符串），并在长字符串的头部和尾部连接 `app_secret` 以完成签名字符串的组装。

4. 最后，使用 MD5 方法对签名字符串进行加密，将得到的 MD5 加密密文转换为大写，即为 sign 值。

##### 签名示例

**步骤 1**: 确定请求参数

```json
{
  "sendRequestList": [
    {
      "trackingNumber": "270324232756",
      "carrierId": "699272611",
      "orderSendInfoList": [
        {
          "goodsId": 601099548666279,
          "orderSn": "211-21905473070712792",
          "parentOrderSn": "PO-211-21905452099192792",
          "quantity": 1,
          "skuId": 17592352673534
        }
      ]
    }
  ],
  "sendType": 0
}
```

**步骤 2**: 组装请求参数和通用参数
- 将通用参数添加到 JSON 对象字典中
- 按 ASCII 码使用 `$key` 升序排序
- 字符串连接 `$key` 和 `$value`

连接后的字符串数组：
```
access_token2nifvmpyymvypwmcms5ct4uqqudrwgpmzbcnmkt1jzjkuaf3x56iixym
app_keyf9d5cc9313893a20d5aa85c654e8f503
data_typeJSON
sendRequestList[{"orderSendInfoList":[{"quantity":1,"orderSn":"211-21905473070712792","parentOrderSn":"PO-211-21905452099192792","goodsId":601099548666279,"skuId":17592352673534}],"carrierId":"699272611","trackingNumber":"270324232756"}]
sendType0
timestamp1711009072
typebg.logistics.shipment.confirm
```

**步骤 3**: 无缝连接字符串，连接后在头部和尾部添加 `app_secret`

假设 `app_secret` 是 `c7e0a1a63542be4de3cb5488f9fba8149e8fc290`，连接后的完整字符串：

```
c7e0a1a63542be4de3cb5488f9fba8149e8fc290access_token2nifvmpyymvypwmcms5ct4uqqudrwgpmzbcnmkt1jzjkuaf3x56iixymapp_keyf9d5cc9313893a20d5aa85c654e8f503data_typeJSONsendRequestList[{"orderSendInfoList":[{"quantity":1,"orderSn":"211-21905473070712792","parentOrderSn":"PO-211-21905452099192792","goodsId":601099548666279,"skuId":17592352673534}],"carrierId":"699272611","trackingNumber":"270324232756"}]sendType0timestamp1711009072typebg.logistics.shipment.confirmc7e0a1a63542be4de3cb5488f9fba8149e8fc290
```

**步骤 4**: 从上述连接字符串生成签名 sign
- 使用 MD5 方法对签名进行签名以生成 MD5 签名
- 使用 upperCase 方法将 MD5 签名转换为大写格式

签名结果：`4CCF219942D4180C6DDA3CE36C1B838F`

**步骤 5**: 将 sign 值插入到原始组装的 JSON 中，构建完整的请求体

```json
{
  "app_key": "f9d5cc9313893a20d5aa85c654e8f503",
  "data_type": "JSON",
  "access_token": "2nifvmpyymvypwmcms5ct4uqqudrwgpmzbcnmkt1jzjkuaf3x56iixym",
  "sendRequestList": [
    {
      "carrierId": "699272611",
      "trackingNumber": "270324232756",
      "orderSendInfoList": [
        {
          "goodsId": 601099548666279,
          "skuId": 17592352673534,
          "orderSn": "211-21905473070712792",
          "parentOrderSn": "PO-211-21905452099192792",
          "quantity": 1
        }
      ]
    }
  ],
  "sendType": 0,
  "sign": "4CCF219942D4180C6DDA3CE36C1B838F",
  "timestamp": 1711009072,
  "type": "bg.logistics.shipment.confirm"
}
```

**步骤 6**: 发起 API 请求（以 JSON 数据格式请求为例）

- 请求方法：`POST`
- 请求 URL：`{{host}}`
- 请求头：`content-type: application/json`
- 请求体：见步骤 5 的示例

**cURL 示例**:

```bash
curl -X POST {{host}} \
  -H "Content-Type: application/json" \
  -d '{
    "app_key": "f9d5cc9313893a20d5aa85c654e8f503",
    "data_type": "JSON",
    "access_token": "2nifvmpyymvypwmcms5ct4uqqudrwgpmzbcnmkt1jzjkuaf3x56iixym",
    "sendRequestList": [
      {
        "carrierId": "699272611",
        "trackingNumber": "270324232756",
        "orderSendInfoList": [
          {
            "goodsId": 601099548666279,
            "skuId": 17592352673534,
            "orderSn": "211-21905473070712792",
            "parentOrderSn": "PO-211-21905452099192792",
            "quantity": 1
          }
        ]
      }
    ],
    "sendType": 0,
    "sign": "4CCF219942D4180C6DDA3CE36C1B838F",
    "timestamp": 1711009072,
    "type": "bg.logistics.shipment.confirm"
  }'
```

#### 限流规则

**最后更新时间**: 2025-01-26 21:48:35  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=f2b9f4e869784b46804fe37cea6af1c0](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=f2b9f4e869784b46804fe37cea6af1c0)

为了确保开放平台的稳定运行，我们对 API 请求实施了限流。通常，每个 `app_key` 的初始限流设置为每秒 20 个请求（qps）。

##### 如何查找限流规则？

您可以在我们平台的文档中找到限流规则的相关信息。

##### 如果遇到限流该怎么办？

限流规则是动态可调的。如果您急需增加流量，请及时通过电子邮件 [partner@temu.com](mailto:partner@temu.com) 或其他可用渠道联系我们。

我们将在收到您的请求后紧急评估流量增加的合理性，并根据评估结果相应调整您的流量规则。

#### 通用错误码

**最后更新时间**: 2025-01-26 22:29:04  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=3420761d5dbd4d409f0e41b67634808a](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=3420761d5dbd4d409f0e41b67634808a)

在向 Temu 发出 API 请求时，我们首先在网关层进行验证。此层的错误以以下表格格式提供：

##### 通用错误

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 1000000 | SUCCESS | 成功 |
| 2000000 | BUSINESS_EXCEPTION | 调用内部 API 失败 |
| 3000000 | BAD_PARAMS | 参数错误 |
| 3000001 | SIGN_UNVALID | 签名无效 |
| 3000002 | there is no type in body. | API 类型缺失 |
| 3000003 | type not exists | API 类型状态不存在 |
| 3000004 | type has been sunset, please stop calling this type and change to use another one. | API 类型状态错误 |
| 3000010 | there is no timestamp in body. | 时间戳缺失 |
| 3000011 | timestamp is invalid. | 时间戳无效，如果 timestamp > current_time + 300s |
| 3000012 | timestamp is expired. | 时间戳已过期 |
| 3000013 | there is no data_type in body. | data_type 类型缺失 |
| 3000014 | data_type is invalid | data_type 参数值无效（传递了除 "Json"（不区分大小写）以外的其他字符） |
| 3000019 | there is no client_id in body. | app_key 缺失 |
| 3000020 | client_id not exists. | app_key 不存在 |
| 3000021 | client_id don't have this api permission. | app_key 没有权限调用该 Type 接口 |
| 3000022 | client_id have been suspended, please contact temu product support team to recover your app status. | APP 状态不可用 |
| 3000025 | there is no app_key in body. | app_key 缺失 |
| 3000026 | app_key not exists. | app_key 不存在 |
| 3000027 | app_key don't have this api permission. | app_key 没有权限调用该 Type 接口 |
| 3000028 | app_key have been suspended, please contact temu product support team to recover your app status. | APP 状态不可用 |
| 3000030 | there is no access_token in body. | access_token 缺失 |
| 3000031 | access_token not exists. | access_token 不存在 |
| 3000032 | access_token don't have this api access, please ask for seller to authorize this api in seller center first，and share the new access_token with you. | access_token 没有权限调用该 Type 接口 |
| 3000033 | access_token and app_key are not mapping. | access_token 与 app_key 不匹配 |
| 3000034 | access_token is expired or have been refreshed, please contact seller to share the new access_token with you. | access_token 状态异常 |
| 3000040 | there is no sign in body. | 签名缺失 |
| 4000000 | SYSTEM_EXCEPTION | 系统异常 |
| 4000004 | RATE_LIMIT_EXCEED_EXCEPTION | 请求超过限流阈值 |
| 5000000 | AUTHORIZE_NOT_ALLOW | 商家未授权 / access token 验证失败 / 接口认证失败 |
| 5000001 | ROUTER_NOT_ALLOW | 文件上传路由必须包含 "upload" |
| 5000002 | NOT_SUPPORT_STAGING_ENV | 当前请求环境不是正式环境。请检查请求头信息 |
| 5000003 | NOT_IN_IP_WHITE_LIST | 请求的 IP 地址不在白名单中 |
| 6000001 | RPC_INTERFACE_NOT_FOUND | 内部 API 缺失 |
| 7000000 | BUSINESS_SERVICE_ERROR | 业务服务错误 |

#### Temu Open API Python 请求示例（含签名生成）

**最后更新时间**: 2025-10-27 21:50:03  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=2d81829fcbbc4058b95f695440e75236](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=2d81829fcbbc4058b95f695440e75236)

此示例演示如何在 Python 中调用 Temu Open API 接口，包括如何组装请求参数、生成请求签名以及将签名的请求发送到 Temu 服务器。

该示例包含两个文件：

1. **TestSign.py**
   - 实现 Temu Open API 所需的签名生成算法
   - `api_sign_method(app_secret, request_params)` 函数使用 **MD5** (api_sign_method = md5)，签名过程如下：
     - 将此请求中的所有请求参数（包括通用参数和请求参数）按 ASCII 格式的首字母升序排序
     - 排序结果按照参数名 `$key` 参数值 `$value` 的顺序连接
     - 将连接后的字符串进一步连接成一个字符串，并在长字符串的头部和尾部连接 `app_secret`
     - 使用 MD5 方法对签名字符串进行加密，将得到的 MD5 加密密文转换为大写

2. **TestRequestwithSign.py**
   - 展示在"沙箱测试店铺"环境下使用测试应用和测试店铺调用 Temu API 的完整示例
   - 执行步骤：
     - 定义应用凭证（`app_key`、`app_secret`、`access_token`）
     - 设置美国端点（适用于在美国注册的应用和店铺）
     - 定义通用参数（参考 `bg.local.goods.cats.get` API 参考）
     - 添加请求特定的必需参数（例如，用于类别查询的 `parentCatId`）
     - 将两个参数集合并到一个字典中
     - 使用 `TestSign.py` 中的方法生成 `sign`
     - 将签名的有效负载发送 POST 请求到 Temu Open API 端点
     - 打印 API 返回的格式化 JSON 响应

此示例帮助开发者理解在集成 Temu Open API 时的正确参数组装、签名生成过程和请求格式。

##### TestSign.py

```python
import json
import hashlib

def api_sign_method(app_secret, request_params):
    temp = []
    # Sort parameters by key
    request_params = sorted(request_params.items())
    for k, v in request_params:
        v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        temp.append(str(k) + str(v.strip('"')))
    un_sign = ''.join(temp)
    un_sign = str(app_secret) + un_sign + str(app_secret)
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    return sign
```

##### TestRequestwithSign.py

```python
import requests
import json
import time
import TestSign as testSign

# US Test App & Test mall in "Sandbox Test Shops"
app_secret = "4782d2d827276688bf4758bed55dbdd4bbe79a79"
app_key = "4ebbc9190ae410443d65b4c2faca981f"
access_token = "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7"

# US Endpoints for shops located in US and app registered in US
url = "https://openapi-b-us.temu.com/openapi/router?app_secret=" + app_secret

# Common Params
type = "bg.local.goods.cats.get"
version = "V1"
data_type = "JSON"
timestamp = int(time.time())

common_params = {
    "app_key": app_key,
    "data_type": data_type,
    "access_token": access_token,
    "timestamp": timestamp,
    "type": type,
    "version": version
}

# Request Params
parentCatId = 0
request_params = {
    "parentCatId": parentCatId
}

# Before sign Params
before_sign_request = {**common_params, **request_params}

# Sign the request
sign = testSign.api_sign_method(app_secret, before_sign_request)

# Initiate an API request
headers = {
    "Content-Type": "application/json"
}

request_payload = {
    **before_sign_request,
    "sign": sign
}

response = requests.post(url, headers=headers, data=json.dumps(request_payload))

try:
    response_json = response.json()
    formatted_json = json.dumps(response_json, indent=4, ensure_ascii=False)
    print(formatted_json)
except json.JSONDecodeError:
    print("Response is not in JSON format:")
    print(response.text)
```

#### 使用 Postman 调用 API

**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=d221eb4428114e46b91f0e99277891ec](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=d221eb4428114e46b91f0e99277891ec)

> **注意**: 此页面需要登录才能查看完整内容。请访问上述链接查看详细的 Postman 使用指南。

#### 沙箱测试店铺

**直达链接**: [https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=9cf457c922fe4b33b93c23ab1d8b15d0](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=9cf457c922fe4b33b93c23ab1d8b15d0)

> **注意**: 此页面需要登录才能查看完整内容。请访问上述链接查看沙箱测试店铺的详细信息。

---

## 授权 (Authorization)

### 授权和授权回调

**最后更新时间**: 2025-03-14 19:52:09  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a)

#### 概述

授权是使用 Open API 的重要步骤。ERP 需要获得卖家的授权才能调用非公开的 API，这些 API 是店铺管理所必需的。

#### 什么是授权回调

授权回调不会直接返回令牌，需要通过 code 来交换令牌。

**两种授权方式**:

1. **卖家内部系统 (Seller In House System)**: 通过运营反馈授权回调地址
2. **企业资源规划 (Enterprise Resource Planning)**: 在开放平台上填写授权重定向 URL 地址

**配置重定向 URL**:

根据不同地区，需要在对应的平台配置重定向 URL：

- **US（美国）**: https://partner-us.temu.com/app/app-mgmt/detail/edit?app_key={{your appkey}}
- **Global（全球）**: https://partner.temu.com/app/app-mgmt/detail/edit?app_key={{your appkey}}
- **EU（欧洲）**: https://partner-eu.temu.com/app/app-mgmt/detail/edit?app_key={{your appkey}}

> **注意**: 您需要在 App 中编辑 `redirect_url` 字段来配置回调地址。请注意，一旦配置，将在 App Store 上立即生效。

#### 如何获取 Code

商家可以像直接授权一样前往卖家中心进行授权。授权后，前端页面将重定向到您授权链接中的重定向 URL，例如：

```
https://seller.temu.com/?code=xxxxxx
```

卖家授予授权后，开放平台会将授权码返回到回调地址重定向 URL。然后 ERP 可以使用该 code 首次获取 access_token。

#### 如何获取 AccessToken

成功授权后，使用重定向 URL 中的 code 调用此 API（`bg.open.accesstoken.create`）。这将帮助您获取 `mall_id` 和 `access_token`。

> **注意**: 首次调用接口时，`token` 等于 `code`。

**API 参考**: `bg.open.accesstoken.create`

**请求示例**:

```json
{
  "access_token": "uplmntfsagmk84f4fm6grdjwm5nvugxqclvzl8b7uyxp04qfxskkoveopgz",
  "app_key": "1024",
  "code": "uplmntfsagmk84f4fm6grdjwm5nvugxqclvzl8b7uyxp04qfxskkoveopgz",
  "data_type": "JSON",
  "sign": "A03C3D255210263CDE6A56FAEEA008AB",
  "timestamp": 1734098171,
  "type": "bg.open.accesstoken.create"
}
```

**响应示例**:

```json
{
  "errorCode": 1000000,
  "errorMsg": "",
  "requestId": "us-0b0bfc9c-f61d-4530-b1a3-bb19704de637",
  "result": {
    "accessToken": "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7",
    "apiScopeList": [
      "bg.aftersales.aftersales.list.get",
      "bg.aftersales.parentaftersales.list.get",
      "bg.aftersales.parentreturnorder.get",
      "bg.freight.template.list.query",
      "bg.local.compliance.goods.list.query",
      "bg.local.goods.add",
      "bg.local.goods.brand.trademark.get",
      "bg.local.goods.category.recommend",
      "bg.local.goods.cats.get",
      "bg.local.goods.compliance.edit",
      "bg.local.goods.compliance.extra.template.get",
      "bg.local.goods.compliance.property.check",
      "bg.local.goods.compliance.rules.get",
      "bg.local.goods.gallery.signature.get",
      "bg.local.goods.list.query",
      "bg.local.goods.out.sn.check",
      "bg.local.goods.out.sn.set",
      "bg.local.goods.partial.update",
      "bg.local.goods.priceorder.accept",
      "bg.local.goods.priceorder.change.sku.price",
      "bg.local.goods.priceorder.negotiate",
      "bg.local.goods.priceorder.query",
      "bg.local.goods.property.get",
      "bg.local.goods.publish.status.get",
      "bg.local.goods.sale.status.set",
      "bg.local.goods.size.element.get",
      "bg.local.goods.sku.list.price.query",
      "bg.local.goods.sku.list.query",
      "bg.local.goods.sku.out.sn.check",
      "bg.local.goods.sku.out.sn.set",
      "bg.local.goods.spec.id.get",
      "bg.local.goods.stock.edit",
      "bg.local.goods.template.get",
      "bg.local.goods.update",
      "bg.logistics.companies.get",
      "bg.logistics.shipment.confirm",
      "bg.logistics.shipment.create",
      "bg.logistics.shipment.document.get",
      "bg.logistics.shipment.get",
      "bg.logistics.shipment.result.get",
      "bg.logistics.shipment.shippingtype.update",
      "bg.logistics.shipment.sub.confirm",
      "bg.logistics.shipment.update",
      "bg.logistics.shippingservices.get",
      "bg.logistics.warehouse.list.get",
      "bg.open.accesstoken.info.get",
      "bg.order.amount.query",
      "bg.order.combinedshipment.list.get",
      "bg.order.detail.get",
      "bg.order.list.get",
      "bg.order.shippinginfo.get",
      "bg.tmc.message.update"
    ],
    "appSubscribeEventCodeList": [
      "bg_open_event_test",
      "bg_order_status_change_event",
      "bg_trade_logistics_address_changed",
      "bg_aftersales_status_change",
      "bg_cancel_order_status_change"
    ],
    "appSubscribeStatus": 0,
    "authEventCodeList": [],
    "expiredTime": 1765634102,
    "mallId": 1024
  },
  "success": true
}
```

**响应字段说明**:

- `accessToken`: 访问令牌
- `mallId`: 商城 ID
- `apiScopeList`: 已授权的 API 范围列表
- `appSubscribeEventCodeList`: 订阅的事件代码列表
- `expiredTime`: 过期时间（Unix 时间戳）

### bg.open.accesstoken.create

**最后更新时间**: 2025-07-10 10:03:12  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=82674d12ebe64af2820d62ebbc2ecc16](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=82674d12ebe64af2820d62ebbc2ecc16)

**接口描述**: Temu 的授权回调接口允许开发者在用户成功授权其应用程序时接收通知。用户授予权限后，Temu 将使用授权码重定向回开发者指定的回调 URL。使用此 API 请求访问令牌。

**接口类型**: Local / Cross Border

#### 请求 URL

| 请求 URL | 站点区域 |
|---------|---------|
| POST https://openapi-b-us.temu.com/openapi/router | US |

#### 通用参数

所有 API 请求都需要包含以下通用参数：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | STRING | 是 | API 名称，例如：bg.* |
| app_key | STRING | 是 | 应用密钥 |
| access_token | STRING | 是 | 用于访问控制的安全令牌 |
| sign | STRING | 是 | 签名 |
| timestamp | STRING | 是 | 时间戳，UNIX 时间格式（秒），长度为 10 位数字，应在当前时间前后 300 秒范围内 |
| data_type | STRING | 否 | 请求响应的数据格式固定为 JSON，可选参数 |
| version | STRING | 否 | API 版本，默认为 V1，如不需要可不传此参数 |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| request | OBJECT | 否 | 请求对象 |
| code | STRING | 否 | 用于获取访问令牌的代码。临时授权码只能使用一次，10 分钟后过期 |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| response | OBJECT | 响应对象 |
| success | BOOLEAN | API 响应中返回的成功或失败状态：true 表示成功，false 表示失败 |
| errorCode | INTEGER | API 响应中返回的失败状态码 |
| errorMsg | STRING | API 响应中返回的失败消息。失败原因将在消息中描述 |
| result | OBJECT | 具体返回信息 |

**result 对象包含以下字段**:

- `regionId`: 区域 ID
- `mallId`: 商城 ID
- `appSubscribeEventCodeList`: 应用订阅事件代码列表
- `appSubscribeStatus`: 应用订阅状态
- `authEventCodeList`: 授权事件代码列表
- `accessToken`: 访问令牌
- `associatedMallTokenList`: 关联商城令牌列表
- `expiredTime`: 过期时间（Unix 时间戳）
- `mallType`: 商城类型
- `apiScopeList`: API 范围列表

#### 请求示例

**cURL**:

```bash
curl -X POST \
'https://openapi-b-us.temu.com/openapi/router' \
 -H 'content-type: application/json' \
 -d '{
  "access_token" : "test",
  "app_key" : "test",
  "code" : "test",
  "sign" : "test",
  "data_type" : "test",
  "type" : "test",
  "version" : "test",
  "timestamp" : "test"
}'
```

#### 响应示例

```json
{
  "result": {
    "regionId": 1,
    "mallId": 1,
    "appSubscribeEventCodeList": [
      "test",
      "test"
    ],
    "appSubscribeStatus": 1,
    "authEventCodeList": [
      {
        "eventCode": "test",
        "permitsStatus": 1
      }
    ],
    "accessToken": "test",
    "associatedMallTokenList": [
      {
        "accessToken": "test",
        "mallId": 1
      }
    ],
    "expiredTime": 1,
    "mallType": 1,
    "apiScopeList": [
      "test",
      "test"
    ]
  },
  "errorCode": 1,
  "success": true,
  "errorMsg": "test"
}
```

#### 错误码

| 错误码 | 错误消息 | 错误 SOP |
|--------|---------|---------|
| 110020001 | System error, please try again. | - |
| 110020002 | Invalid code, please check and try again. | - |
| 110020003 | The error occurred when creating access token, please authorize again. | - |

#### 权限包

| 权限包 | 应用类型 |
|--------|---------|
| Local Basic Management | private, public |
| Semi Basic Management | private, public |

#### 限流规则

> 待补充限流规则详情

### bg.open.accesstoken.info.get

**最后更新时间**: 2025-07-10 10:03:12  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=93de550b56c8417caccb88824be3e614](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=93de550b56c8417caccb88824be3e614)

**接口描述**: 此接口允许商家查看与其当前授权令牌关联的 API 权限，提供已授权的 API 端点列表。

**接口类型**: Local / Cross Border

#### 请求 URL

| 请求 URL | 站点区域 |
|---------|---------|
| POST https://openapi-b-us.temu.com/openapi/router | US |

#### 通用参数

所有 API 请求都需要包含以下通用参数（与 `bg.open.accesstoken.create` 相同）：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | STRING | 是 | API 名称，例如：bg.* |
| app_key | STRING | 是 | 应用密钥 |
| access_token | STRING | 是 | 用于访问控制的安全令牌 |
| sign | STRING | 是 | 签名 |
| timestamp | STRING | 是 | 时间戳，UNIX 时间格式（秒），长度为 10 位数字，应在当前时间前后 300 秒范围内 |
| data_type | STRING | 否 | 请求响应的数据格式固定为 JSON，可选参数 |
| version | STRING | 否 | API 版本，默认为 V1，如不需要可不传此参数 |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| request | OBJECT | 否 | 请求对象（此接口无需额外请求参数） |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| response | OBJECT | 响应对象 |
| success | BOOLEAN | API 响应中返回的成功或失败状态：true 表示成功，false 表示失败 |
| errorCode | INTEGER | API 响应中返回的失败状态码 |
| errorMsg | STRING | API 响应中返回的失败消息。失败原因将在消息中描述 |
| result | OBJECT | 具体返回信息 |

**result 对象包含以下字段**:

- `regionId`: 区域 ID
- `mallId`: 商城 ID
- `appSubscribeEventCodeList`: 应用订阅事件代码列表
- `appSubscribeStatus`: 应用订阅状态
- `authEventCodeList`: 授权事件代码列表
- `expiredTime`: 过期时间（Unix 时间戳）
- `mallType`: 商城类型
- `apiScopeList`: API 范围列表（已授权的 API 端点列表）

#### 请求示例

**cURL**:

```bash
curl -X POST \
'https://openapi-b-us.temu.com/openapi/router' \
 -H 'content-type: application/json' \
 -d '{
  "access_token" : "test",
  "app_key" : "test",
  "sign" : "test",
  "data_type" : "test",
  "type" : "test",
  "version" : "test",
  "timestamp" : "test"
}'
```

#### 响应示例

```json
{
  "result": {
    "regionId": 1,
    "mallId": 1,
    "appSubscribeEventCodeList": [
      "test",
      "test"
    ],
    "appSubscribeStatus": 1,
    "authEventCodeList": [
      {
        "eventCode": "test",
        "permitsStatus": 1
      }
    ],
    "expiredTime": 1,
    "mallType": 1,
    "apiScopeList": [
      "test",
      "test"
    ]
  },
  "errorCode": 1,
  "success": true,
  "errorMsg": "test"
}
```

#### 错误码

此接口暂无特定错误码。

#### 权限包

| 权限包 | 应用类型 |
|--------|---------|
| Local Basic Management | private, public |
| Semi Basic Management | private, public |
| Cross Border Basic Management | private, public |

#### 限流规则

> 待补充限流规则详情

---

## 产品 (Product)

Product 模块提供了商品管理的完整 API 接口，包括商品添加、更新、查询、删除、合规检查等功能。

### 如何发布商品 (How to release product ?)

**最后更新时间**: 2025-10-20 22:20:35  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=4ab5cfac8bf444d882acfc1f64859f5d](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=4ab5cfac8bf444d882acfc1f64859f5d)

#### 概述

Product API 帮助卖家大规模管理其产品目录。使用 Product API，卖家可以创建产品。

以下是产品发布涉及的字段值和 API 调用的说明。我们希望本文档能帮助您更高效地发布产品。

#### 产品发布涉及的接口

| API 名称 | 接口概述 |
|---------|---------|
| `bg.local.goods.cats.get` | 获取 Temu 的完整分类 |
| `bg.local.goods.template.get` | 获取与 Temu 分类对应的属性/变体数据 |
| `bg.local.goods.spec.id.get` | 用于生成自定义变体规格 ID |
| `bg.local.goods.size.element.get` | 是否填写尺寸表和获取类目的要求 |
| `bg.local.goods.image.upload` | 上传产品图片 |
| `bg.local.goods.gallery.signature.get` | 上传产品视频、文件和图片 |
| `bg.local.goods.compliance.property.check` | 验证产品属性是否符合站点的销售规则 |
| `bg.local.goods.tax.code.get` | 获取产品税码 |
| `bg.local.goods.out.sn.check` / `bg.local.goods.sku.out.sn.check` | 验证外部产品代码和 SKU 代码是否重复 |
| `bg.freight.template.list.query` | 获取卖家设置的产品运费模板 |
| `temu.local.goods.brand.trademark.V2.get` | 获取卖家注册的品牌信息 |
| `temu.local.goods.sku.net.content.unit.query` | 获取 SKU 净含量单位信息 |
| `temu.local.goods.illegal.vocabulary.check` | 验证产品名称、产品描述等信息是否存在违规 |
| `bg.local.goods.compliance.rules.get` / `bg.local.goods.compliance.extra.template.get` | 用于查询产品合规和治理属性要求 |
| `bg.local.goods.compliance.info.fill.list.query` | 用于获取产品合规信息并填写 |
| `bg.local.goods.add` | 创建新产品 |

#### 产品发布注意事项

##### 必填属性说明

| 属性 | 必填 | 如何填写 | 注意事项 |
|------|------|---------|---------|
| `goodsBasic` | True | - | - |
| `goodsName` | True | 用户输入 | **验证规则**：<br>- 仅支持英文字母、数字和符号<br>- 不支持装饰字符：~ ! * $ ? _ ~ { } # < > \| * ; ^ ¬ ¦<br>- 不支持高 ASCII 字符类型 1，如 ®, ©, ™ 等<br>- 字符数：500 字符以内<br>- 建议使用 `temu.local.goods.illegal.vocabulary.check` 接口检查产品信息是否存在违规，以避免影响销售 |
| `catId` | True | 从其他 API 获取<br>`bg.local.goods.cats.get`<br>`bg.local.goods.category.recommend` | **重要**：<br>- 输入 `parentCatId=0` 可获取所有可用的第一级分类<br>- 要获取叶子分类：递归调用此接口，输入 `parentCatId` 为上一次调用结果中选择的 `catId`，直到获取到叶子分类<br>- 输入叶子分类时，接口返回为空<br>- 必须使用最具体的（叶子）分类 ID 发布产品<br>- `catType` 是判断分类是服装（`catType=0`）还是非服装（`catType=1`）的重要变量，会影响图片要求的形状<br>- 不同站点上的某些分类不可销售，只有 `availableStatus=0` 的分类需要获取 |
| `goodsGallery` | False | - | - |
| `detailVideo` | False | 用户输入 | - 最大视频 URI 数量：1<br>- 时长：≤180s<br>- 宽高比：1:1, 4:3, 16:9<br>- 分辨率：≥720P<br>- 大小：≤300 MB<br>- 格式：wmv, avi, 3gp, mov, mp4, flv, rmvb, mkv, m4v, x-flv, WMV, AVI, 3GP, MOV, MP4, FLV, RMVB, MKV, M4V, X-FLV<br>- 上传需要额外调用视频上传接口 |
| `detailImage` | False | 用户输入 | - 最大图片 URI 数量：49<br>- 宽高比：≥1:3<br>- 宽度：≥480px<br>- 高度：≥480px<br>- 大小：≤3 MB<br>- 格式：JPEG, JPG, PNG<br>- 图片上传需要额外调用 `bg.local.goods.image.upload` 进行转换 |
| `carouselVideo` | False | 用户输入 | - 数量：≤1<br>- 宽高比：无限制<br>- 时长：≤60s<br>- 分辨率：≥720P<br>- 大小：≤100MB<br>- 格式：wmv, avi, 3gp, mov, mp4, flv, rmvb, mkv, m4v, x-flv, WMV, AVI, 3GP, MOV, MP4, FLV, RMVB, MKV, M4V, X-FLV |
| `outGoodsSn` | False | 用户输入 | - 用于关联 TEMU 和外部电商平台之间的 SKU<br>- 必须在店铺内唯一<br>- 最大长度：100 个字符<br>- 请不要在 SKU 中使用前导或尾随空格<br>- 可使用 `bg.local.goods.out.sn.check` 接口验证卖家的产品是否有重复的商品代码 |
| `goodsServicePromise` | True | - | - |
| `shipmentLimitDay` | True | 用户输入 | 表示从收到商品订单到可以发货之间的时间（以天为单位）。默认生产时间为 1 或 2 天 |
| `fulfillmentType` | True | 用户输入 | 配送方式：1 - 自配送，固定设置为 1 |
| `costTemplateId` | True | 从其他 API 获取<br>`bg.freight.template.list.query` | 用户需要前往卖家中心创建运费模板页面，此接口才能返回相应的数据 |
| `goodsProperty` | True | 从其他 API 获取<br>`bg.local.goods.template.get` | **重要且复杂的信息**：<br>- 确定字段 `isSale=false` 是普通属性还是 `isSale=true` 是变体属性<br>- 此数组用于设置关于 `isSale=false` 的产品数据<br>- **必填属性必须传入**，通过 `bg.local.goods.template.get` 中的 `required=True` 判断<br>- 存在父子关系属性。当父属性选择值时，必须传入子属性<br>  - `showType = 0`：父属性<br>  - `showType = 1`：子属性<br>- 子属性根据父属性的 `controlType` 出现。如果 `controlType = 0`，`showCondition` 将指示根据父属性值触发子属性的条件<br>- 如果 `controlType` 是 "1"、"3" 或 "16"，`templatePropertyValueParentList` 将决定何时触发子属性<br>- 有单位的属性应在 `valueUnitList` 可用时同时包含 `valueUnitId` 和 `valueUnit` |

### 接口列表

#### 商品基础操作
- `temu.local.goods.baseprice.recommend` - 获取商品基础价格推荐  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.brand.trademark.V2.get` - 获取品牌商标信息（V2）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.illegal.vocabulary.check` - 检查非法词汇  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.sku.net.content.unit.query` - 查询 SKU 净含量单位  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.delete` - 删除商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.sku.list.retrieve` - 检索 SKU 列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.list.retrieve` - 检索商品列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.spec.info.get` - 获取规格信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品分类和属性
- `bg.local.goods.spec.id.get` - 获取规格 ID  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.size.element.get` - 获取尺寸元素  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.cats.get` - 获取商品分类  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.category.recommend` - 获取推荐分类  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.category.check` - 检查分类  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.get` - 获取商品属性  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.relations` - 商品属性关联  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.relations.level.template` - 商品属性关联级别模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.relations.template` - 商品属性关联模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品合规
- `bg.local.goods.compliance.extra.template.get` - 获取合规额外模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.rules.get` - 获取合规规则  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.property.check` - 检查合规属性  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.edit` - 编辑商品合规信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.compliance.goods.list.query` - 查询合规商品列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品模板和图片
- `bg.local.goods.template.get` - 获取商品模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.gallery.signature.get` - 获取图库签名  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.image.upload` - 上传商品图片  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.videocoverimage.get` - 获取视频封面图片  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品库存和状态
- `bg.local.goods.stock.edit` - 编辑商品库存  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sale.status.set` - 设置商品销售状态  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.publish.status.get` - 获取商品发布状态  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品查询

##### bg.local.goods.list.query - 查询商品列表

**最后更新时间**: 2025-07-04 09:38:13  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=860a51f023a042a2805211f658119536](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=860a51f023a042a2805211f658119536)

**接口描述**: Get product list（获取商品列表）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `pageNo` | INTEGER | 是 | 页码，用于分页 |
| `pageSize` | INTEGER | 是 | 每页大小，表示每页返回的记录数，每页限制 100 条 |
| `orderField` | STRING | 否 | 排序字段。支持按 goodsId、createTime、goodsName、outGoodsSn、quantity、price 排序。默认按创建时间排序 |
| `orderType` | INTEGER | 否 | 排序类型。0 为降序，1 为升序。默认降序 |
| `goodsSearchType` | INTEGER | 是 | 商品状态筛选：1 - 已上架/已下架 4 - 未发布 5 - 草稿 6 - 已删除 |
| `searchText` | STRING | 否 | 搜索文本，支持按 goodName 或 goodsId 搜索 |
| `statusFilterType` | INTEGER | 否 | 子状态筛选类型。请参考商品状态描述 |
| `crtFrom` | LONG | 否 | 创建开始时间，输入时间戳，13 位毫秒 |
| `crtTo` | LONG | 否 | 创建结束时间，输入时间戳，13 位毫秒 |
| `goodsIdList` | LONG[] | 否 | 商品 ID 列表 |
| `catIdList` | LONG[] | 否 | 分类 ID 列表，支持叶子分类和非叶子分类 ID，支持批量 |
| `goodsStatusFilterType` | INTEGER | 是 | 商品状态筛选（新版本字段） |
| `goodsSubStatusFilterType` | INTEGER | 否 | 商品子状态筛选（新版本字段） |
| `goodsStatusChangeTimeFrom` | LONG | 否 | 商品状态变更开始时间，通过时间戳传参 |
| `goodsStatusChangeTimeTo` | LONG | 否 | 商品状态变更结束时间，通过时间戳传参 |
| `goodsSearchTags` | INTEGER[] | 否 | 商品搜索标签：1-低流量，4-限流 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 请求成功状态：成功返回 True，否则返回 False |
| `errorCode` | INTEGER | 错误码：用于参考下面的错误码，可以帮助找到每个错误对应的解决方案 |
| `errorMsg` | STRING | 错误消息：与错误码对应的反馈内容 |
| `result` | OBJECT | 响应结果对象 |
| `result.goodsList` | OBJECT[] | 商品列表 |
| `result.goodsList[].goodsId` | LONG | 商品 ID |
| `result.goodsList[].goodsName` | STRING | 商品名称 |
| `result.goodsList[].outGoodsSn` | STRING | 商品外部编号 |
| `result.goodsList[].catId` | LONG | 分类 ID |
| `result.goodsList[].price` | STRING | 价格 |
| `result.goodsList[].currency` | STRING | 货币 |
| `result.goodsList[].quantity` | INTEGER | 库存数量 |
| `result.goodsList[].thumbUrl` | STRING | 缩略图 URL |
| `result.goodsList[].skuInfoList` | OBJECT[] | SKU 信息列表 |
| `result.pageNo` | INTEGER | 当前页码 |
| `result.total` | INTEGER | 总记录数 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 150010003 | Invalid Request Parameters | 无效的请求参数 |
| 150010005 | Try again later | 请稍后重试 |

**权限包**: 
- `Local Product Management` (private, public)
- `WMS Local Product Management` (public)

**限流规则**: AppKey: 20次/1秒

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

- `bg.local.goods.sku.list.query` - 查询 SKU 列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.detail.query` - 查询商品详情  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品操作

##### bg.local.goods.add - 添加商品

**最后更新时间**: 2025-10-30 19:03:25  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=b68f47b094e7469eab7cf58c2b7cf0c6](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=b68f47b094e7469eab7cf58c2b7cf0c6)

**接口描述**: Add New Items On Temu（在 Temu 上添加新商品）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `goodsBasic` | OBJECT | 是 | 商品基本信息 |
| `goodsServicePromise` | OBJECT | 是 | 卖家服务信息 |
| `goodsProperty` | OBJECT | 是 | 商品属性 |
| `goodsOriginInfo` | OBJECT | 否 | 原产国/地区信息 |
| `bulletPoints` | STRING[] | 否 | 商品卖点 |
| `goodsDesc` | STRING | 否 | 商品描述：用于详细商品展示装饰 |
| `certificationInfo` | OBJECT | 否 | 商品认证信息列表 |
| `guideFileInfo` | OBJECT | 否 | 使用说明书 |
| `goodsSizeChartList` | OBJECT | 否 | 尺寸表信息 |
| `goodsSizeImage` | STRING[] | 否 | 尺寸表图片 URL |
| `skuList` | OBJECT[] | 是 | SKU 列表 |
| `goodsTrademark` | OBJECT | 否 | 商标信息 |
| `taxCodeInfo` | OBJECT | 否 | 税码信息 |
| `goodsVehiclePropertyRelation` | OBJECT | 否 | 车辆基础数据 |
| `secondHand` | OBJECT | 否 | 二手商品信息 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 请求成功状态：成功返回 True，否则返回 False |
| `errorCode` | INTEGER | 错误码：用于参考下面的错误码，可以帮助找到每个错误对应的解决方案 |
| `errorMsg` | STRING | 错误消息：与错误码对应的反馈内容 |
| `result` | OBJECT | 响应结果对象 |
| `result.goodsId` | INTEGER | 商品 ID |
| `result.productType` | INTEGER | 商品类型 |
| `result.skuInfoList` | OBJECT[] | SKU 信息列表 |
| `result.skuInfoList[].skuId` | INTEGER | SKU ID |
| `result.skuInfoList[].outSkuSn` | STRING | SKU 外部编号 |
| `result.skuInfoList[].specList` | OBJECT[] | 规格列表 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 150010238 | The "productType" does not exist. Please check and try again. | 产品类型不存在 |
| 150011013 | Used-product shop do not support the listing of custom products. | 二手商品店铺不支持定制产品 |
| 150011015 | Refurbished product shop do not support the listing of custom products. | 翻新产品店铺不支持定制产品 |
| 150011057 | "Made-to-order" feature is only available to select qualified sellers. | 定制功能仅对符合条件的卖家开放 |
| 150011059 | "Made-to-order products" are mutually exclusive with other product types. | 定制产品与其他产品类型互斥 |
| 150011027 | The product is missing tax code information. | 商品缺少税码信息 |
| 150010237 | The newly added specification information is missing in the goods properties. | 商品属性中缺少新添加的规格信息 |
| 150010236 | SKC must not exceed 25 | SKC 不能超过 25 |
| 150010235 | Please enter template name of size charts | 请输入尺寸表模板名称 |
| 150010234 | The property value of the charger type is invalid. | 充电器类型的属性值无效 |

**权限包**: `bg.local.goods.add`

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

- `bg.local.goods.update` - 更新商品   
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=7dd781cddbd440c490c0312bc8d5aa0d) - 直达链接
- `bg.local.goods.partial.update` - 部分更新商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品外部编号
- `bg.local.goods.sku.out.sn.check` - 检查 SKU 外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sku.out.sn.set` - 设置 SKU 外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.out.sn.set` - 设置商品外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.out.sn.check` - 检查商品外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 商品属性和关系
- `bg.local.goods.property.relations` - 商品属性关系  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.relations.level.template` - 商品属性关系级别模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.property.relations.template` - 商品属性关系模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.category.check` - 检查分类  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### Temu 特定接口
- `temu.local.goods.baseprice.recommend` - 推荐基础价格  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.brand.trademark.V2.get` - 获取品牌商标V2  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.illegal.vocabulary.check` - 检查非法词汇  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.sku.net.content.unit.query` - 查询SKU净含量单位  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.delete` - 删除商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.sku.list.retrieve` - 检索SKU列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.list.retrieve` - 检索商品列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `temu.local.goods.spec.info.get` - 获取规格信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

#### 其他
- `bg.local.goods.tax.code.get` - 获取商品税码  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.freight.template.list.query` - 查询运费模板列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。由于接口数量较多，本文档仅列出接口名称和简要说明。如需详细信息，请访问对应的接口文档页面。

---

## 价格 (Price)

Price 模块提供了价格管理相关的 API 接口。

### 价格指南 (Guide of price)

**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找 "Guide of price"

### 接口列表

- **Guide of price** - 价格指南  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找

#### temu.local.goods.recommendedprice.query - 查询推荐价格

**最后更新时间**: 2025-06-30 13:40:27  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=2e473e289f2541c1b2b2318d841e0f25](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=2e473e289f2541c1b2b2318d841e0f25)

**接口描述**: Support merchants in querying the recommended supply prices.（支持商家查询推荐的供货价格）

**适用店铺类型**: Local（本地店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `language` | STRING | 否 | 语言 |
| `recommendedPriceType` | INTEGER | 是 | 推荐价格类型：10-低流量，20-限流 |
| `goodsIdList` | LONG[] | 是 | 搜索参数：商品 ID 列表。列表大小应在 1 到 100 之间 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 是否成功 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 具体信息 |
| `result.goodsList` | OBJECT[] | 商品列表 |
| `result.goodsList[].goodsId` | LONG | 商品 ID |
| `result.goodsList[].skuList` | OBJECT[] | SKU 列表 |
| `result.goodsList[].skuList[].skuId` | LONG | SKU ID |
| `result.goodsList[].skuList[].recommendedSupplyPrice` | OBJECT | 推荐供货价格 |
| `result.goodsList[].skuList[].recommendedSupplyPrice.amount` | STRING | 金额 |
| `result.goodsList[].skuList[].recommendedSupplyPrice.currency` | STRING | 货币 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 150010002 | System error, please try again later | 系统错误，请稍后重试 |
| 150010003 | Invalid Request Parameters | 无效的请求参数 |

**权限包**: 
- `Local Price Management` (private, public)

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。
- `temu.local.goods.appealorder.record.query` - 查询申诉订单记录  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `temu.local.goods.appealorder.create` - 创建申诉订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `temu.local.goods.appealorder.query` - 查询申诉订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `temu.local.goods.priceorder.reject` - 拒绝价格订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
#### bg.local.goods.sku.list.price.query - 查询 SKU 价格列表

**最后更新时间**: 2025-07-01 21:55:37  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=94c62a5e74ee427cb114609026aad12d](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=94c62a5e74ee427cb114609026aad12d)

**接口描述**: This is an API for batch querying the latest supply prices of SKUs for local-to-local goods.（这是一个用于批量查询本地到本地商品的 SKU 最新供货价格的 API）

**适用店铺类型**: Local（本地店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `querySupplierPriceBaseList` | OBJECT[] | 是 | 查询供货价格基础列表 |
| `querySupplierPriceBaseList[].goodsId` | LONG | 是 | 商品 ID |
| `querySupplierPriceBaseList[].skuIdList` | LONG[] | 是 | SKU ID 列表 |
| `language` | STRING | 否 | 语言 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 是否成功 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 结果 |
| `result.openapiGoodsSupplierPriceDTOList` | OBJECT[] | 商品供货价格列表 |
| `result.openapiGoodsSupplierPriceDTOList[].goodsId` | LONG | 商品 ID |
| `result.openapiGoodsSupplierPriceDTOList[].openapiSkuSupplierPriceDTOList` | OBJECT[] | SKU 供货价格列表 |
| `result.openapiGoodsSupplierPriceDTOList[].openapiSkuSupplierPriceDTOList[].skuId` | LONG | SKU ID |
| `result.openapiGoodsSupplierPriceDTOList[].openapiSkuSupplierPriceDTOList[].supplierPrice` | OBJECT | 供货价格 |
| `result.openapiGoodsSupplierPriceDTOList[].openapiSkuSupplierPriceDTOList[].supplierPrice.amount` | STRING | 金额 |
| `result.openapiGoodsSupplierPriceDTOList[].openapiSkuSupplierPriceDTOList[].supplierPrice.currency` | STRING | 货币 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 150010105 | Mall information not found | 未找到店铺信息 |
| 150010003 | Invalid Request Parameters | 无效的请求参数 |
| 150010002 | System error, please try again later | 系统错误，请稍后重试 |

**权限包**: 
- `Local Product Management` (private, public)

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

- `bg.local.goods.priceorder.change.sku.price` - 更改 SKU 价格  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找

#### bg.local.goods.priceorder.query - 查询价格订单

**最后更新时间**: 2025-10-27 22:22:25  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=dcfb2f00fa4c497ea6ce15fd5b0ae84a](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=dcfb2f00fa4c497ea6ce15fd5b0ae84a)

**接口描述**: Support merchants within the white list to query the price offer list.（支持白名单内的商家查询价格报价列表）

**适用店铺类型**: Local（本地店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `page` | INTEGER | 否 | 页码 |
| `size` | INTEGER | 否 | 每页大小，小于 100 |
| `priceOrderType` | INTEGER | 否 | 定价类型，默认为定价评估报价，1：定价评估报价 2：定价机会或修改报价 |
| `priceOrderSubType` | INTEGER | 否 | 价格订单子类型，2002：基础价格增加邀请；2003：销售提升 |
| `goodsName` | STRING | 否 | 搜索参数：商品名称 |
| `goodsId` | STRING | 否 | 搜索参数：商品 ID |
| `priceOrderSnList` | STRING[] | 否 | 搜索参数：价格订单编号列表 |
| `orderBy` | STRING | 否 | 排序字段：goods_create_time, order_create_time。默认值为 order_create_time |
| `orderByType` | INTEGER | 否 | 排序类型：0-DESC, 1-ASC。默认值为 0-DESC |
| `goodsCreateTimeFrom` | LONG | 否 | 搜索参数：商品创建开始时间 |
| `goodsCreateTimeTo` | LONG | 否 | 搜索参数：商品创建结束时间 |
| `priceOrderCreateTimeFrom` | LONG | 否 | 搜索参数：价格订单创建开始时间 |
| `priceOrderCreateTimeTo` | LONG | 否 | 搜索参数：价格订单创建结束时间 |
| `goodsIdList` | STRING[] | 否 | 商品 ID 列表 |
| `status` | INTEGER | 否 | 价格订单状态 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 是否成功 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 返回具体信息 |
| `result.pageNum` | INTEGER | 页码 |
| `result.total` | INTEGER | 总数 |
| `result.priceAuditList` | OBJECT[] | 价格审核列表 |
| `result.priceAuditList[].priceOrderId` | LONG | 价格订单 ID |
| `result.priceAuditList[].goodsId` | LONG | 商品 ID |
| `result.priceAuditList[].skuIdList` | LONG[] | SKU ID 列表 |
| `result.priceAuditList[].specName` | STRING[] | 规格名称列表 |
| `result.priceAuditList[].pricingType` | INTEGER | 定价类型 |
| `result.priceAuditList[].status` | INTEGER | 状态 |
| `result.priceAuditList[].priceCommitId` | LONG | 价格提交 ID |
| `result.priceAuditList[].priceCommitVersion` | INTEGER | 价格提交版本 |
| `result.priceAuditList[].sourceSupplierPrice` | OBJECT | 源供货价格 |
| `result.priceAuditList[].targetSupplierPrice` | OBJECT | 目标供货价格 |
| `result.priceAuditList[].suggestSupplierPrice` | OBJECT | 建议供货价格 |
| `result.priceAuditList[].supplierPrice` | OBJECT | 供货价格 |
| `result.priceAuditList[].reason` | STRING | 原因 |
| `result.priceAuditList[].rejectTypeDesc` | STRING | 拒绝类型描述 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 150010002 | System error, please try again later | 系统错误，请稍后重试 |
| 150010003 | Invalid Request Parameters | 无效的请求参数 |
| 150010005 | Try again later | 请稍后重试 |
| 150010105 | Mall information not found | 未找到店铺信息 |

**权限包**: 
- `Local Product Management` (private, public)
- `Local Price Management` (private, public)

**限流规则**: AppKey: 30次 / 1秒

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。
- `bg.local.goods.priceorder.accept` - 接受价格订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.priceorder.negotiate` - 价格订单协商  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.order.amount.query` - 查询订单金额  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## 订单 (Order)

Order 模块提供了订单管理相关的 API 接口，包括订单查询、详情获取、金额查询等功能。

### 接口列表

#### V2 版本接口

##### bg.order.list.v2.get - 获取订单列表（V2）

**最后更新时间**: 2025-10-20 21:42:27  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=554fd46b45ee49269cbdd6d4008a5dc1](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=554fd46b45ee49269cbdd6d4008a5dc1)

**接口描述**: The bg.order.list.v2.get interface is designed for support batch return of corresponding order lists based on filtering criteria.（bg.order.list.v2.get 接口设计用于根据筛选条件批量返回相应的订单列表）

**适用店铺类型**: Local（本地店铺）、Cross Border（跨境店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `pageNumber` | INTEGER | 否 | 分页页码，默认为 1 |
| `pageSize` | INTEGER | 否 | 分页大小，默认为 10，最大为 100 |
| `parentOrderStatus` | INTEGER | 否 | 父订单状态，默认为查询全部。枚举值：0 - 全部，1 - PENDING（待处理），2 - UN_SHIPPING（待发货），3 - CANCELED（订单已取消），4 - SHIPPED（订单已发货），5 - RECEIPTED（订单已收货），41 - 部分发货（仅本地店铺），51 - 部分收货（仅本地店铺） |
| `parentOrderSnList` | STRING[] | 否 | 父订单号列表，每次请求最多 20 个 |
| `createAfter` | INTEGER | 否 | 查询父订单创建的开始时间，单位为秒（时间戳）。定义查询父订单时创建时间的起始范围。必须与 createBefore 配合使用 |
| `createBefore` | INTEGER | 否 | 查询父订单创建的结束时间，单位为秒（时间戳）。定义查询父订单时创建时间的结束范围（闭区间）。必须与 createAfter 配合使用 |
| `expectShipLatestTimeStart` | INTEGER | 否 | 查询预期最晚发货的开始时间，单位为秒 |
| `expectShipLatestTimeEnd` | INTEGER | 否 | 查询预期最晚发货的结束时间，单位为秒 |
| `updateAtStart` | INTEGER | 否 | 查询订单更新的开始时间，单位为秒（时间戳）。定义查询父订单时状态变更时间的起始范围。必须与 updateAtEnd 配合使用 |
| `updateAtEnd` | INTEGER | 否 | 查询订单更新的结束时间，单位为秒（时间戳）。定义查询父订单时状态变更时间的结束范围（闭区间）。必须与 updateAtStart 配合使用 |
| `regionId` | LONG | 否 | 区域 ID，例如：USA - 211 |
| `fulfillmentTypeList` | STRING[] | 否 | 订单履约类型。枚举值：fulfillBySeller（卖家履约），fulfillByCooperativeWarehouse（合作仓库履约） |
| `parentOrderLabel` | STRING[] | 否 | PO 订单状态标签列表：soon_to_be_overdue（即将逾期）、past_due（已逾期）、pending_buyer_cancellation（待买家取消）、pending_buyer_address_change（待买家地址变更）、pending_risk_control_alert（待风控提醒）、signature_required_on_delivery（需要签收） |
| `sortby` | STRING | 否 | 排序字段，按倒序输出。默认使用订单创建时间。对应的枚举值为：updateTime（更新时间）、createTime（创建时间） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 请求成功状态 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 响应结果对象 |
| `result.totalItemNum` | INTEGER | 总记录数 |
| `result.pageItems` | OBJECT[] | 分页数据列表 |
| `result.pageItems[].parentOrderMap` | OBJECT | 父订单信息 |
| `result.pageItems[].parentOrderMap.parentOrderSn` | STRING | 父订单号 |
| `result.pageItems[].parentOrderMap.parentOrderStatus` | INTEGER | **父订单状态**（详见下方订单状态说明） |
| `result.pageItems[].parentOrderMap.parentOrderTime` | INTEGER | 父订单创建时间（时间戳，单位：秒） |
| `result.pageItems[].parentOrderMap.updateTime` | INTEGER | **更新时间**（时间戳，单位：秒，可用于判断状态变更时间） |
| `result.pageItems[].parentOrderMap.expectShipLatestTime` | INTEGER | 预期最晚发货时间（时间戳，单位：秒） |
| `result.pageItems[].orderList` | OBJECT[] | 子订单列表 |
| `result.pageItems[].orderList[].orderSn` | STRING | 订单号 |
| `result.pageItems[].orderList[].goodsId` | LONG | 商品 ID |
| `result.pageItems[].orderList[].goodsName` | STRING | 商品名称 |
| `result.pageItems[].orderList[].skuId` | LONG | SKU ID |
| `result.pageItems[].orderList[].orderStatus` | INTEGER | **订单状态**（详见下方订单状态说明） |
| `result.pageItems[].orderList[].quantity` | INTEGER | 数量 |
| `result.pageItems[].orderList[].fulfillmentType` | STRING | 履约类型 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 140020001 | This interface does not support cross-border sellers. Please check whether the store bound to the token is a SEMI or LOCAL store! | 此接口不支持跨境卖家。请检查绑定到 token 的店铺是否为 SEMI 或 LOCAL 店铺 |

**权限包**: 
- `Semi Order Management` (public)
- `Local Order Management` (private, public)
- `Semi Seller in House System Management` (private)

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

##### bg.order.detail.v2.get - 获取订单详情（V2）

**最后更新时间**: 2025-10-20 21:42:27  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=9bf33a25319e4d7bbaf5ece4b823b9c3](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=9bf33a25319e4d7bbaf5ece4b823b9c3)

**接口描述**: The bg.order.detail.v2.get interface is designed for merchants to retrieve detailed information about a specific order within their respective stores. This functionality provides merchants with access to comprehensive order details, enabling them to process, fulfill, and manage individual orders with precision.（bg.order.detail.v2.get 接口设计用于商家检索其各自店铺中特定订单的详细信息。此功能为商家提供全面的订单详情访问权限，使他们能够精确地处理、履约和管理单个订单）

**适用店铺类型**: Local（本地店铺）、Cross Border（跨境店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `parentOrderSn` | STRING | 是 | 父订单号 |
| `fulfillmentTypeList` | STRING[] | 否 | 订单履约类型。枚举值：fulfillBySeller（卖家履约），fulfillByCooperativeWarehouse（合作仓库履约） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 请求成功状态 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 响应结果对象 |
| `result.parentOrderMap` | OBJECT | 父订单信息 |
| `result.parentOrderMap.parentOrderSn` | STRING | 父订单号 |
| `result.parentOrderMap.parentOrderStatus` | INTEGER | **父订单状态**（详见下方订单状态说明） |
| `result.parentOrderMap.parentOrderTime` | INTEGER | 父订单创建时间（时间戳，单位：秒） |
| `result.parentOrderMap.expectShipLatestTime` | INTEGER | 预期最晚发货时间（时间戳，单位：秒） |
| `result.parentOrderMap.latestDeliveryTime` | INTEGER | **最晚送达时间**（时间戳，单位：秒） |
| `result.parentOrderMap.parentShippingTime` | INTEGER | **父订单发货时间**（时间戳，单位：秒） |
| `result.parentOrderMap.parentOrderPendingFinishTime` | INTEGER | 父订单待完成时间（时间戳，单位：秒） |
| `result.parentOrderMap.parentOrderLabel` | OBJECT[] | 父订单标签列表 |
| `result.parentOrderMap.parentOrderLabel[].name` | STRING | 标签名称 |
| `result.parentOrderMap.parentOrderLabel[].value` | INTEGER | 标签值 |
| `result.orderList` | OBJECT[] | 子订单列表 |
| `result.orderList[].orderSn` | STRING | 订单号 |
| `result.orderList[].goodsId` | LONG | 商品 ID |
| `result.orderList[].goodsName` | STRING | 商品名称 |
| `result.orderList[].skuId` | LONG | SKU ID |
| `result.orderList[].orderStatus` | INTEGER | **订单状态**（详见下方订单状态说明） |
| `result.orderList[].orderCreateTime` | INTEGER | 订单创建时间（时间戳，单位：秒） |
| `result.orderList[].orderShippingTime` | INTEGER | **订单发货时间**（时间戳，单位：秒） |
| `result.orderList[].quantity` | INTEGER | 数量 |
| `result.orderList[].fulfillmentType` | STRING | 履约类型 |
| `result.orderList[].packageSnInfo` | OBJECT[] | 包裹单号信息 |
| `result.orderList[].packageSnInfo[].packageSn` | STRING | 包裹单号 |
| `result.orderList[].packageSnInfo[].packageDeliveryType` | INTEGER | 包裹配送类型 |
| `result.orderList[].packageSnInfo[].callSuccess` | BOOLEAN | 调用是否成功 |
| `result.orderList[].orderLabel` | OBJECT[] | 订单标签列表 |
| `result.orderList[].orderLabel[].name` | STRING | 标签名称 |
| `result.orderList[].orderLabel[].value` | INTEGER | 标签值 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 140020001 | This interface does not support cross-border sellers. Please check whether the store bound to the token is a SEMI or LOCAL store! | 此接口不支持跨境卖家。请检查绑定到 token 的店铺是否为 SEMI 或 LOCAL 店铺 |
| 140020002 | Order not found | 订单未找到 |
| 140020003 | The provider has at least one unsigned agreement. Please go to the home page to sign. | 提供商至少有一个未签署的协议。请前往首页签署 |

**权限包**: 
- `Semi Order Management` (public)
- `Local Order Management` (private, public)
- `Semi Seller in House System Management` (private)

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

##### bg.order.shippinginfo.v2.get - 获取订单物流信息（V2）

**最后更新时间**: 2025-07-01 20:20:56  
**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=ccc2f59661584f5e8e205d85ddb9a6c9](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=ccc2f59661584f5e8e205d85ddb9a6c9)

**接口描述**: The bg.order.shippinginfo.get.V2 interface is designed to retrieve shipping address information for a specific order. This functionality is crucial for merchants and logistics providers to ensure that orders are shipped to the correct location.（bg.order.shippinginfo.get.V2 接口设计用于检索特定订单的物流地址信息。此功能对商家和物流提供商至关重要，可确保订单发货到正确的位置）

**适用店铺类型**: Local（本地店铺）、Cross Border（跨境店铺）

**请求 URL**: 
- **US**: `POST https://openapi-b-us.temu.com/openapi/router`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `request` | OBJECT | 否 | 请求对象 |
| `parentOrderSn` | STRING | 否 | 父订单号 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | BOOLEAN | 请求成功状态 |
| `errorCode` | INTEGER | 错误码 |
| `errorMsg` | STRING | 错误消息 |
| `result` | OBJECT | 响应结果对象 |
| `result.receiptName` | STRING | 收货人姓名 |
| `result.receiptAdditionalName` | STRING | 收货人附加姓名 |
| `result.mobile` | STRING | 手机号 |
| `result.backupMobile` | STRING | 备用手机号 |
| `result.mail` | STRING | 邮箱 |
| `result.regionName1` | STRING | 区域名称1（国家/地区） |
| `result.regionName2` | STRING | 区域名称2（省/州） |
| `result.regionName3` | STRING | 区域名称3（市） |
| `result.regionName4` | STRING | 区域名称4（区/县） |
| `result.addressLine1` | STRING | 地址行1 |
| `result.addressLine2` | STRING | 地址行2 |
| `result.addressLine3` | STRING | 地址行3 |
| `result.addressLineAll` | STRING | 完整地址 |
| `result.postCode` | STRING | 邮政编码 |
| `result.taxCode` | STRING | 税号 |
| `result.warning` | OBJECT | 警告信息 |
| `result.warning.isRestriction` | BOOLEAN | 是否受限 |
| `result.warning.reason` | INTEGER | 原因 |

**错误码**:

| 错误码 | 错误消息 | 说明 |
|--------|---------|------|
| 180020001 | This country has not yet opened address query capabilities | 该国家尚未开放地址查询功能 |
| 180020003 | Invalid param | 无效参数 |
| 180020004 | Invalid business type | 无效的业务类型 |
| 180020008 | Please sign on DPA agreement first | 请先签署 DPA 协议 |
| 180020030 | Your store has been restricted from confirming shipment by tracking number. Please use the online buy shipping function instead. | 您的店铺已被限制通过跟踪号确认发货。请改用在线购买运输功能 |

**权限包**: 
- `Semi Order Management` (public)
- `Local Order Management` (private, public)
- `Semi Seller in House System Management` (private)

> **注意**: 此接口的详细参数说明、嵌套对象结构、请求/响应示例等完整文档，请访问上述直达链接查看。

### 订单状态和签收日期说明

#### 订单状态枚举值

**父订单状态（parentOrderStatus）**:

| 状态值 | 状态名称 | 说明 |
|--------|---------|------|
| 0 | 全部 | 查询全部状态 |
| 1 | PENDING | 待处理 |
| 2 | UN_SHIPPING | 待发货 |
| 3 | CANCELED | 订单已取消 |
| 4 | SHIPPED | 订单已发货 |
| 5 | RECEIPTED | **订单已收货** |
| 41 | 部分发货 | 仅本地店铺 |
| 51 | 部分收货 | 仅本地店铺 |

**子订单状态（orderStatus）**:

子订单状态与父订单状态使用相同的枚举值，表示单个子订单的状态。

#### 订单时间字段说明

以下时间字段均为 UNIX 时间戳（单位：秒）：

| 字段名 | 说明 | 来源接口 |
|--------|------|---------|
| `parentOrderTime` | 父订单创建时间 | `bg.order.detail.v2.get`, `bg.order.list.v2.get` |
| `orderCreateTime` | 子订单创建时间 | `bg.order.detail.v2.get` |
| `expectShipLatestTime` | 预期最晚发货时间 | `bg.order.detail.v2.get`, `bg.order.list.v2.get` |
| `parentShippingTime` | **父订单发货时间** | `bg.order.detail.v2.get` |
| `orderShippingTime` | **子订单发货时间** | `bg.order.detail.v2.get` |
| `latestDeliveryTime` | **最晚送达时间** | `bg.order.detail.v2.get` |
| `updateTime` | 订单更新时间 | `bg.order.list.v2.get` |

#### 订单签收日期获取说明

**重要提示**: 根据当前 API 文档，订单签收日期信息可能通过以下方式获取：

1. **通过订单状态判断**: 
   - 当 `parentOrderStatus` 或 `orderStatus` 为 `5`（RECEIPTED，订单已收货）时，表示订单已签收
   - 可通过 `updateTime` 字段判断状态变更时间，当状态变更为已收货时，该时间可视为签收时间

2. **通过物流跟踪 API**: 
   - 建议使用物流跟踪相关 API（如 Fulfillment 模块中的物流跟踪接口）获取详细的物流状态和签收时间
   - 物流跟踪 API 可能包含更详细的签收日期信息

3. **通过 Webhook 事件**: 
   - 订阅 `bg_order_status_change_event` 事件，当订单状态变更为已收货时，会收到相应的通知
   - 事件通知中可能包含签收时间信息

#### 相关 API 接口汇总

| API 接口 | 功能 | 订单状态 | 发货时间 | 签收日期 |
|---------|------|---------|---------|---------|
| `bg.order.list.v2.get` | 获取订单列表 | ✅ | ✅ | ⚠️ 通过状态判断 |
| `bg.order.detail.v2.get` | 获取订单详情 | ✅ | ✅ | ⚠️ 通过状态判断 |
| `bg.order.shippinginfo.v2.get` | 获取物流地址信息 | ❌ | ❌ | ❌ |
| Webhook 事件 | 订单状态变更通知 | ✅ | ✅ | ⚠️ 可能包含 |

**说明**:
- ✅ 表示该接口直接提供该信息
- ⚠️ 表示该接口间接提供或需要结合其他信息判断
- ❌ 表示该接口不提供该信息

#### 使用建议

1. **查询订单状态**: 使用 `bg.order.list.v2.get` 或 `bg.order.detail.v2.get` 接口，通过 `parentOrderStatus` 或 `orderStatus` 字段获取订单状态

2. **获取发货时间**: 使用 `bg.order.detail.v2.get` 接口，通过 `parentShippingTime` 或 `orderShippingTime` 字段获取发货时间

3. **判断签收日期**: 
   - 当订单状态为 `5`（RECEIPTED）时，订单已签收
   - 建议结合 `updateTime` 字段判断状态变更时间
   - 如需更精确的签收时间，建议使用物流跟踪 API 或 Webhook 事件

#### 其他订单接口
- `bg.order.combinedshipment.list.get` - 获取合并发货列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.customization.get` - 获取订单定制信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.decryptshippinginfo.get` - 解密订单物流信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找

#### Temu 订单取消接口
- `temu.order.cancel.outofstock.apply` - 申请缺货取消订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.appeal.apply` - 申请订单取消申诉  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.appeal.result.get` - 获取订单取消申诉结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.outofstock.result.get` - 获取缺货取消订单结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找

#### 订单取消相关接口
- `temu.order.cancel.outofstock.apply` - 申请缺货取消订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.appeal.apply` - 申请取消订单申诉  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.appeal.result.get` - 获取取消订单申诉结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `temu.order.cancel.outofstock.result.get` - 获取缺货取消订单结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找

#### 旧版本接口（已废弃，建议使用 V2 版本）
- `bg.order.amount.query` - 查询订单金额  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.detail.get` - 获取订单详情（旧版本）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.list.get` - 获取订单列表（旧版本）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.shippinginfo.get` - 获取订单物流信息（旧版本）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。建议优先使用 V2 版本的接口。

---

## 物流 (Logistics)

Logistics 模块提供了物流管理相关的 API 接口，包括物流公司查询、发货单创建、物流信息查询等功能。

### 接口列表

#### 基础信息查询
- `bg.logistics.warehouse.list.get` - 获取仓库列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.companies.get` - 获取物流公司  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shippingservices.get` - 获取物流服务  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `temu.logistics.shiplogisticstype.get` - 获取发货物流类型  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找

#### 发货单管理（根据 API 范围列表）
- `bg.logistics.shipment.confirm` - 确认发货  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.create` - 创建发货单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.document.get` - 获取发货单据  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.get` - 获取发货信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.result.get` - 获取发货结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.shippingtype.update` - 更新发货类型  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.sub.confirm` - 确认子发货  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.update` - 更新发货信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## 履约 (Fulfillment)

Fulfillment 模块提供了履约相关的 API 接口。

### 指南页面

- **Fulfillment by Buy-shipping on TEMU** - TEMU 代发货履约指南  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- **TEMU Logistics Tracking API Documentation** - TEMU 物流追踪 API 文档  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

### 接口列表

#### 履约信息同步
- `bg.order.fulfillment.info.sync` - 同步订单履约信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 发货相关接口（V2）
- `bg.logistics.shipment.v2.confirm` - 确认发货（V2）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.v2.get` - 获取发货信息（V2）  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 包裹相关接口
- `bg.order.unshipped.package.get` - 获取未发货包裹  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipped.package.confirm` - 确认已发货包裹  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 扫描表单相关接口
- `temu.logistics.candidate.scanform.list.get` - 获取候选扫描表单列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `temu.logistics.scanform.create` - 创建扫描表单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `temu.logistics.scanform.document.get` - 获取扫描表单文档  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `temu.logistics.scanform.get` - 获取扫描表单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 取件预约相关接口
- `temu.logistics.shipment.pickup.reservation.create` - 创建取件预约  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `temu.logistics.shipment.pickup.reservation.cancel` - 取消取件预约  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `temu.logistics.shipment.pickup.reservation.result.get` - 获取取件预约结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 物流追踪接口
- `temu.track.trackinginfo.get` - 获取物流追踪信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

#### 其他发货接口
- `bg.logistics.shipment.sub.confirm` - 确认子发货  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.shippingtype.update` - 更新发货类型  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.create` - 创建发货单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.result.get` - 获取发货结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.update` - 更新发货信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找
- `bg.logistics.shipment.document.get` - 获取发货单据  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Fulfillment 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## 退货退款 (Return and Refund)

Return and Refund 模块提供了售后处理相关的 API 接口，包括退货退款查询、处理等功能。

### 接口列表

- `bg.aftersales.aftersales.list.get` - 获取售后列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找
- `bg.aftersales.parentaftersales.list.get` - 获取父售后列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找
- `bg.aftersales.parentreturnorder.get` - 获取父退货订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## 促销 (Promotion)

Promotion 模块提供了促销活动管理相关的 API 接口。

### 促销活动 API 概览

- **Promotion activities API overview** - 促销活动 API 概览  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找

### 接口列表

- `bg.promotion.activity.query` - 查询促销活动  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找
- `bg.promotion.activity.candidate.goods.query` - 查询促销活动候选商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找
- `bg.promotion.activity.goods.query` - 查询促销活动商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找
- `bg.promotion.activity.goods.enroll` - 商品报名促销活动  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找
- `bg.promotion.activity.goods.operation.query` - 查询促销活动商品操作  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找
- `bg.promotion.activity.goods.update` - 更新促销活动商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Promotion 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## Webhook

Webhook 模块提供了事件通知相关的功能。

### Webhook 事件说明 (The event of webhook)

**直达链接**: [https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Webhook 模块下查找 "The event of webhook"

### Webhook 事件列表

以下是所有可订阅的 Webhook 事件：

- `bg_open_event_test` - 测试事件
- `bg_order_status_change_event` - 订单状态变更事件
- `bg_trade_logistics_address_changed` - 交易物流地址变更
- `bg_aftersales_status_change` - 售后状态变更
- `bg_cancel_order_status_change` - 取消订单状态变更

### 接口列表

- **The event of webhook** - Webhook 事件说明  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Webhook 模块下查找
- `bg.tmc.message.update` - 更新消息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Webhook 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## 广告 (Ads)

Ads 模块提供了广告管理相关的 API 接口。

### 广告介绍

- **Ads Introduction** - 广告介绍  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找

### 接口列表

- `temu.searchrec.ad.roas.pred` - 预测广告投资回报率  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.reports.mall.query` - 查询店铺广告报告  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.reports.goods.query` - 查询商品广告报告  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.create` - 创建广告  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.detail.query` - 查询广告详情  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.log.query` - 查询广告日志  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.goods.create.query` - 查询广告商品创建  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找
- `temu.searchrec.ad.modify` - 修改广告  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Ads 模块下查找

> **注意**: 以上接口的详细文档（请求参数、响应参数、示例等）请访问 Temu 合作伙伴平台 API 参考页面查看。

---

## API 范围列表

以下是所有可用的 API 接口列表：

### 售后相关
- `bg.aftersales.aftersales.list.get` - 获取售后列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找
- `bg.aftersales.parentaftersales.list.get` - 获取父售后列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找
- `bg.aftersales.parentreturnorder.get` - 获取父退货订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Return and Refund 模块下查找

### 运费相关
- `bg.freight.template.list.query` - 查询运费模板列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找

### 商品相关
- `bg.local.compliance.goods.list.query` - 查询合规商品列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.add` - 添加商品     
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=b68f47b094e7469eab7cf58c2b7cf0c6) - 直达链接
- `bg.local.goods.brand.trademark.get` - 获取品牌商标
- `bg.local.goods.category.recommend` - 获取推荐分类  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.cats.get` - 获取分类
- `bg.local.goods.compliance.edit` - 编辑商品合规信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.extra.template.get` - 获取合规额外模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.property.check` - 检查合规属性  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.compliance.rules.get` - 获取合规规则  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.gallery.signature.get` - 获取图库签名  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.list.query` - 查询商品列表    
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=860a51f023a042a2805211f658119536) - 直达链接
- `bg.local.goods.out.sn.check` - 检查外部商品编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.out.sn.set` - 设置外部商品编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.partial.update` - 部分更新商品  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.priceorder.accept` - 接受价格订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.priceorder.change.sku.price` - 更改 SKU 价格  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.priceorder.negotiate` - 价格订单协商  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.priceorder.query` - 查询价格订单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.property.get` - 获取商品属性  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.publish.status.get` - 获取发布状态  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sale.status.set` - 设置销售状态  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.size.element.get` - 获取尺寸元素  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sku.list.price.query` - 查询 SKU 价格列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Price 模块下查找
- `bg.local.goods.sku.list.query` - 查询 SKU 列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sku.out.sn.check` - 检查 SKU 外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.sku.out.sn.set` - 设置 SKU 外部编号  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.spec.id.get` - 获取规格 ID  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.stock.edit` - 编辑库存  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.template.get` - 获取商品模板  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Product 模块下查找
- `bg.local.goods.update` - 更新商品   
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=7dd781cddbd440c490c0312bc8d5aa0d) - 直达链接

### 物流相关
- `bg.logistics.companies.get` - 获取物流公司  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.confirm` - 确认发货  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.create` - 创建发货单  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.document.get` - 获取发货单据  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.get` - 获取发货信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.result.get` - 获取发货结果  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.shippingtype.update` - 更新发货类型  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.sub.confirm` - 确认子发货  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shipment.update` - 更新发货信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.shippingservices.get` - 获取物流服务  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找
- `bg.logistics.warehouse.list.get` - 获取仓库列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Logistics 模块下查找

### 授权相关
- `bg.open.accesstoken.info.get` - 获取访问令牌信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a&sub_menu_code=93de550b56c8417caccb88824be3e614) - 直达链接

### 订单相关
- `bg.order.amount.query` - 查询订单金额  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.combinedshipment.list.get` - 获取合并发货列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.detail.get` - 获取订单详情  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.list.get` - 获取订单列表  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找
- `bg.order.shippinginfo.get` - 获取订单物流信息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Order 模块下查找

### 消息相关
- `bg.tmc.message.update` - 更新消息  
  [查看文档](https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a) - 在左侧菜单的 Webhook 模块下查找

---

## Webhook 事件列表

以下是所有可订阅的 Webhook 事件：

- `bg_open_event_test` - 测试事件
- `bg_order_status_change_event` - 订单状态变更事件
- `bg_trade_logistics_address_changed` - 交易物流地址变更
- `bg_aftersales_status_change` - 售后状态变更
- `bg_cancel_order_status_change` - 取消订单状态变更

---

## 相关链接

### 平台链接

- **Partner Platform for US**: https://partner-us.temu.com
- **Partner Platform for EU**: https://partner-eu.temu.com
- **Partner Platform for GLOBAL**: https://partner.temu.com
- **TEMU 买家**: https://www.temu.com/
- **TEMU 卖家中心（中国大陆/香港）**: https://agentseller-us.temu.com/

### 文档链接

- **合作伙伴指南**: https://partner-us.temu.com/documentation?menu_code=52ef88bdef1d4527b15f6d303b173e48
- **开发者指南**: https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303
- **API 参考**: https://partner-us.temu.com/documentation?menu_code=fb16b05f7a904765aac4af3a24b87d4a

### 政策链接

- **Temu 合作伙伴平台条款**: https://partner-us.temu.com/documentation?menu_code=d8425dcd25b04658843e622e178a3b42
- **Temu 合作伙伴平台隐私政策**: https://partner-us.temu.com/documentation?menu_code=d8425dcd25b04658843e622e178a3b42&sub_menu_code=2b5a53673c5f4b2284cb30c77d40ae98
- **服务提供商数据安全政策**: https://partner-us.temu.com/documentation?menu_code=d8425dcd25b04658843e622e178a3b42&sub_menu_code=9cc3edb526494a059c477fd99953fa3e
- **合作伙伴平台 Cookie 政策**: https://partner-us.temu.com/protocol/temu_partner_platform_cookie_policy_20240731.pdf

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-03-14 | - | 授权和授权回调文档更新 |

---

*本文档由自动化工具从 Temu 合作伙伴平台提取并整理。如有疑问，请联系 Temu 技术支持。*
