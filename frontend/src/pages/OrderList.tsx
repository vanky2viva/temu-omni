import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Space, Select, DatePicker, Tag, Tooltip, Button, message, Row, Col, Input, Collapse, Modal, Dropdown } from 'antd'
import { CopyOutlined, SearchOutlined, FilterOutlined, DownOutlined, UpOutlined, ReloadOutlined, SaveOutlined, FolderOutlined, DeleteOutlined, ExportOutlined, TagOutlined, FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { orderApi, shopApi, userViewsApi } from '@/services/api'
import EnhancedKPICard from '@/components/EnhancedKPICard'
import OrderDetailDrawer from '@/components/OrderDetailDrawer'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const statusColors: Record<string, string> = {
  PENDING: 'default',
  PROCESSING: 'processing',
  SHIPPED: 'warning',
  DELIVERED: 'success',
  CANCELLED: 'error',
}

const statusLabels: Record<string, string> = {
  PENDING: '待处理',
  PROCESSING: '未发货',
  SHIPPED: '已发货',
  DELIVERED: '已送达',
  CANCELLED: '已取消',
}

function OrderList() {
  const [isMobile, setIsMobile] = useState(false)
  const [shopId, setShopId] = useState<number | undefined>()
  const [shopIds, setShopIds] = useState<number[]>([]) // 多选店铺
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [statusFilters, setStatusFilters] = useState<string[]>([]) // 多选状态
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [orderSn, setOrderSn] = useState<string>('')
  const [productName, setProductName] = useState<string>('')
  const [productSku, setProductSku] = useState<string>('')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false) // 高级筛选展开状态
  const [delayRiskLevel, setDelayRiskLevel] = useState<string | undefined>(undefined) // 延误风险等级
  const [currentViewId, setCurrentViewId] = useState<number | null>(null) // 当前视图ID
  const [saveViewModalVisible, setSaveViewModalVisible] = useState(false) // 保存视图对话框
  const [viewName, setViewName] = useState('') // 视图名称
  const [viewDescription, setViewDescription] = useState('') // 视图描述
  const [isDefaultView, setIsDefaultView] = useState(false) // 是否设为默认视图
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false) // 订单详情Drawer
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null) // 选中的订单ID
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]) // 选中的订单ID列表
  
  const queryClient = useQueryClient()
  
  // 获取用户视图列表
  const { data: userViews } = useQuery({
    queryKey: ['user-views', 'order_list'],
    queryFn: async () => {
      const result = await userViewsApi.getViews('order_list')
      return result || []
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  })
  
  // 获取默认视图
  useEffect(() => {
    const loadDefaultView = async () => {
      try {
        const defaultView = await userViewsApi.getDefaultView('order_list')
        if (defaultView) {
          loadView(defaultView)
        }
      } catch (error) {
        // 如果没有默认视图，忽略错误
      }
    }
    loadDefaultView()
  }, [])
  
  // 加载视图
  const loadView = (view: any) => {
    if (view.filters) {
      // 加载筛选条件
      if (view.filters.shop_ids) {
        setShopIds(view.filters.shop_ids)
        setShopId(view.filters.shop_ids.length === 1 ? view.filters.shop_ids[0] : undefined)
      } else if (view.filters.shop_id) {
        setShopId(view.filters.shop_id)
        setShopIds(view.filters.shop_id ? [view.filters.shop_id] : [])
      }
      
      if (view.filters.status_filters) {
        setStatusFilters(view.filters.status_filters)
        setStatusFilter(view.filters.status_filters.length === 1 ? view.filters.status_filters[0] : undefined)
      } else if (view.filters.status_filter) {
        setStatusFilter(view.filters.status_filter)
        setStatusFilters(view.filters.status_filter ? [view.filters.status_filter] : [])
      }
      
      if (view.filters.date_range) {
        setDateRange([
          dayjs(view.filters.date_range[0]),
          dayjs(view.filters.date_range[1])
        ])
      }
      
      if (view.filters.search) setSearchKeyword(view.filters.search)
      if (view.filters.order_sn) setOrderSn(view.filters.order_sn)
      if (view.filters.product_name) setProductName(view.filters.product_name)
      if (view.filters.product_sku) setProductSku(view.filters.product_sku)
      if (view.filters.delay_risk_level) setDelayRiskLevel(view.filters.delay_risk_level)
    }
    
    setCurrentViewId(view.id)
    message.success(`已加载视图: ${view.name}`)
  }
  
  // 保存视图
  const saveViewMutation = useMutation({
    mutationFn: async (data: any) => {
      if (currentViewId) {
        return await userViewsApi.updateView(currentViewId, data)
      } else {
        return await userViewsApi.createView(data)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-views'] })
      setSaveViewModalVisible(false)
      setViewName('')
      setViewDescription('')
      setIsDefaultView(false)
      message.success(currentViewId ? '视图已更新' : '视图已保存')
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '保存视图失败')
    },
  })
  
  // 删除视图
  const deleteViewMutation = useMutation({
    mutationFn: async (viewId: number) => {
      return await userViewsApi.deleteView(viewId)
    },
    onSuccess: (_, viewId) => {
      queryClient.invalidateQueries({ queryKey: ['user-views'] })
      if (currentViewId === viewId) {
        setCurrentViewId(null)
      }
      message.success('视图已删除')
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除视图失败')
    },
  })
  
  // 批量导出
  const handleBatchExport = async (format: 'csv' | 'excel') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要导出的订单')
      return
    }
    
    try {
      // TODO: 实现批量导出API
      message.info(`正在导出 ${selectedRowKeys.length} 个订单为 ${format.toUpperCase()} 格式...`)
      // 这里需要调用后端API进行导出
    } catch (error) {
      message.error('导出失败')
    }
  }
  
  // 批量修改标签
  const handleBatchTags = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要修改标签的订单')
      return
    }
    
    Modal.confirm({
      title: '批量修改标签',
      content: (
        <div style={{ marginTop: '16px' }}>
          <div style={{ marginBottom: '8px' }}>请输入标签名称：</div>
          <Input
            id="batch-tag-input"
            placeholder="标签名称"
          />
        </div>
      ),
      onOk: () => {
        const input = document.getElementById('batch-tag-input') as HTMLInputElement
        const tagName = input?.value?.trim()
        if (!tagName) {
          message.warning('请输入标签名称')
          return
        }
        // TODO: 实现批量添加标签API
        message.success(`已为 ${selectedRowKeys.length} 个订单添加标签：${tagName}`)
      },
    })
  }
  
  // 批量添加备注
  const handleBatchNotes = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要添加备注的订单')
      return
    }
    
    Modal.confirm({
      title: '批量添加备注',
      width: 500,
      content: (
        <div style={{ marginTop: '16px' }}>
          <div style={{ marginBottom: '8px' }}>备注内容：</div>
          <Input.TextArea
            id="batch-note-input"
            placeholder="请输入备注内容..."
            rows={4}
          />
        </div>
      ),
      onOk: () => {
        const textarea = document.getElementById('batch-note-input') as HTMLTextAreaElement
        const noteContent = textarea?.value?.trim()
        if (!noteContent) {
          message.warning('请输入备注内容')
          return
        }
        // TODO: 实现批量添加备注API
        message.success(`已为 ${selectedRowKeys.length} 个订单添加备注`)
      },
    })
  }
  
  // 批量修改状态
  const handleBatchStatus = (status: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要修改状态的订单')
      return
    }
    
    const statusLabels: Record<string, string> = {
      SHIPPED: '已发货',
      DELIVERED: '已送达',
      CANCELLED: '已取消',
    }
    
    const confirmMessage = status === 'CANCELLED'
      ? `确定要将 ${selectedRowKeys.length} 个订单标记为已取消吗？此操作不可撤销！`
      : `确定要将 ${selectedRowKeys.length} 个订单标记为${statusLabels[status]}吗？`
    
    Modal.confirm({
      title: '批量修改状态',
      content: confirmMessage,
      okText: '确定',
      cancelText: '取消',
      okType: status === 'CANCELLED' ? 'danger' : 'primary',
      onOk: () => {
        // TODO: 实现批量修改状态API
        message.success(`已将 ${selectedRowKeys.length} 个订单标记为${statusLabels[status]}`)
        setSelectedRowKeys([])
        // 刷新订单列表
        queryClient.invalidateQueries({ queryKey: ['orders'] })
      },
    })
  }
  
  // 保存当前视图
  const handleSaveView = () => {
    if (!viewName.trim()) {
      message.warning('请输入视图名称')
      return
    }
    
    const filters = {
      shop_ids: shopIds.length > 0 ? shopIds : undefined,
      shop_id: shopId,
      status_filters: statusFilters.length > 0 ? statusFilters : undefined,
      status_filter: statusFilter,
      date_range: dateRange ? [dateRange[0].toISOString(), dateRange[1].toISOString()] : undefined,
      search: searchKeyword || undefined,
      order_sn: orderSn || undefined,
      product_name: productName || undefined,
      product_sku: productSku || undefined,
      delay_risk_level: delayRiskLevel || undefined,
    }
    
    // 移除undefined值
    Object.keys(filters).forEach(key => {
      if (filters[key as keyof typeof filters] === undefined) {
        delete filters[key as keyof typeof filters]
      }
    })
    
    saveViewMutation.mutate({
      name: viewName,
      view_type: 'order_list',
      description: viewDescription || undefined,
      filters,
      is_default: isDefaultView,
    })
  }
  
  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // 当筛选条件改变时，重置到第一页
  const handleFilterChange = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
  })

  // 获取订单状态统计
  const { data: statusStats, isLoading: isLoadingStats, error: statusStatsError } = useQuery({
    queryKey: ['order-status-statistics', shopIds, shopId, dateRange],
    queryFn: async () => {
      const params: any = {}
      // 优先使用多选店铺，如果没有则使用单选
      if (shopIds && shopIds.length > 0) {
        params.shop_ids = shopIds
      } else if (shopId) {
        params.shop_id = shopId
      }
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      try {
        const result = await orderApi.getStatusStatistics(params)
        console.log('Status stats result:', result) // 调试日志
        return result
      } catch (error) {
        console.error('Failed to fetch status statistics:', error) // 调试日志
        throw error
      }
    },
    staleTime: 30000, // 30秒缓存
  })
  
  // 调试：输出状态统计数据
  useEffect(() => {
    if (statusStats) {
      console.log('Status stats loaded:', statusStats)
    }
    if (statusStatsError) {
      console.error('Status stats error:', statusStatsError)
    }
  }, [statusStats, statusStatsError])

  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })

  // 获取订单列表（使用分页）
  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['orders', shopIds, shopId, dateRange, statusFilters, statusFilter, searchKeyword, orderSn, productName, productSku, delayRiskLevel, pagination.current, pagination.pageSize],
    queryFn: async () => {
      const params: any = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      }
      // 优先使用多选店铺，如果没有则使用单选
      if (shopIds && shopIds.length > 0) {
        params.shop_ids = shopIds
      } else if (shopId) {
        params.shop_id = shopId
      }
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      // 优先使用多选状态，如果没有则使用单选
      if (statusFilters && statusFilters.length > 0) {
        params.status_filters = statusFilters
      } else if (statusFilter) {
        params.status_filter = statusFilter
      }
      if (searchKeyword) params.search = searchKeyword
      if (orderSn) params.order_sn = orderSn
      if (productName) params.product_name = productName
      if (productSku) params.product_sku = productSku
      if (delayRiskLevel) params.delay_risk_level = delayRiskLevel
      const result = await orderApi.getOrders(params)
      return result
    },
    staleTime: 30000, // 30秒缓存
  })
  
  // 从API响应中提取数据并更新分页
  useEffect(() => {
    if (ordersData) {
      if (ordersData && typeof ordersData === 'object' && 'total' in ordersData) {
        const total = ordersData.total as number
        setPagination(prev => {
          if (prev.total !== total) {
            console.log('更新分页总数:', { total, current: prev.current, pageSize: prev.pageSize })
            return { ...prev, total }
          }
          return prev
        })
      } else if (Array.isArray(ordersData)) {
        // 兼容旧的数据结构（直接返回数组）
        setPagination(prev => ({ ...prev, total: ordersData.length }))
      }
    }
  }, [ordersData])

  // 兼容新旧数据结构
  const orders = Array.isArray(ordersData) 
    ? ordersData  // 旧格式：直接返回数组
    : ((ordersData as any)?.items || [])  // 新格式：分页响应对象

  // 处理订单数据，按父订单号分组，用于合并显示
  const processedOrders = useMemo(() => {
    const ordersList = orders || []
    if (!ordersList || ordersList.length === 0) return []
    
    // 按父订单号分组
    const groupedByParent: Record<string, any[]> = {}
    ordersList.forEach((order: any) => {
      const parentKey = order.parent_order_sn || `single_${order.order_sn}`
      if (!groupedByParent[parentKey]) {
        groupedByParent[parentKey] = []
      }
      groupedByParent[parentKey].push(order)
    })
    
    // 展平数据，添加合并信息
    const result: any[] = []
    Object.keys(groupedByParent).forEach((parentKey) => {
      const group = groupedByParent[parentKey]
      
      // 计算该组中最晚的发货时间
      let latestShippingTime: string | null = null
      const shippingTimes = group
        .map((o: any) => o.shipping_time)
        .filter((t: any) => t != null)
        .map((t: string) => new Date(t).getTime())
      
      if (shippingTimes.length > 0) {
        const latestTime = Math.max(...shippingTimes)
        latestShippingTime = new Date(latestTime).toISOString()
      }
      
      // 获取该组的签收时间（仅当状态为DELIVERED时才有签收时间）
      const deliveryTime = group.find((o: any) => o.status === 'DELIVERED' && o.delivery_time)?.delivery_time || null
      
      // 获取该组的最晚发货时间
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
  }, [orders])

  // 复制到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'parent_order_sn',
      key: 'parent_order_sn',
      width: 150,
      fixed: 'left' as const,
      render: (parentSn: string, record: any) => {
        const displayValue = parentSn || record.order_sn || '-'
        
        if (!record._hasParent) {
          return {
            children: (
              <div 
                style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', cursor: 'pointer' }}
                onClick={() => {
                  setSelectedOrderId(record.id)
                  setDetailDrawerVisible(true)
                }}
              >
                <span style={{ fontFamily: 'monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {displayValue}
                </span>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    copyToClipboard(displayValue)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              </div>
            ),
            props: { rowSpan: 1 },
          }
        }
        
        if (record._isFirstInGroup && record._groupSize > 1) {
          return {
            children: (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
                <span style={{ fontFamily: 'monospace', fontWeight: 'bold', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {displayValue}
                </span>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    copyToClipboard(displayValue)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              </div>
            ),
            props: { rowSpan: record._groupSize },
          }
        } else if (record._groupSize > 1) {
          return {
            children: null,
            props: { rowSpan: 0 },
          }
        }
        return {
          children: (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
              <span style={{ fontFamily: 'monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {displayValue}
              </span>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                onClick={(e) => {
                  e.stopPropagation()
                  copyToClipboard(displayValue)
                }}
                style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
              />
            </div>
          ),
          props: { rowSpan: 1 },
        }
      },
    },
    {
      title: '子订单号',
      dataIndex: 'order_sn',
      key: 'order_sn',
      width: 150,
      fixed: 'left' as const,
      render: (sn: string, record: any) => {
        // 如果订单有父订单号，且不是第一行，不显示
        if (record._hasParent && record._groupSize > 1 && !record._isFirstInGroup) {
          return {
            children: null,
            props: { rowSpan: 0 },
          }
        }
        
        const displaySn = sn || '-'
        
        return {
          children: (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
              <span style={{ fontFamily: 'monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {displaySn}
              </span>
              {sn && (
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    copyToClipboard(sn)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              )}
            </div>
          ),
          props: record._hasParent && record._groupSize > 1 && record._isFirstInGroup 
            ? { rowSpan: record._groupSize }
            : { rowSpan: 1 },
        }
      },
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 250,
      ellipsis: true,
      render: (text: string) => {
        if (!text) return '-'
        const displayText = text.length > 20 ? text.substring(0, 20) + '...' : text
        return (
          <Tooltip title={text}>
            <span>{displayText}</span>
          </Tooltip>
        )
      },
    },
    {
      title: 'SKU货号',
      dataIndex: 'product_sku',
      key: 'product_sku',
      width: 150,
      render: (sku: string) => sku || '-',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'center' as const,
    },
    {
      title: '订单金额',
      dataIndex: 'total_price',
      key: 'total_price',
      width: 120,
      align: 'right' as const,
      render: (price: number | null | undefined) => {
        if (price === null || price === undefined || price === 0) return '-'
        const priceNum = typeof price === 'number' ? price : parseFloat(String(price)) || 0
        return (
          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
            ¥{priceNum.toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => {
        const statusKey = status?.toUpperCase() || 'PENDING'
        return (
          <Tag color={statusColors[statusKey]}>
            {statusLabels[statusKey] || status}
          </Tag>
        )
      },
    },
    {
      title: '下单时间',
      dataIndex: 'order_time',
      key: 'order_time',
      width: 180,
      render: (time: string) => 
        time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '最晚发货时间',
      dataIndex: 'shipping_time',
      key: 'latest_shipping_time',
      width: 180,
      render: (time: string, record: any) => {
        const displayTime = record._latestShippingTime || time
        
        if (!displayTime) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }
        
        if (record._groupSize > 1 && record._hasParent) {
          if (record._isFirstInGroup) {
            return {
              children: (
                <div style={{ fontSize: '12px' }}>
                  {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              ),
              props: { rowSpan: record._groupSize },
            }
          } else {
            return {
              children: null,
              props: { rowSpan: 0 },
            }
          }
        }
        
        return {
          children: (
            <div style={{ fontSize: '12px' }}>
              {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          ),
          props: { rowSpan: 1 },
        }
      },
    },
    {
      title: '签收时间',
      dataIndex: 'delivery_time',
      key: 'delivery_time',
      width: 180,
      render: (time: string, record: any) => {
        const isDelivered = record.status === 'DELIVERED'
        
        if (!isDelivered) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }
        
        const displayTime = (record._groupSize > 1 && record._hasParent) 
          ? record._groupDeliveryTime 
          : time
        
        if (!displayTime) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }
        
        if (record._groupSize > 1 && record._hasParent) {
          if (record._isFirstInGroup) {
            return {
              children: (
                <div style={{ fontSize: '12px' }}>
                  {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              ),
              props: { rowSpan: record._groupSize },
            }
          } else {
            return {
              children: null,
              props: { rowSpan: 0 },
            }
          }
        }
        
        return {
          children: (
            <div style={{ fontSize: '12px' }}>
              {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          ),
          props: { rowSpan: 1 },
        }
      },
    },
  ]

  return (
    <div>
        <h2 style={{ 
          margin: 0,
          marginBottom: '16px',
        fontSize: isMobile ? '18px' : '20px',
          fontWeight: 600,
          color: 'var(--color-fg)'
        }}>
        订单列表
        </h2>
      
      <div style={{ marginBottom: '20px' }}>
        {/* 增强的KPI统计卡片 */}
        <Row gutter={[8, 8]}>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '总订单数',
                  value: (statusStats as any)?.total_orders ?? 0,
                  trend: (statusStats as any)?.trends?.total || [],
                  todayChange: (statusStats as any)?.today_changes?.total,
                  weekChange: (statusStats as any)?.week_changes?.total,
                  color: '#1677ff',
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '未发货',
                  value: (statusStats as any)?.processing ?? 0,
                  trend: (statusStats as any)?.trends?.processing || [],
                  todayChange: (statusStats as any)?.today_changes?.processing,
                  weekChange: (statusStats as any)?.week_changes?.processing,
                  color: '#faad14',
                  valueStyle: { color: '#faad14' },
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '已发货',
                  value: (statusStats as any)?.shipped ?? 0,
                  trend: [], // 不显示趋势图表
                  todayChange: (statusStats as any)?.today_changes?.shipped,
                  weekChange: (statusStats as any)?.week_changes?.shipped,
                  color: '#1890ff',
                  valueStyle: { color: '#1890ff' },
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '已送达',
                  value: (statusStats as any)?.delivered ?? 0,
                  trend: [], // 不显示趋势图表
                  todayChange: (statusStats as any)?.today_changes?.delivered,
                  weekChange: (statusStats as any)?.week_changes?.delivered,
                  color: '#52c41a',
                  valueStyle: { color: '#52c41a' },
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '延误订单',
                  value: (statusStats as any)?.delayed_orders ?? 0,
                  color: '#ff4d4f',
                  valueStyle: { color: '#ff4d4f' },
                }}
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <EnhancedKPICard
                isMobile={isMobile}
                data={{
                  loading: isLoadingStats,
                  title: '延误率',
                  value: (statusStats as any)?.delay_rate ?? 0,
                  precision: 2,
                  suffix: '%',
                  color: ((statusStats as any)?.delay_rate ?? 0) > 10 ? '#ff4d4f' : '#52c41a',
                  valueStyle: { 
                    color: ((statusStats as any)?.delay_rate ?? 0) > 10 ? '#ff4d4f' : '#52c41a',
                    whiteSpace: 'nowrap',
                  },
                }}
              />
            </Col>
          </Row>
      </div>
      
        {/* 保存视图对话框 */}
        <Modal
          title={currentViewId ? '更新视图' : '保存视图'}
          open={saveViewModalVisible}
          onOk={handleSaveView}
          onCancel={() => {
            setSaveViewModalVisible(false)
            setViewName('')
            setViewDescription('')
            setIsDefaultView(false)
          }}
          confirmLoading={saveViewMutation.isPending}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <div style={{ marginBottom: '8px' }}>视图名称：</div>
              <Input
                placeholder="请输入视图名称"
                value={viewName}
                onChange={(e) => setViewName(e.target.value)}
              />
            </div>
            <div>
              <div style={{ marginBottom: '8px' }}>视图描述：</div>
              <Input.TextArea
                placeholder="请输入视图描述（可选）"
                value={viewDescription}
                onChange={(e) => setViewDescription(e.target.value)}
                rows={3}
              />
            </div>
            <div>
              <Input
                type="checkbox"
                checked={isDefaultView}
                onChange={(e) => setIsDefaultView(e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span>设为默认视图</span>
            </div>
          </Space>
        </Modal>

        {/* 常用筛选和搜索（一行显示） */}
        <div style={{ marginBottom: '16px' }}>
          <Space 
            size={isMobile ? "small" : "middle"} 
            wrap 
            direction={isMobile ? "vertical" : "horizontal"}
            style={{ width: '100%' }}
          >
            {/* 视图选择器 */}
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'save',
                    label: '保存当前视图',
                    icon: <SaveOutlined />,
                    onClick: () => {
                      setViewName('')
                      setViewDescription('')
                      setIsDefaultView(false)
                      setSaveViewModalVisible(true)
                    },
                  },
                  ...(userViews && Array.isArray(userViews) && userViews.length > 0 ? [
                    { type: 'divider' as const },
                    ...(userViews as any[]).map((view: any) => ({
                      key: `view-${view.id}`,
                      label: (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                          <span>{view.name}{view.is_default && ' (默认)'}</span>
                          <Space>
                            <Button
                              type="text"
                              size="small"
                              icon={<DeleteOutlined />}
                              onClick={(e) => {
                                e.stopPropagation()
                                Modal.confirm({
                                  title: '确认删除',
                                  content: `确定要删除视图"${view.name}"吗？`,
                                  onOk: () => deleteViewMutation.mutate(view.id),
                                })
                              }}
                            />
                          </Space>
                        </div>
                      ),
                      onClick: () => loadView(view),
                    }))
                  ] : []),
                ],
              }}
              trigger={['click']}
            >
              <Button icon={<FolderOutlined />}>
                {currentViewId 
                  ? (userViews as any)?.find((v: any) => v.id === currentViewId)?.name || '选择视图'
                  : '视图'}
              </Button>
            </Dropdown>
            
            {/* 搜索框 */}
            <Input
              placeholder="搜索订单号、商品名称或SKU..."
              prefix={<SearchOutlined />}
              allowClear
              value={searchKeyword}
              onChange={(e) => {
                setSearchKeyword(e.target.value)
                handleFilterChange()
              }}
              onPressEnter={() => handleFilterChange()}
              style={{ 
                width: isMobile ? '100%' : '280px',
              }}
            />
            
            {/* 店铺筛选 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
              <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>店铺：</span>
            <Select
                mode="multiple"
                style={{ width: isMobile ? '100%' : 180 }}
              placeholder="全部店铺"
              allowClear
                value={shopIds.length > 0 ? shopIds : undefined}
                onChange={(values) => {
                  setShopIds(values || [])
                  // 兼容单选逻辑（保留shopId用于向后兼容）
                  setShopId(values && values.length === 1 ? values[0] : undefined)
                handleFilterChange()
              }}
              options={Array.isArray(shops) ? shops.map((shop: any) => ({
                label: shop.shop_name,
                value: shop.id,
              })) : []}
            />
          </div>
            
            {/* 状态筛选 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
              <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>状态：</span>
            <Select
                mode="multiple"
                style={{ width: isMobile ? '100%' : 180 }}
              placeholder="全部状态"
              allowClear
                value={statusFilters.length > 0 ? statusFilters : undefined}
                onChange={(values) => {
                  setStatusFilters(values || [])
                  // 兼容单选逻辑
                  setStatusFilter(values && values.length === 1 ? values[0] : undefined)
                handleFilterChange()
              }}
              options={[
                { label: '待处理', value: 'PENDING' },
                { label: '未发货', value: 'PROCESSING' },
                { label: '已发货', value: 'SHIPPED' },
                { label: '已送达', value: 'DELIVERED' },
                { label: '已取消', value: 'CANCELLED' },
              ]}
            />
          </div>
            
            {/* 日期筛选 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
              <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>日期：</span>
              <Space size="small" wrap>
                {/* 快捷时间选择下拉框 */}
                <Select
                  placeholder="快捷选择"
                  allowClear
                  style={{ width: isMobile ? '100%' : 120 }}
                  onChange={(value) => {
                    if (!value) {
                      setDateRange(null)
                      handleFilterChange()
                      return
                    }
                    
                    let start: dayjs.Dayjs
                    let end: dayjs.Dayjs = dayjs()
                    
                    switch (value) {
                      case 'today':
                        start = dayjs().startOf('day')
                        end = dayjs().endOf('day')
                        break
                      case 'yesterday':
                        start = dayjs().subtract(1, 'day').startOf('day')
                        end = dayjs().subtract(1, 'day').endOf('day')
                        break
                      case 'last7days':
                        start = dayjs().subtract(6, 'day').startOf('day')
                        end = dayjs().endOf('day')
                        break
                      case 'last30days':
                        start = dayjs().subtract(29, 'day').startOf('day')
                        end = dayjs().endOf('day')
                        break
                      case 'thisMonth':
                        start = dayjs().startOf('month')
                        end = dayjs().endOf('month')
                        break
                      case 'lastMonth':
                        start = dayjs().subtract(1, 'month').startOf('month')
                        end = dayjs().subtract(1, 'month').endOf('month')
                        break
                      default:
                        return
                    }
                    
                    setDateRange([start, end])
                    handleFilterChange()
                  }}
                  options={[
                    { label: '今天', value: 'today' },
                    { label: '昨天', value: 'yesterday' },
                    { label: '最近7天', value: 'last7days' },
                    { label: '最近30天', value: 'last30days' },
                    { label: '本月', value: 'thisMonth' },
                    { label: '上月', value: 'lastMonth' },
                  ]}
                />
            <RangePicker
                  value={dateRange}
              onChange={(dates) => {
                setDateRange(dates as any)
                handleFilterChange()
              }}
              format="YYYY-MM-DD"
                  style={{ width: isMobile ? '100%' : 240 }}
            />
              </Space>
          </div>
            
            {/* 重置按钮 */}
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                // 重置所有筛选条件
                setShopIds([])
                setShopId(undefined)
                setStatusFilters([])
                setStatusFilter(undefined)
                setDateRange(null)
                setSearchKeyword('')
                setOrderSn('')
                setProductName('')
                setProductSku('')
                setDelayRiskLevel(undefined)
                setCurrentViewId(null)
                handleFilterChange()
              }}
            >
              重置
            </Button>
        </Space>
      </div>

        {/* 高级筛选（可折叠） */}
        <Collapse
          activeKey={showAdvancedFilters ? ['advanced'] : []}
          onChange={(keys) => setShowAdvancedFilters(keys.length > 0)}
          style={{ marginBottom: '16px', background: 'transparent', border: 'none' }}
          items={[
            {
              key: 'advanced',
              label: (
                <Space>
                  <FilterOutlined />
                  <span>高级筛选</span>
                  {showAdvancedFilters ? <UpOutlined /> : <DownOutlined />}
                </Space>
              ),
              children: (
                <Space 
                  size={isMobile ? "small" : "middle"} 
                  wrap 
                  direction={isMobile ? "vertical" : "horizontal"}
                  style={{ width: '100%', paddingTop: '16px' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
                    <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>订单号：</span>
                    <Input
                      placeholder="订单号"
                      allowClear
                      value={orderSn}
                      onChange={(e) => {
                        setOrderSn(e.target.value)
                        handleFilterChange()
                      }}
                      onPressEnter={() => handleFilterChange()}
                      style={{ width: isMobile ? '100%' : 200 }}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
                    <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>商品名称：</span>
                    <Input
                      placeholder="商品名称"
                      allowClear
                      value={productName}
                      onChange={(e) => {
                        setProductName(e.target.value)
                        handleFilterChange()
                      }}
                      onPressEnter={() => handleFilterChange()}
                      style={{ width: isMobile ? '100%' : 200 }}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
                    <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>SKU：</span>
                    <Input
                      placeholder="SKU"
                      allowClear
                      value={productSku}
                      onChange={(e) => {
                        setProductSku(e.target.value)
                        handleFilterChange()
                      }}
                      onPressEnter={() => handleFilterChange()}
                      style={{ width: isMobile ? '100%' : 200 }}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
                    <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>延误风险：</span>
                    <Select
                      style={{ width: isMobile ? '100%' : 150 }}
                      placeholder="全部"
                      allowClear
                      value={delayRiskLevel}
                      onChange={(value) => {
                        setDelayRiskLevel(value)
                        handleFilterChange()
                      }}
                      options={[
                        { label: '正常', value: 'normal' },
                        { label: '临界', value: 'warning' },
                        { label: '延误', value: 'delayed' },
                      ]}
                    />
                  </div>
                </Space>
              ),
            },
          ]}
        />

      {/* 批量操作工具栏 */}
      {selectedRowKeys.length > 0 && (
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 10,
            background: 'var(--color-bg-container)',
            padding: '12px 16px',
            marginBottom: '16px',
            borderRadius: '8px',
            border: '1px solid var(--color-border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <Space>
            <span style={{ fontWeight: 'bold' }}>
              已选择 {selectedRowKeys.length} 个订单
            </span>
            <Button
              type="text"
              size="small"
              onClick={() => {
                setSelectedRowKeys([])
              }}
            >
              取消选择
            </Button>
          </Space>
          <Space>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'export-csv',
                    label: '导出为 CSV',
                    icon: <ExportOutlined />,
                    onClick: () => handleBatchExport('csv'),
                  },
                  {
                    key: 'export-excel',
                    label: '导出为 Excel',
                    icon: <ExportOutlined />,
                    onClick: () => handleBatchExport('excel'),
                  },
                ],
              }}
              trigger={['click']}
            >
              <Button icon={<ExportOutlined />}>导出</Button>
            </Dropdown>
            <Button
              icon={<TagOutlined />}
              onClick={() => handleBatchTags()}
            >
              标签
            </Button>
            <Button
              icon={<FileTextOutlined />}
              onClick={() => handleBatchNotes()}
            >
              备注
            </Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'mark-shipped',
                    label: '标记为已发货',
                    icon: <CheckCircleOutlined />,
                    onClick: () => handleBatchStatus('SHIPPED'),
                  },
                  {
                    key: 'mark-delivered',
                    label: '标记为已送达',
                    icon: <CheckCircleOutlined />,
                    onClick: () => handleBatchStatus('DELIVERED'),
                  },
                  { type: 'divider' },
                  {
                    key: 'mark-cancelled',
                    label: '标记为已取消',
                    icon: <CloseCircleOutlined />,
                    danger: true,
                    onClick: () => handleBatchStatus('CANCELLED'),
                  },
                ],
              }}
              trigger={['click']}
            >
              <Button>状态</Button>
            </Dropdown>
          </Space>
        </div>
      )}
      
      <div style={{ marginTop: '20px', overflowX: 'auto' }}>
        <Table
          columns={columns}
          dataSource={processedOrders}
          rowKey="id"
          loading={isLoading}
          bordered={false}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => {
              setSelectedRowKeys(keys)
            },
            getCheckboxProps: (record) => ({
              disabled: record.status === 'CANCELLED', // 已取消的订单不能选择
            }),
          }}
          scroll={{ 
            x: 'max-content',
            y: isMobile ? undefined : 'calc(100vh - 400px)',
          }}
          pagination={pagination.total > 0 ? {
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showLessItems: false,
            showTotal: (total, range) => `共 ${total} 条订单，显示 ${range[0]}-${range[1]} 条`,
            pageSizeOptions: ['20', '50', '100', '200'],
            onChange: (page, pageSize) => {
              setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: pageSize || prev.pageSize,
              }))
            },
            onShowSizeChange: (_current, size) => {
              setPagination(prev => ({
                ...prev,
                current: 1,
                pageSize: size,
              }))
            },
            style: { 
              marginTop: '16px',
              background: 'transparent'
            }
          } : false}
          style={{
            background: 'transparent',
          }}
          className="order-list-table"
        />
      </div>
      
      {/* 订单详情Drawer */}
      <OrderDetailDrawer
        visible={detailDrawerVisible}
        orderId={selectedOrderId}
        onClose={() => {
          setDetailDrawerVisible(false)
          setSelectedOrderId(null)
        }}
      />
    </div>
  )
}

export default OrderList

