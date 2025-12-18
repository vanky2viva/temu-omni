import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message, Modal } from 'antd'
import { productApi, shopApi } from '@/services/api'
import type { ProductListFilters } from '../types'

export function useProductList() {
  const queryClient = useQueryClient()

  // 状态管理
  const [filters, setFilters] = useState<ProductListFilters>({
    shopId: undefined,
    statusFilter: 'published',
    manager: undefined,
    category: undefined,
    keyword: '',
  })

  const [isCostModalOpen, setIsCostModalOpen] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<any>(null)
  const [editingCostPrice, setEditingCostPrice] = useState<{ [key: number]: number | null }>({})
  const [editingSupplyPrice, setEditingSupplyPrice] = useState<{ [key: number]: number | null }>({})
  const [isEditingSupplyPrice, setIsEditingSupplyPrice] = useState<{ [key: number]: boolean }>({})
  const [isEditingCostPrice, setIsEditingCostPrice] = useState<{ [key: number]: boolean }>({})

  // 数据获取
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
  })

  const { data: products, isLoading } = useQuery({
    queryKey: ['products', filters],
    queryFn: () =>
      productApi.getProducts({
        shop_id: filters.shopId,
        is_active:
          filters.statusFilter === 'published' ? true : filters.statusFilter === 'unpublished' ? false : undefined,
        manager: filters.manager,
        category: filters.category,
        q: filters.keyword?.trim() || undefined,
        skip: 0,
        limit: 10000,
      }),
    staleTime: 0,
  })

  // Mutations
  const createCostMutation = useMutation({
    mutationFn: productApi.createProductCost,
    onSuccess: () => {
      message.success('成本记录添加成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setIsCostModalOpen(false)
      setSelectedProduct(null)
    },
    onError: () => {
      message.error('成本记录添加失败')
    },
  })

  const updateManagerMutation = useMutation({
    mutationFn: ({ id, manager }: { id: number; manager: string }) =>
      productApi.updateProduct(id, { manager }),
    onSuccess: () => {
      message.success('负责人更新成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      message.error('负责人更新失败')
    },
  })

  const updateCostPriceMutation = useMutation({
    mutationFn: ({ id, cost_price, currency }: { id: number; cost_price: number; currency?: string }) =>
      productApi.updateProductCost(id, { cost_price, currency: currency || 'CNY' }),
    onSuccess: () => {
      message.success('成本价格更新成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      message.error('成本价格更新失败')
    },
  })

  const updateSupplyPriceMutation = useMutation({
    mutationFn: ({ id, current_price }: { id: number; current_price: number }) =>
      productApi.updateProduct(id, { current_price }),
    onSuccess: () => {
      message.success('供货价更新成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      message.error('供货价更新失败')
    },
  })

  const clearProductsMutation = useMutation({
    mutationFn: (shopId?: number) => productApi.clearProducts(shopId),
    onSuccess: (data: any) => {
      message.success(data.message || '商品数据清理成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '商品数据清理失败')
    },
  })

  // 选项计算
  const managerOptions = useMemo(() => {
    const set = new Set<string>()
    products?.forEach((p: any) => p?.manager && set.add(p.manager))
    return Array.from(set)
  }, [products])

  const categoryOptions = useMemo(() => {
    const set = new Set<string>()
    products?.forEach((p: any) => p?.category && set.add(p.category))
    return Array.from(set)
  }, [products])

  return {
    filters,
    setFilters,
    shops,
    products,
    isLoading,
    isCostModalOpen,
    setIsCostModalOpen,
    selectedProduct,
    setSelectedProduct,
    managerOptions,
    categoryOptions,
    isEditingSupplyPrice,
    setIsEditingSupplyPrice,
    editingSupplyPrice,
    setEditingSupplyPrice,
    isEditingCostPrice,
    setIsEditingCostPrice,
    editingCostPrice,
    setEditingCostPrice,
    createCostMutation,
    updateManagerMutation,
    updateCostPriceMutation,
    updateSupplyPriceMutation,
    clearProductsMutation,
    queryClient,
  }
}

