import { useState, useMemo, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { shopApi, analyticsApi } from '@/services/api'
import dayjs from 'dayjs'
import type { Dayjs as DayjsType } from 'dayjs'

export function useSalesStatistics() {
  const queryClient = useQueryClient()
  const [isMobile, setIsMobile] = useState(false)
  const [dateRange, setDateRange] = useState<[DayjsType | null, DayjsType | null] | null>(null)
  const [quickSelectValue, setQuickSelectValue] = useState<string>('all')
  const [shopIds, setShopIds] = useState<number[]>([])
  const [manager, setManager] = useState<string | undefined>()
  const [region, setRegion] = useState<string | undefined>()
  const [activeTab, setActiveTab] = useState('sku')
  const [refreshTimestamp, setRefreshTimestamp] = useState<number>(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [countdown, setCountdown] = useState(300)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const { data: shops } = useQuery({ queryKey: ['shops'], queryFn: shopApi.getShops })

  const { data: salesOverview } = useQuery({
    queryKey: ['sales-overview', dateRange, shopIds, manager, region, refreshTimestamp],
    queryFn: async () => {
      const params: any = {}
      if (dateRange?.[0] && dateRange[1]) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (manager) params.manager = manager
      if (region) params.region = region
      if (refreshTimestamp > 0) params.refresh_cache = true
      return await analyticsApi.getSalesOverview(params)
    },
  })

  const { data: skuRanking, isLoading: skuLoading } = useQuery({
    queryKey: ['sku-sales-ranking', dateRange, shopIds, manager, region, refreshTimestamp],
    queryFn: async () => {
      const params: any = { limit: 100 }
      if (dateRange?.[0] && dateRange[1]) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (manager) params.manager = manager
      if (region) params.region = region
      if (refreshTimestamp > 0) params.refresh_cache = true
      return await analyticsApi.getSkuSalesRanking(params)
    },
    enabled: activeTab === 'sku',
  })

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    setRefreshTimestamp(Date.now())
    await queryClient.invalidateQueries({ queryKey: ['sales-overview'] })
    setIsRefreshing(false)
    setCountdown(300)
  }, [queryClient])

  return {
    isMobile,
    dateRange,
    setDateRange,
    quickSelectValue,
    setQuickSelectValue,
    shopIds,
    setShopIds,
    manager,
    setManager,
    region,
    setRegion,
    activeTab,
    setActiveTab,
    isRefreshing,
    countdown,
    handleRefresh,
    shops,
    salesOverview,
    skuRanking,
    skuLoading,
  }
}

