# Temu API 测试工具集

## 📋 当前状态

### ✅ 已验证
- ✅ API连接成功（https://openapi-b-us.temu.com/openapi/router）
- ✅ 请求格式正确
- ✅ 签名算法正确（MD5）
- ✅ App Key 和 App Secret 有效

### ❓ 待配置
- 📝 需要从文档获取 Access Token（沙盒令牌）

---

## 🎯 快速开始

### 步骤 1: 获取 Access Token

访问文档页面，获取沙盒令牌：
- [文档链接 1](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=2d81829fcbbc4058b95f695440e75236)
- [文档链接 2](https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=9cf457c922fe4b33b93c23ab1d8b15d0)

在文档中查找：
- "Sandbox Token" / "测试令牌"
- "Test Access Token" / "测试访问令牌"
- 示例代码中的 `access_token` 值

### 步骤 2: 设置 Token

**方法 1: 环境变量（推荐）**
```bash
export TEMU_ACCESS_TOKEN='你从文档中获取的token'
```

**方法 2: 交互式输入**
```bash
python3 api_test_interactive.py
# 然后在提示时输入token
```

### 步骤 3: 运行测试

```bash
# 详细测试（推荐）
python3 api_test_detailed.py

# 或使用交互式测试
python3 api_test_interactive.py

# 或基础测试
python3 api_test.py
```

---

## 🛠️ 测试工具说明

### 1. `api_test.py` - 基础测试
最简单的测试脚本，测试商品分类接口。

**使用方法：**
```bash
export TEMU_ACCESS_TOKEN='你的token'
python3 api_test.py
```

### 2. `api_test_detailed.py` - 详细测试
测试多个API端点，提供详细的请求和响应信息。

**测试的API：**
- 查询商品分类
- 查询Token信息
- 获取店铺信息
- 订单列表查询

**使用方法：**
```bash
export TEMU_ACCESS_TOKEN='你的token'
python3 api_test_detailed.py
```

### 3. `api_test_interactive.py` - 交互式测试 ⭐
**推荐使用！** 可以手动输入token，实时测试。

**使用方法：**
```bash
python3 api_test_interactive.py
# 按提示输入access_token
```

**特点：**
- 自动检测环境变量
- 支持手动输入token
- 测试多个常用接口
- 清晰的成功/失败统计

---

## 📊 测试结果示例

### 成功响应
```json
{
    "success": true,
    "requestId": "us-xxx-xxx-xxx",
    "result": {
        // 返回的数据
    }
}
```

### 失败响应
```json
{
    "success": false,
    "requestId": "us-xxx-xxx-xxx",
    "errorCode": 3000030,
    "errorMsg": "there is no access_token in body."
}
```

---

## 🔍 常见错误码

| 错误码 | 说明 | 解决方法 |
|--------|------|---------|
| 3000030 | 缺少 access_token | 设置 TEMU_ACCESS_TOKEN 环境变量 |
| 1000001 | 签名错误 | 检查 App Key 和 App Secret |
| 1000002 | 参数错误 | 检查请求参数格式 |
| 3000010 | Token过期 | 重新获取 access_token |

---

## 📁 相关文件

```
/Users/vanky/code/temu-Omni/
├── api_test.py                    # 基础测试脚本
├── api_test_detailed.py           # 详细测试脚本
├── api_test_interactive.py        # 交互式测试脚本 ⭐
├── README_API_TESTING.md          # 本文档
├── TEMU_API_TEST_GUIDE.md         # 详细测试指南
└── Temu_OpenAPI_开发者文档.md     # API文档
```

---

## 🎓 下一步

完成API测试后，你可以：

1. **集成到主应用**
   - 更新 `backend/app/temu/client.py` 使用正确的签名算法
   - 添加更多业务接口

2. **配置生产环境**
   - 设置真实的 App Key 和 Secret
   - 完成OAuth授权流程
   - 获取生产环境的 access_token

3. **开发业务功能**
   - 同步商品数据
   - 处理订单信息
   - 实现物流追踪

---

## 💡 提示

### 如果你已经有了沙盒token：

```bash
# 一键测试
export TEMU_ACCESS_TOKEN='你的沙盒token'
python3 api_test_interactive.py
```

### 如果还没有token：

1. 打开上面的文档链接
2. 查找沙盒测试凭据
3. 复制 access_token
4. 运行交互式测试脚本

---

## 🐛 遇到问题？

如果遇到任何问题，请提供：
1. 错误码和错误信息
2. 使用的测试脚本
3. 是否设置了 access_token

我会帮助你解决！

---

**最后更新**: 2025-10-30
**状态**: ✅ API连接已验证，等待access_token进行完整测试

