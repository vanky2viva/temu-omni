import type { Dayjs } from 'dayjs'

export interface FinanceOverviewStats {
  total_gmv: number
  total_profit: number
}

export interface CollectionData {
  table_data: any[]
  summary: {
    shops: string[]
  }
  chart_data: {
    dates: string[]
    series: any[]
  }
}

export interface ProfitItem {
  parent_order_sn: string
  matched_order_count: number
  matched_parent_order_sns: string[]
  matched_order_sns: string[]
  package_sn: string
  product_name: string
  product_names: string[]
  sku: string
  skus: string[]
  quantity: number
  revenue: number
  sales_collection: number
  sales_collection_after_discount: number
  sales_reversal: number
  shipping_collection: number
  shipping_collection_after_discount: number
  product_cost: number
  shipping_cost: number
  chargeable_weight: number
  last_mile_cost: number
  deduction: number
  total_cost: number
  profit: number
  profit_rate: number
}

