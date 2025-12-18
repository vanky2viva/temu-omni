export interface Shop {
  id: number
  shop_name: string
  region: string
  entity: string
  is_active: boolean
  has_api_config: boolean
  default_manager?: string
  last_sync_at?: string
  access_token?: string
  cn_access_token?: string
  description?: string
}

export interface SyncProgress {
  status: 'running' | 'completed' | 'error'
  progress: number
  current_step?: string
  error?: string
  time_info?: {
    processing_speed: number
    estimated_remaining_seconds: number
    processed_count: number
    total_count: number
  }
  estimated_completion_timestamp?: number
  orders?: {
    total: number
    new: number
    updated: number
    failed: number
    error?: string
  }
  products?: {
    total: number
    new: number
    updated: number
    failed: number
    error?: string
  }
  categories?: number | { error: string }
}

