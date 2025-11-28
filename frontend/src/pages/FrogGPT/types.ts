/**
 * FrogGPT 2.0 相关类型定义
 */

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
  thinking?: string // AI思考过程
  sources?: Source[] // 来源引用
}

export interface Source {
  title: string
  url?: string
  snippet?: string
}

export interface DecisionData {
  decisionSummary?: string
  riskLevel?: 'low' | 'medium' | 'high'
  actions?: DecisionAction[]
  metadata?: {
    analysisDate?: string
    dataRange?: string
    confidence?: number
  }
}

export interface DecisionAction {
  type: string
  target: string
  delta?: string
  reason?: string
  priority?: 'high' | 'medium' | 'low'
  estimatedImpact?: string
}

export interface MetricData {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  icon?: React.ReactNode
}

export interface QuickPrompt {
  id: string
  label: string
  prompt: string
  icon?: string
  category?: 'analysis' | 'optimization' | 'report' | 'custom'
}

export interface TrendData {
  date: string
  gmv: number
  orders: number
  profit: number
  refundRate: number
}

export interface SkuRankingItem {
  sku: string
  productName: string
  quantity: number
  orders: number
  gmv: number
  profit: number
  refundRate: number
  rank: number
}

