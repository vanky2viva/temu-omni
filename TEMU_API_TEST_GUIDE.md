# Temu API 测试指南

## 🎯 当前状态

✅ **已成功验证：**
- API 连接正常
- 请求格式正确
- 签名算法正确
- App Key 和 App Secret 有效

❌ **需要配置：**
- Access Token（访问令牌）

---

## 📖 如何获取沙盒 Access Token

根据你提供的文档链接，请按以下步骤操作：

### 方法 1: 从文档获取沙盒令牌

1. 访问文档页面：
   - https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=2d81829fcbbc4058b95f695440e75236
   - https://partner-us.temu.com/documentation?menu_code=38e79b35d2cb463d85619c1c786dd303&sub_menu_code=9cf457c922fe4b33b93c23ab1d8b15d0

2. 在文档中查找以下内容：
   - "Sandbox Token" 或 "测试令牌"
   - "Test Credentials" 或 "测试凭据"
   - 示例请求中的 `access_token` 值

3. 复制 access_token 的值

### 方法 2: 通过授权流程获取

如果文档中没有提供沙盒令牌，需要通过正式的授权流程：

1. 登录 Temu Seller Center
2. 进入 "Apps and Services" → "Manage your apps"
3. 找到你的应用（App Key: `798478197604e93f6f2ce4c2e833041u`）
4. 完成授权流程，获取 authorization code
5. 使用 `bg.open.accesstoken.create` 接口换取 access_token

---

## 🧪 快速测试

### 使用环境变量

```bash
# 设置沙盒令牌
export TEMU_ACCESS_TOKEN='你从文档中获取的token'

# 运行测试
python3 api_test.py
```

### 或直接在脚本中测试

```bash
# 使用交互式测试脚本
python3 api_test_interactive.py
```

---

## 📝 可测试的 API 接口

一旦有了 access_token，可以测试以下接口：

| API 类型 | 功能 | 需要 Token |
|---------|------|-----------|
| `bg.local.goods.cats.get` | 查询商品分类 | ✅ |
| `bg.open.accesstoken.info.get` | 查询Token信息 | ✅ |
| `bg.shop.info.get` | 获取店铺信息 | ✅ |
| `bg.order.list.get` | 订单列表查询 | ✅ |
| `bg.goods.list.get` | 商品列表查询 | ✅ |

---

## 🔧 现有测试工具

### 1. `api_test.py` - 基础测试脚本
运行简单的API测试

```bash
python3 api_test.py
```

### 2. `api_test_detailed.py` - 详细测试脚本
测试多个API端点，提供详细输出

```bash
python3 api_test_detailed.py
```

### 3. `api_test_interactive.py` - 交互式测试（即将创建）
可以手动输入token进行测试

```bash
python3 api_test_interactive.py
```

---

## 💡 下一步

1. **查看文档**：打开上面的文档链接，找到沙盒令牌
2. **设置令牌**：使用环境变量或直接在代码中设置
3. **运行测试**：执行测试脚本验证API功能
4. **查看结果**：确认能否成功获取数据

---

## 🐛 常见问题

### Q: 出现 "there is no access_token in body" 错误
**A:** 需要设置 access_token，请参考上面的方法获取。

### Q: 出现签名错误
**A:** 检查 App Key 和 App Secret 是否正确。

### Q: 文档中没有找到沙盒令牌
**A:** 可能需要先创建应用并完成授权流程。

---

## 📞 需要帮助？

如果你在文档中找到了沙盒令牌，请告诉我，我会帮你立即测试！

示例：
```bash
export TEMU_ACCESS_TOKEN='文档中的token'
python3 api_test_detailed.py
```

