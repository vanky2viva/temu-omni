# ChatKit 集成文档

## 概述

本项目已集成基于 OpenAI SDK 的高级 AI 中枢系统，支持：
- ✅ 使用 OpenAI SDK 进行对话
- ✅ Function Calling（工具函数调用）
- ✅ Dashboard 指令协议（AI 控制前端图表）
- ✅ 多店铺权限管理
- ✅ 流式响应

## 架构设计

### 后端架构

```
backend/app/
├── api/
│   └── chatkit.py          # ChatKit API 端点
└── services/
    └── chatkit_service.py  # ChatKit 核心服务（使用 OpenAI SDK）
```

### 前端架构

```
frontend/src/
├── components/
│   └── FrogGPTChat.tsx     # ChatKit 聊天组件
├── stores/
│   └── dashboardStore.ts   # Dashboard 状态管理（Zustand）
├── services/
│   └── chatkitApi.ts       # ChatKit API 客户端
└── types/
    └── chatkit.ts          # TypeScript 类型定义
```

## 功能特性

### 1. 会话管理

**创建会话**
```typescript
POST /api/chatkit/session
{
  "shop_id": 1,           // 可选：单个店铺ID
  "shop_ids": [1, 2],     // 可选：多个店铺ID
  "tenant_id": "default"  // 可选：租户ID
}
```

**响应**
```json
{
  "session_id": "uuid",
  "metadata": {
    "userId": "1",
    "shopId": 1,
    "allowedShops": [1, 2],
    "provider": "openai",
    "model": "gpt-4o"
  },
  "api_key_configured": true
}
```

### 2. AI 工具函数（Function Calling）

系统支持以下工具函数：

#### `get_shop_dashboard`
获取店铺仪表盘数据
```json
{
  "shop_id": 1,
  "days": 7
}
```

#### `get_order_trend`
获取订单趋势数据
```json
{
  "shop_id": 1,
  "days": 7
}
```

#### `list_top_profit_skus`
列出高利润 SKU
```json
{
  "shop_id": 1,
  "limit": 10,
  "days": 30
}
```

#### `list_top_loss_skus`
列出亏损 SKU
```json
{
  "shop_id": 1,
  "limit": 10,
  "days": 30
}
```

#### `emit_dashboard_command`
发送 Dashboard 指令
```json
{
  "command_type": "SET_METRIC_CHART",
  "payload": {
    "metric": "gmv",
    "days": 14,
    "chart_type": "line"
  }
}
```

### 3. Dashboard 指令协议

支持的指令类型：

- `SET_DATE_RANGE`: 设置时间范围
- `SET_METRIC_CHART`: 设置图表指标
- `FOCUS_SKU`: 聚焦某个 SKU
- `COMPARE_SHOPS`: 对比多个店铺
- `REFRESH_DATA`: 刷新数据

## 使用示例

### 前端使用

```tsx
import { FrogGPTChat } from '@/components/FrogGPTChat'
import { useDashboardStore } from '@/stores/dashboardStore'

function MyPage() {
  const dispatchCommand = useDashboardStore((state) => state.dispatchCommand)
  
  return (
    <FrogGPTChat
      shopId={1}
      onCommand={(command) => {
        console.log('收到 Dashboard 指令:', command)
        dispatchCommand(command)
      }}
    />
  )
}
```

### 对话示例

**用户**: "展示最近 14 天 GMV 趋势"

**AI 响应流程**:
1. AI 识别需要调用 `emit_dashboard_command` 工具
2. 执行工具，发送 `SET_METRIC_CHART` 指令
3. 前端接收指令，更新 Dashboard 状态
4. AI 继续生成回复："已为您展示最近 14 天的 GMV 趋势图表..."

**用户**: "找出最近 30 天最赚钱的 5 个 SKU"

**AI 响应流程**:
1. AI 调用 `list_top_profit_skus` 工具
2. 获取数据后，AI 生成表格和图表
3. 返回格式化的分析结果

## 配置

### 后端配置

1. 安装依赖：
```bash
pip install openai==1.12.0
```

2. 配置 OpenAI API Key（通过前端设置页面或数据库）：
```python
# 数据库 SystemConfig 表
key: "openai_api_key"
value: "sk-..."
```

### 前端配置

无需额外配置，直接使用组件即可。

## 开发指南

### 添加新的工具函数

1. 在 `chatkit_service.py` 的 `get_available_tools()` 中添加工具定义
2. 在 `execute_tool()` 中添加执行逻辑
3. 实现对应的私有方法（如 `_my_new_tool()`）

### 添加新的 Dashboard 指令

1. 在 `types/chatkit.ts` 的 `DashboardCommandType` 中添加新类型
2. 在 `dashboardStore.ts` 的 `dispatchCommand()` 中添加处理逻辑
3. 在工具函数 `emit_dashboard_command` 中支持新指令

## 注意事项

1. **API Key 安全**: API Key 存储在数据库中，不会暴露给前端
2. **权限控制**: 工具函数会自动使用用户有权限的店铺ID列表
3. **流式响应**: 所有对话都使用流式响应，提供更好的用户体验
4. **错误处理**: 工具调用失败时会返回错误信息，不会中断对话

## 故障排查

### OpenAI SDK 未安装
```bash
docker compose exec backend pip install openai==1.12.0
```

### API Key 未配置
在前端设置页面配置 OpenAI API Key

### 工具调用失败
检查后端日志，查看具体错误信息

## 下一步

- [ ] 实现会话持久化存储
- [ ] 添加更多工具函数
- [ ] 支持多轮工具调用优化
- [ ] 添加工具调用缓存
- [ ] 实现模型自动切换（gpt-4o / gpt-4o-mini）


