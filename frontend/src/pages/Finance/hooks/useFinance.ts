import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/services/api'
import dayjs from 'dayjs'
import type { Dayjs as DayjsType } from 'dayjs'

export function useFinance() {
  const [isMobile, setIsMobile] = useState(false)
  const [dateRange, setDateRange] = useState<[DayjsType, DayjsType] | null>(null)
  const [isAllData, setIsAllData] = useState(true)
  const [activeTabKey, setActiveTabKey] = useState<string>(() => {
    return localStorage.getItem('finance_active_tab') || 'estimated-collection'
  })

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const { data: monthlyStats, isLoading: monthlyStatsLoading } = useQuery({
    queryKey: ['sales-overview', isAllData ? 'all' : (dateRange ? `${dateRange[0].format('YYYY-MM-DD')}_${dateRange[1].format('YYYY-MM-DD')}` : 'month')],
    queryFn: () => {
      const params: any = {}
      if (!isAllData && dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }
      return analyticsApi.getSalesOverview(params)
    },
  })

  const { data: collectionData, isLoading: collectionLoading } = useQuery({
    queryKey: ['payment-collection', 'all'],
    queryFn: () => analyticsApi.getPaymentCollection({ days: 365 }),
  })

  return {
    isMobile,
    dateRange,
    setDateRange,
    isAllData,
    setIsAllData,
    activeTabKey,
    setActiveTabKey,
    monthlyStats,
    monthlyStatsLoading,
    collectionData,
    collectionLoading,
  }
}

