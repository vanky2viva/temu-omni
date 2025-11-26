/**
 * ChatKit 类型定义
 */

export interface ChatKitSession {
  session_id: string
  client_secret?: string
  metadata: {
    userId: string
    username: string
    tenantId: string
    shopId?: number
    allowedShops: number[]
    provider: string
    model: string
  }
  model: string
  base_url: string
  api_key_configured: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  tool_calls?: ToolCall[]
  tool_results?: ToolResult[]
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, any>
}

export interface ToolResult {
  tool_call_id: string
  result: any
  error?: string
}

/**
 * Dashboard 指令协议
 */
export type DashboardCommandType =
  | 'SET_DATE_RANGE'
  | 'SET_METRIC_CHART'
  | 'FOCUS_SKU'
  | 'COMPARE_SHOPS'
  | 'REFRESH_DATA'

export interface DashboardCommand {
  type: DashboardCommandType
  payload: {
    // SET_DATE_RANGE
    start_date?: string
    end_date?: string
    days?: number
    
    // SET_METRIC_CHART
    metric?: 'gmv' | 'orders' | 'profit' | 'refund_rate'
    chart_type?: 'line' | 'bar' | 'pie'
    
    // FOCUS_SKU
    sku?: string
    product_id?: number
    
    // COMPARE_SHOPS
    shop_ids?: number[]
    compare_metric?: string
    
    // REFRESH_DATA
    force?: boolean
  }
}

/**
 * Dashboard 状态
 */
export interface DashboardState {
  dateRange: {
    start: string
    end: string
  }
  selectedShops: number[]
  selectedMetric: 'gmv' | 'orders' | 'profit' | 'refund_rate'
  focusedSku?: string
  focusedProductId?: number
  chartType: 'line' | 'bar' | 'pie'
}


