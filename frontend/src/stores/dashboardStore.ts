/**
 * Dashboard 状态管理（使用 Zustand）
 */
import { create } from 'zustand'
import { DashboardState, DashboardCommand } from '@/types/chatkit'
import dayjs from 'dayjs'

interface DashboardStore extends DashboardState {
  dispatchCommand: (command: DashboardCommand) => void
  setDateRange: (start: string, end: string) => void
  setSelectedShops: (shopIds: number[]) => void
  setSelectedMetric: (metric: DashboardState['selectedMetric']) => void
  setFocusedSku: (sku?: string, productId?: number) => void
  setChartType: (type: DashboardState['chartType']) => void
  reset: () => void
}

const defaultState: DashboardState = {
  dateRange: {
    start: dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    end: dayjs().format('YYYY-MM-DD'),
  },
  selectedShops: [],
  selectedMetric: 'gmv',
  chartType: 'line',
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  ...defaultState,

  dispatchCommand: (command: DashboardCommand) => {
    switch (command.type) {
      case 'SET_DATE_RANGE':
        if (command.payload.days) {
          const end = dayjs().format('YYYY-MM-DD')
          const start = dayjs().subtract(command.payload.days, 'day').format('YYYY-MM-DD')
          set({ dateRange: { start, end } })
        } else if (command.payload.start_date && command.payload.end_date) {
          set({
            dateRange: {
              start: command.payload.start_date,
              end: command.payload.end_date,
            },
          })
        }
        break

      case 'SET_METRIC_CHART':
        if (command.payload.metric) {
          set({ selectedMetric: command.payload.metric })
        }
        if (command.payload.chart_type) {
          set({ chartType: command.payload.chart_type })
        }
        if (command.payload.days) {
          const end = dayjs().format('YYYY-MM-DD')
          const start = dayjs().subtract(command.payload.days, 'day').format('YYYY-MM-DD')
          set({ dateRange: { start, end } })
        }
        break

      case 'FOCUS_SKU':
        set({
          focusedSku: command.payload.sku,
          focusedProductId: command.payload.product_id,
        })
        break

      case 'COMPARE_SHOPS':
        if (command.payload.shop_ids) {
          set({ selectedShops: command.payload.shop_ids })
        }
        if (command.payload.compare_metric) {
          set({ selectedMetric: command.payload.compare_metric as DashboardState['selectedMetric'] })
        }
        break

      case 'REFRESH_DATA':
        // 触发数据刷新（可以通过事件或回调实现）
        window.dispatchEvent(new CustomEvent('dashboard:refresh', { detail: { force: command.payload.force } }))
        break

      default:
        console.warn('Unknown dashboard command:', command)
    }
  },

  setDateRange: (start: string, end: string) => {
    set({ dateRange: { start, end } })
  },

  setSelectedShops: (shopIds: number[]) => {
    set({ selectedShops: shopIds })
  },

  setSelectedMetric: (metric: DashboardState['selectedMetric']) => {
    set({ selectedMetric: metric })
  },

  setFocusedSku: (sku?: string, productId?: number) => {
    set({ focusedSku: sku, focusedProductId: productId })
  },

  setChartType: (type: DashboardState['chartType']) => {
    set({ chartType: type })
  },

  reset: () => {
    set(defaultState)
  },
}))


