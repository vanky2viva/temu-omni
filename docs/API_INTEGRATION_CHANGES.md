# API 集成更改总结

## 概述

本次更新将 Temu API 集成到应用中，主要变更包括：
1. 删除系统设置边栏
2. 内置 App Key 和 App Secret
3. 在店铺管理页面添加区域和 Access Token 字段
4. 根据区域自动设置 API 基础 URL
5. 更新订单状态映射以匹配 API 文档

## 主要更改

### 1. 删除系统设置边栏

- ✅ 从 `frontend/src/layouts/MainLayout.tsx` 中删除系统设置菜单项
- ✅ 从 `frontend/src/App.tsx` 中删除系统设置路由
- ✅ 删除 `frontend/src/pages/SystemSettings.tsx` 文件

### 2. 内置 App Key 和 App Secret

**文件**: `backend/app/core/config.py`

- App Key: `798478197604e93f6f2ce4c2e833041u`
- App Secret: `776a96163c56c53e237f5456d4e14765301aa8aa`

这些凭证现在直接内置在配置文件中，不再需要从数据库或环境变量读取。

**更新的文件**:
- `backend/app/core/config.py` - 设置默认值
- `backend/app/services/temu_service.py` - 使用内置配置
- `backend/app/api/system.py` - 更新 `get_app_credentials` 函数

### 3. 店铺管理页面更新

**文件**: `frontend/src/pages/ShopList.tsx`

- ✅ 在创建店铺表单中添加了 **Access Token** 字段（必填）
- ✅ 保留了区域选择字段
- ✅ 更新了提示信息，说明 App Key 和 App Secret 已内置

**文件**: `backend/app/api/shops.py`

- ✅ 根据选择的区域自动设置 `api_base_url`：
  - US: `https://openapi-b-us.temu.com/openapi/router`
  - EU: `https://openapi-b-eu.temu.com/openapi/router`
  - GLOBAL: `https://openapi-b-global.temu.com/openapi/router`
- ✅ 更新授权接口，确保设置 `api_base_url`

### 4. 订单状态映射更新

**文件**: `backend/app/services/sync_service.py`

根据 Temu API 文档更新了订单状态映射：

| Temu 状态码 | 状态名称 | 系统状态 |
|------------|---------|---------|
| 0 | 全部 | PENDING |
| 1 | PENDING（待处理） | PENDING |
| 2 | UN_SHIPPING（待发货） | PROCESSING |
| 3 | CANCELED（订单已取消） | CANCELLED |
| 4 | SHIPPED（订单已发货） | SHIPPED |
| 5 | RECEIPTED（订单已收货） | DELIVERED |
| 41 | 部分发货 | SHIPPED |
| 51 | 部分收货 | DELIVERED |

### 5. 时间字段提取更新

**文件**: `backend/app/services/sync_service.py`

根据 API 文档更新了时间字段的提取逻辑：
- `parentOrderTime` → `order_time`
- `parentShippingTime` / `orderShippingTime` → `shipping_time`
- `latestDeliveryTime` → `delivery_time`
- `paymentTime` → `payment_time`

### 6. 数据清理脚本

**文件**: `backend/scripts/clear_all_data.py`

创建了数据清理脚本，可以：
- 清理所有订单、商品、活动等数据（保留店铺）
- 清理所有店铺数据（级联删除关联数据）

**使用方法**:
```bash
# 清理所有数据（保留店铺）
python backend/scripts/clear_all_data.py

# 清理所有店铺数据（包括关联数据）
python backend/scripts/clear_all_data.py --shops-only
```

## 使用说明

### 添加新店铺

1. 进入"店铺管理"页面
2. 点击"添加店铺"按钮
3. 填写以下信息：
   - **店铺名称**: 必填
   - **地区**: 必填（US / EU / GLOBAL）
   - **Access Token**: 必填（从 Temu 卖家中心获取）
   - **经营主体**: 可选
   - **负责人**: 可选
   - **备注**: 可选

4. 系统会自动根据选择的区域设置 API 基础 URL

### 获取 Access Token

1. 访问 [Temu 卖家中心](https://seller.temu.com/open-platform/client-manage)
2. 登录您的卖家账号
3. 在"授权管理"页面找到您的应用
4. 复制 Access Token
5. 在添加店铺时粘贴到 Access Token 字段

### 同步数据

1. 在店铺列表中点击"同步"按钮
2. 系统将通过 Temu API 获取订单、商品等数据
3. 数据将自动存入数据库

## 注意事项

1. **App Key 和 App Secret** 已内置，无需配置
2. **Access Token** 是每个店铺独立的，需要在添加店铺时填写
3. **区域选择** 会影响 API 请求的端点，请确保选择正确的区域
4. 首次同步可能需要 2-5 分钟，请耐心等待

## 后续工作

- [ ] 验证 API 数据同步功能
- [ ] 测试不同区域的 API 调用
- [ ] 优化数据同步性能
- [ ] 添加错误处理和重试机制


