import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message, App } from 'antd'
import { shopApi, syncApi } from '@/services/api'
import type { SyncProgress } from '../types'

export function useShopList() {
  const { modal } = App.useApp()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingShop, setEditingShop] = useState<any>(null)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [importingShop, setImportingShop] = useState<any>(null)
  const [syncingShopId, setSyncingShopId] = useState<number | null>(null)
  const [syncProgress, setSyncProgress] = useState<SyncProgress | null>(null)
  const [syncProgressModalVisible, setSyncProgressModalVisible] = useState(false)
  const [syncLogs, setSyncLogs] = useState<any[]>([])
  const [authModalShop, setAuthModalShop] = useState<any>(null)
  
  const progressIntervalRef = useRef<number | null>(null)

  // 获取店铺列表
  const { data: shops, isLoading, error: shopsError } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: shopApi.createShop,
    onSuccess: () => {
      message.success('店铺创建成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      setIsModalOpen(false)
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '店铺创建失败')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => shopApi.updateShop(id, data),
    onSuccess: () => {
      message.success('店铺更新成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      setIsModalOpen(false)
    },
    onError: () => {
      message.error('店铺更新失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: shopApi.deleteShop,
    onSuccess: () => {
      message.success('店铺删除成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '店铺删除失败')
    },
  })

  const syncMutation = useMutation({
    mutationFn: ({ shopId, fullSync }: { shopId: number; fullSync: boolean }) =>
      syncApi.syncShopAll(shopId, fullSync),
    onSuccess: (response: any) => {
      const shopId = response?.data?.shop_id
      setSyncingShopId(shopId)
      setSyncProgressModalVisible(true)
      startProgressPolling(shopId)
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.message || '数据同步失败'
      message.error(errorMsg)
      setSyncingShopId(null)
    },
  })

  const authorizeMutation = useMutation({
    mutationFn: ({ id, token, shopId }: { id: number; token: string; shopId?: string }) => 
      shopApi.authorizeShop(id, token, shopId),
    onSuccess: () => {
      message.success('授权成功')
      setAuthModalShop(null)
      queryClient.invalidateQueries({ queryKey: ['shops'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '授权失败')
    },
  })

  const startProgressPolling = (shopId: number) => {
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current)
    
    const fetchProgress = async () => {
      try {
        const [progressResponse, logsResponse] = await Promise.all([
          syncApi.getSyncProgress(shopId),
          syncApi.getSyncLogs(shopId, 50)
        ])
        const progress = progressResponse?.data || progressResponse
        const logs = logsResponse?.data || []
        setSyncProgress(progress)
        setSyncLogs(logs)
        
        if (progress?.status === 'completed' || progress?.status === 'error') {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current)
            progressIntervalRef.current = null
          }
          queryClient.invalidateQueries({ queryKey: ['shops'] })
          setSyncingShopId(null)
        }
      } catch (error) {}
    }

    fetchProgress()
    progressIntervalRef.current = window.setInterval(fetchProgress, 1000)
  }

  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current)
    }
  }, [])

  return {
    shops,
    isLoading,
    isModalOpen,
    setIsModalOpen,
    editingShop,
    setEditingShop,
    isImportModalOpen,
    setIsImportModalOpen,
    importingShop,
    setImportingShop,
    syncingShopId,
    syncProgress,
    syncProgressModalVisible,
    setSyncProgressModalVisible,
    syncLogs,
    authModalShop,
    setAuthModalShop,
    createMutation,
    updateMutation,
    deleteMutation,
    syncMutation,
    authorizeMutation,
    modal,
  }
}

