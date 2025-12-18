import type { Dayjs } from 'dayjs'

export interface SalesOverview {
  total_quantity: number
  total_orders: number
  total_gmv: number
  total_profit: number | null
  daily_trends: any[]
  shop_trends: Record<string, any[]>
}

export interface SkuRanking {
  ranking: any[]
}

export interface ManagerSales {
  managers: any[]
}

