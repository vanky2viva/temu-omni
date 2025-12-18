/**
 * OrderList 页面类型定义
 */
import type { Dayjs } from 'dayjs'

export interface OrderListFilters {
  shopId?: number
  shopIds: number[]
  dateRange: [Dayjs, Dayjs] | null
  statusFilter?: string
  statusFilters: string[]
  searchKeyword: string
  orderSn: string
  productName: string
  productSku: string
  delayRiskLevel?: string
}

export interface OrderListView {
  id: number
  name: string
  description?: string
  filters: Partial<OrderListFilters>
  is_default?: boolean
}

export interface ProcessedOrder {
  id: number
  parent_order_sn?: string
  order_sn: string
  package_sn?: string
  product_name?: string
  product_sku?: string
  quantity: number
  total_price?: number
  status: string
  order_time?: string
  shipping_time?: string
  delivery_time?: string
  expect_ship_latest_time?: string
  _isFirstInGroup?: boolean
  _groupSize?: number
  _parentKey?: string
  _hasParent?: boolean
  _latestShippingTime?: string
  _groupDeliveryTime?: string
}

export interface OrderStatusStatistics {
  total_orders: number
  processing: number
  shipped: number
  delivered: number
  delayed_orders: number
  delay_rate: number
  trends?: {
    total?: number[]
    processing?: number[]
  }
  today_changes?: {
    total?: number
    processing?: number
    shipped?: number
    delivered?: number
  }
  week_changes?: {
    total?: number
  }
}

