/**
 * FrogGPT 相关类型定义
 */

export interface ChatMessage {
  key: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: Date
}

export interface DecisionData {
  decisionSummary?: string
  riskLevel?: 'low' | 'medium' | 'high'
  actions?: Array<{
    type: string
    target: string
    delta?: string
    reason?: string
  }>
}

export interface MetricData {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
}

export interface QuickPrompt {
  label: string
  prompt: string
  icon?: string
}

