# FrogGPT 2.0 重构说明

## 概述

FrogGPT 2.0 是使用 Ant Design X 组件库重构的专业电商运营 AI 控制台，实现了可视化的数据查看、AI 自动分析 & 决策、结构化 JSON 驱动决策卡片、ChatGPT 风格对话窗口等功能。

## 组件结构

```
FrogGPT/
├── components/
│   ├── AiChatPanelV2.tsx      # AI 聊天面板（使用 Ant Design X Bubble）
│   ├── DecisionPanel.tsx       # AI 结构化决策区
│   └── TrendsCharts.tsx       # 运营图表区
├── FrogGPTV2.tsx              # 主页面（左右分栏布局）
├── types.ts                   # 类型定义
├── MetricOverview.tsx         # 指标速览组件
└── QuickPrompts.tsx           # 快捷问题组件
```

## 主要特性

### 1. 左右分栏布局（左 40% / 右 60%）

**左侧（数据 & 决策视图）**：
- 运营指标速览（GMV、订单数、退款率、客单价）
- 运营图表区（趋势图、退款率图、SKU Top 表格）
- AI 结构化决策区（风险等级、决策总结、建议动作）
- 快捷问题区（推荐问题、标准模板、自定义问题）

**右侧（AI Chat 面板）**：
- 使用 Ant Design X 的 Bubble 组件显示消息
- 使用 react-markdown 渲染 AI 回复
- 自动解析 JSON 决策数据并同步到左侧
- 支持思考过程和来源引用显示

### 2. 顶部工具栏

- 左侧：标题 + 副标题
- 中部：模型配置卡片（模型选择、温度、数据范围、包含系统数据）
- 右侧：设置、保存配置、重置默认按钮

### 3. AI 工作流

- **通用聊天 API**: `POST /api/frog-gpt/chat`
- **决策型分析**: 自动从 AI 回复中提取 ````json` 代码块
- **决策数据同步**: 提取的 JSON 自动更新左侧决策卡片

## 使用方法

### 1. 在路由中使用新页面

```typescript
import FrogGPTV2 from '@/pages/FrogGPT/FrogGPTV2'

// 在路由配置中
{
  path: '/frog-gpt',
  element: <FrogGPTV2 />,
}
```

### 2. 或者替换现有页面

将 `index.tsx` 的内容替换为 `FrogGPTV2.tsx` 的内容，或者直接重命名文件。

## 类型定义

### DecisionData

```typescript
interface DecisionData {
  decisionSummary?: string
  riskLevel?: 'low' | 'medium' | 'high'
  actions?: DecisionAction[]
  metadata?: {
    analysisDate?: string
    dataRange?: string
    confidence?: number
  }
}
```

### ChatMessage

```typescript
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
  thinking?: string
  sources?: Source[]
}
```

## API 集成

### 聊天 API

```typescript
const response = await frogGptApi.chat({
  messages: [...],
  model: 'auto',
  temperature: 0.7,
  include_system_data: true,
  data_summary_days: 7,
  shop_id: 1,
})
```

### 决策数据格式

AI 回复中应包含如下格式的 JSON 代码块：

````markdown
```json
{
  "decisionSummary": "整体运营状况良好...",
  "riskLevel": "low",
  "actions": [
    {
      "type": "优化SKU",
      "target": "SKU-12345",
      "delta": "退货率降低 5%",
      "reason": "该SKU退货率较高...",
      "priority": "high"
    }
  ]
}
```
````

## 样式主题

使用深色科技风格：
- 背景色：`#0f172a`、`#020617`
- 卡片背景：`#1e293b`
- 边框色：`#334155`
- 主色调：`#60a5fa`（蓝色）、`#00d1b2`（青色）

## 依赖项

- `@ant-design/x`: ^1.6.1
- `antd`: ^5.11.5
- `react-markdown`: ^10.1.0
- `echarts-for-react`: ^3.0.2

## 下一步优化

1. 集成真实的趋势数据 API
2. 集成真实的 SKU 排行 API
3. 优化快捷问题的交互（直接发送到聊天）
4. 添加更多图表类型（饼图、柱状图等）
5. 支持决策动作的导出和分享

