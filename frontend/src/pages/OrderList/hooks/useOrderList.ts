/**
 * OrderList 主业务逻辑 Hook
 */
import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { orderApi, shopApi, userViewsApi } from '@/services/api'
import type { OrderListFilters, ProcessedOrder, OrderStatusStatistics } from '../types'
import dayjs from 'dayjs'

export function useOrderList() {
  const [isMobile, setIsMobile] = useState(false)
  const [filters, setFilters] = useState<OrderListFilters>({
    shopId: undefined,
    shopIds: [],
    dateRange: null,
    statusFilter: undefined,
    statusFilters: [],
    searchKeyword: '',
    orderSn: '',
    productName: '',
    productSku: '',
    delayRiskLevel: undefined,
  })
  const [currentViewId, setCurrentViewId] = useState<number | null>(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  const queryClient = useQueryClient()

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
  })

  // 获取订单状态统计
  const { data: statusStats, isLoading: isLoadingStats } = useQuery<OrderStatusStatistics>({
    queryKey: ['order-status-statistics', filters.shopIds, filters.shopId, filters.dateRange],
    queryFn: async () => {
      const params: any = {}
      if (filters.shopIds && filters.shopIds.length > 0) {
        params.shop_ids = filters.shopIds
      } else if (filters.shopId) {
        params.shop_id = filters.shopId
      }
      if (filters.dateRange) {
        params.start_date = filters.dateRange[0].toISOString()
        params.end_date = filters.dateRange[1].toISOString()
      }
      return await orderApi.getStatusStatistics(params)
    },
    staleTime: 30000,
  })

  // 获取订单列表
  const { data: ordersData, isLoading } = useQuery({
    queryKey: [
      'orders',
      filters.shopIds,
      filters.shopId,
      filters.dateRange,
      filters.statusFilters,
      filters.statusFilter,
      filters.searchKeyword,
      filters.orderSn,
      filters.productName,
      filters.productSku,
      filters.delayRiskLevel,
      pagination.current,
      pagination.pageSize,
    ],
    queryFn: async () => {
      const params: any = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      }
      if (filters.shopIds && filters.shopIds.length > 0) {
        params.shop_ids = filters.shopIds
      } else if (filters.shopId) {
        params.shop_id = filters.shopId
      }
      if (filters.dateRange) {
        params.start_date = filters.dateRange[0].toISOString()
        params.end_date = filters.dateRange[1].toISOString()
      }
      if (filters.statusFilter) {
        params.status_filter = filters.statusFilter
      } else if (filters.statusFilters && filters.statusFilters.length > 0) {
        params.status_filters = filters.statusFilters
      }
      if (filters.searchKeyword) params.search = filters.searchKeyword
      if (filters.orderSn) params.order_sn = filters.orderSn
      if (filters.productName) params.product_name = filters.productName
      if (filters.productSku) params.product_sku = filters.productSku
      if (filters.delayRiskLevel) params.delay_risk_level = filters.delayRiskLevel
      return await orderApi.getOrders(params)
    },
    staleTime: 30000,
  })

  // 更新分页总数
  useEffect(() => {
    if (ordersData) {
      if (ordersData && typeof ordersData === 'object' && 'total' in ordersData) {
        const total = ordersData.total as number
        setPagination(prev => {
          if (prev.total !== total) {
            return { ...prev, total }
          }
          return prev
        })
      } else if (Array.isArray(ordersData)) {
        setPagination(prev => ({ ...prev, total: ordersData.length }))
      }
    }
  }, [ordersData])

  // 处理订单数据，按父订单号分组
  const processedOrders = useMemo<ProcessedOrder[]>(() => {
    const ordersList = Array.isArray(ordersData)
      ? ordersData
      : ((ordersData as any)?.items || [])

    if (!ordersList || ordersList.length === 0) return []

    const groupedByParent: Record<string, any[]> = {}
    ordersList.forEach((order: any) => {
      const parentKey = order.parent_order_sn || `single_${order.order_sn}`
      if (!groupedByParent[parentKey]) {
        groupedByParent[parentKey] = []
      }
      groupedByParent[parentKey].push(order)
    })

    const result: ProcessedOrder[] = []
    Object.keys(groupedByParent).forEach((parentKey) => {
      const group = groupedByParent[parentKey]

      let latestShippingTime: string | null = null
      const shippingTimes = group
        .map((o: any) => o.shipping_time)
        .filter((t: any) => t != null)
        .map((t: string) => new Date(t).getTime())

      if (shippingTimes.length > 0) {
        const latestTime = Math.max(...shippingTimes)
        latestShippingTime = new Date(latestTime).toISOString()
      }

      const deliveryTime = group.find((o: any) => o.status === 'DELIVERED' && o.delivery_time)?.delivery_time || null
      const expectShipLatestTime = group.find((o: any) => o.expect_ship_latest_time)?.expect_ship_latest_time || null

      group.forEach((order, index) => {
        result.push({
          ...order,
          _isFirstInGroup: index === 0,
          _groupSize: group.length,
          _parentKey: parentKey,
          _hasParent: !!order.parent_order_sn,
          _latestShippingTime: expectShipLatestTime || latestShippingTime,
          _groupDeliveryTime: deliveryTime,
        })
      })
    })

    return result
  }, [ordersData])

  // 当筛选条件改变时，重置到第一页
  const handleFilterChange = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  return {
    isMobile,
    filters,
    setFilters,
    currentViewId,
    setCurrentViewId,
    pagination,
    setPagination,
    selectedRowKeys,
    setSelectedRowKeys,
    shops,
    statusStats,
    isLoadingStats,
    processedOrders,
    isLoading,
    handleFilterChange,
    queryClient,
  }
}

