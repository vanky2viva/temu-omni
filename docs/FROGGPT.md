# FrogGPT AI 模块使用指南

## 概述

FrogGPT 是一个集成到 Temu Omni 系统中的 AI 运营助手模块，使用 OpenRouter API 提供 AI 能力，帮助运营人员进行数据分析、决策建议等。

## 功能特性

- 🤖 **ChatGPT 风格对话**：支持自然语言对话，与 AI 助手交互
- 📊 **系统数据集成**：自动获取系统内的订单、商品、销售等数据，为 AI 提供上下文
- 📎 **文件上传支持**：支持上传图片、文档等文件进行分析
- 🔧 **灵活配置**：可选择不同的 AI 模型、调整温度参数等
- 💡 **智能决策**：结合系统数据，提供运营决策建议

## 配置

### 1. 获取 OpenRouter API 密钥

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册并登录账户
3. 在控制面板中创建 API 密钥
4. 将密钥添加到环境变量中

### 2. 环境变量配置

在 `backend/.env` 文件中添加以下配置：

```env
# OpenRouter API配置
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini  # 可选，默认模型
OPENROUTER_TIMEOUT=60.0  # 可选，请求超时时间（秒）
OPENROUTER_HTTP_REFERER=http://localhost:5173  # 可选，用于免费使用
OPENROUTER_X_TITLE=Temu Omni  # 可选，X-Title头
```

### 3. 免费使用模式

如果没有 API 密钥，可以设置 `OPENROUTER_HTTP_REFERER` 来使用免费模式（功能可能受限）。

## 使用方法

### 1. 访问 FrogGPT

在系统侧边栏中点击 "FrogGPT" 菜单项，进入 AI 助手页面。

### 2. 选择 AI 模型

在页面顶部的设置栏中，选择要使用的 AI 模型。系统会自动加载可用的模型列表。

### 3. 配置参数

- **温度（Temperature）**：控制 AI 回答的随机性，范围 0.1-1.0
  - 较低值（0.1-0.3）：更确定、一致的回答
  - 较高值（0.7-1.0）：更创新、多样的回答

- **包含系统数据**：开启后，AI 会自动获取系统内的数据摘要作为上下文

- **数据天数**：选择要包含多少天的系统数据（3/7/15/30天）

### 4. 开始对话

1. 在输入框中输入问题或指令
2. 可以上传文件（图片、文档等）进行分析
3. 按 Enter 发送消息，Shift+Enter 换行
4. AI 会结合系统数据给出回答和建议

### 5. 示例问题

- "分析最近7天的销售趋势"
- "哪些商品销量最好？"
- "帮我分析一下利润率情况"
- "给出提升销量的建议"
- "对比不同负责人的业绩"

## API 接口

### 发送聊天消息

```http
POST /api/frog-gpt/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "分析最近7天的销售数据"}
  ],
  "model": "openai/gpt-4o-mini",
  "temperature": 0.7,
  "include_system_data": true,
  "data_summary_days": 7
}
```

### 发送带文件的消息

```http
POST /api/frog-gpt/chat/with-files
Content-Type: multipart/form-data

messages: [{"role": "user", "content": "分析这个图片"}]
files: [文件对象]
model: openai/gpt-4o-mini
```

### 获取可用模型列表

```http
GET /api/frog-gpt/models
```

### 获取系统数据摘要

```http
GET /api/frog-gpt/data-summary?days=7
```

## 技术架构

### 后端

- **服务层**：`backend/app/services/frog_gpt_service.py`
  - 封装 OpenRouter API 调用
  - 处理系统数据上下文构建

- **API 层**：`backend/app/api/frog_gpt.py`
  - 提供 RESTful API 接口
  - 处理文件上传
  - 集成系统数据

### 前端

- **页面组件**：`frontend/src/pages/FrogGPT.tsx`
  - ChatGPT 风格的对话界面
  - 文件上传功能
  - 模型选择和参数配置

- **API 服务**：`frontend/src/services/api.ts`
  - 封装 API 调用
  - 处理请求和响应

## 注意事项

1. **API 密钥安全**：请妥善保管 API 密钥，不要提交到代码仓库
2. **使用限制**：注意 OpenRouter 的使用限制和费用
3. **数据隐私**：系统数据会作为上下文发送给 AI，请注意数据隐私
4. **网络要求**：需要能够访问 OpenRouter API（可能需要代理）

## 故障排除

### 问题：API 密钥未配置错误

**解决方案**：
- 检查环境变量 `OPENROUTER_API_KEY` 是否设置
- 或设置 `OPENROUTER_HTTP_REFERER` 使用免费模式

### 问题：无法获取模型列表

**解决方案**：
- 检查网络连接
- 确认 API 密钥有效
- 查看后端日志获取详细错误信息

### 问题：AI 回答不准确

**解决方案**：
- 调整温度参数
- 尝试不同的模型
- 确保系统数据摘要功能已开启

## 更新日志

- **v1.0.0** (2024-11-27)
  - 初始版本发布
  - 支持基础对话功能
  - 支持文件上传
  - 集成系统数据上下文





