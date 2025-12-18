import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { shopApi } from '@/services/api'
import axios from 'axios'
import dayjs from 'dayjs'

export function useHotSeller() {
  const [isMobile, setIsMobile] = useState(false)
  const currentDate = dayjs()
  const [year, setYear] = useState(currentDate.year())
  const [month, setMonth] = useState(currentDate.month() + 1)
  const [selectedShops, setSelectedShops] = useState<number[]>([])
  const [selectedManager, setSelectedManager] = useState<any>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const { data: shops } = useQuery({ queryKey: ['shops'], queryFn: shopApi.getShops })

  const { data: rankingData, isLoading } = useQuery({
    queryKey: ['hot-seller-ranking', year, month, selectedShops],
    queryFn: async () => {
      const params: any = { year, month }
      if (selectedShops.length > 0) params.shop_ids = selectedShops
      const res = await axios.get('/api/analytics/hot-seller-ranking', { params })
      return res.data
    },
  })

  const { data: managerSkus, isLoading: skuLoading } = useQuery({
    queryKey: ['manager-skus', selectedManager?.manager, year, month],
    queryFn: async () => {
      if (!selectedManager) return null
      const params = { manager: selectedManager.manager, year, month }
      const res = await axios.get('/api/analytics/manager-sku-details', { params })
      return res.data
    },
    enabled: !!selectedManager,
  })

  return {
    isMobile,
    year, setYear,
    month, setMonth,
    selectedShops, setSelectedShops,
    selectedManager, setSelectedManager,
    isDetailModalOpen, setIsDetailModalOpen,
    shops,
    rankingData,
    isLoading,
    managerSkus,
    skuLoading,
  }
}

