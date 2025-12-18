import type { Dayjs } from 'dayjs'

export interface Product {
  id: number
  product_name: string
  manager: string
  category: string
  shop_id: number
  product_id: string
  sku: string
  total_sales: number
  current_price: number
  current_cost_price: number
  listed_at: string
  created_at: string
  is_active: boolean
}

export interface ProductListFilters {
  shopId?: number
  statusFilter: 'published' | 'unpublished' | 'all'
  manager?: string
  category?: string
  keyword: string
}

export interface CostFormData {
  product_id: number
  cost_price: number
  currency: string
  effective_from: Dayjs
  notes?: string
}

