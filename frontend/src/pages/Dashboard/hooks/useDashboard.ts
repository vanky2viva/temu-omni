import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { statisticsApi, analyticsApi } from '@/services/api'

export function useDashboard() {
  const [isMobile, setIsMobile] = useState(false)
  const REFRESH_INTERVAL = 5 * 60 * 1000

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['statistics', 'unified', 'overview'],
    queryFn: () => statisticsApi.getUnifiedOverview(),
    refetchInterval: REFRESH_INTERVAL,
  })

  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['statistics', 'unified', 'daily'],
    queryFn: () => statisticsApi.getUnifiedDaily({ days: 30 }),
    refetchInterval: REFRESH_INTERVAL,
  })

  return { isMobile, overview, overviewLoading, dailyData, dailyLoading }
}

