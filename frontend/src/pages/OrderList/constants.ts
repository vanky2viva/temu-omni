/**
 * OrderList 页面常量定义
 */

export const STATUS_COLORS: Record<string, string> = {
  PENDING: 'default',
  PROCESSING: 'processing',
  SHIPPED: 'warning',
  DELIVERED: 'success',
  CANCELLED: 'error',
}

export const STATUS_LABELS: Record<string, string> = {
  PENDING: '待处理',
  PROCESSING: '未发货',
  SHIPPED: '已发货',
  DELIVERED: '已送达',
  CANCELLED: '已取消',
}

