import React, { useState, useEffect, useCallback } from 'react'
import { Modal, Input, message, Space } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import UnifiedTable from '@/components/Table'
import OrderDetailDrawer from '@/components/OrderDetailDrawer'
import { userViewsApi, orderApi } from '@/services/api'
import { useOrderList } from './hooks/useOrderList'
import { createOrderTableColumns } from './components/OrderTableColumns'
import OrderStats from './components/OrderStats'
import OrderFilters from './components/OrderFilters'
import BatchActions from './components/BatchActions'
import type { OrderListView } from './types'
import './styles/index.css'

const OrderList: React.FC = () => {
  const {
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
  } = useOrderList()

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [saveViewModalVisible, setSaveViewModalVisible] = useState(false)
  const [viewName, setViewName] = useState('')
  const [viewDescription, setViewDescription] = useState('')
  const [isDefaultView, setIsDefaultView] = useState(false)
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false)
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null)

  // 获取用户视图列表
  const { data: userViews } = useQuery({
    queryKey: ['user-views', 'order_list'],
    queryFn: async () => {
      const result = await userViewsApi.getViews('order_list')
      return result || []
    },
    staleTime: 5 * 60 * 1000,
  })

  // 保存视图 Mutation
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
  })

  // 删除视图 Mutation
  const deleteViewMutation = useMutation({
    mutationFn: async (viewId: number) => {
      return await userViewsApi.deleteView(viewId)
    },
    onSuccess: (_, viewId) => {
      queryClient.invalidateQueries({ queryKey: ['user-views'] })
      if (currentViewId === viewId) setCurrentViewId(null)
      message.success('视图已删除')
    },
  })

  // 加载视图
  const handleLoadView = (view: OrderListView) => {
    if (view.filters) {
      setFilters(prev => ({
        ...prev,
        ...view.filters,
        shopIds: (view.filters as any).shop_ids || [],
        shopId: (view.filters as any).shop_id,
        statusFilters: (view.filters as any).status_filters || [],
        statusFilter: (view.filters as any).status_filter,
      }))
    }
    setCurrentViewId(view.id)
    message.success(`已加载视图: ${view.name}`)
  }

  // 复制到剪贴板
  const copyToClipboard = useCallback((text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    })
  }, [])

  // 批量操作
  const handleBatchStatus = (status: string) => {
    const statusLabels: Record<string, string> = {
      SHIPPED: '已发货',
      DELIVERED: '已送达',
      CANCELLED: '已取消',
    }
    Modal.confirm({
      title: '批量修改状态',
      content: `确定要将 ${selectedRowKeys.length} 个订单标记为${statusLabels[status]}吗？`,
      onOk: () => {
        message.success(`已将 ${selectedRowKeys.length} 个订单标记为${statusLabels[status]}`)
        setSelectedRowKeys([])
        queryClient.invalidateQueries({ queryKey: ['orders'] })
      },
    })
  }

  const columns = createOrderTableColumns({
    onCopy: copyToClipboard,
    onRowClick: (id) => {
      setSelectedOrderId(id)
      setDetailDrawerVisible(true)
    },
  })

  return (
    <div className="order-list-container">
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: isMobile ? '24px' : '32px', marginBottom: '8px' }}>订单列表</h1>
        <p style={{ opacity: 0.7 }}>实时监控订单状态，高效管理运营数据</p>
      </div>

      <OrderStats statusStats={statusStats} isLoadingStats={isLoadingStats} isMobile={isMobile} />

      <div className="order-filters-container">
        <OrderFilters
          filters={filters}
          setFilters={setFilters}
          isMobile={isMobile}
          shops={shops}
          userViews={userViews as OrderListView[]}
          currentViewId={currentViewId}
          showAdvancedFilters={showAdvancedFilters}
          setShowAdvancedFilters={setShowAdvancedFilters}
          onSaveView={() => setSaveViewModalVisible(true)}
          onLoadView={handleLoadView}
          onDeleteView={(id) => deleteViewMutation.mutate(id)}
          onFilterChange={handleFilterChange}
          onReset={() => {
            setFilters({
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
            setCurrentViewId(null)
            handleFilterChange()
          }}
        />
      </div>

      <BatchActions
        selectedCount={selectedRowKeys.length}
        onCancel={() => setSelectedRowKeys([])}
        onExport={(format) => message.info(`导出为 ${format}`)}
        onTags={() => message.info('批量修改标签')}
        onNotes={() => message.info('批量添加备注')}
        onStatus={handleBatchStatus}
      />

      <div className="order-table-card">
        <div className="order-table-header">
          <span className="order-table-title">订单列表</span>
          {pagination.total > 0 && (
            <span className="order-table-pagination-info">
              共 {pagination.total.toLocaleString()} 条订单
            </span>
          )}
        </div>
        <UnifiedTable
          variant="order-list"
          columns={columns}
          dataSource={processedOrders}
          rowKey="id"
          loading={isLoading}
          isMobile={isMobile}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
            getCheckboxProps: (record) => ({
              disabled: record.status === 'CANCELLED',
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
            onChange: (page, pageSize) => setPagination(prev => ({ ...prev, current: page, pageSize: pageSize || prev.pageSize })),
          } : false}
        />
      </div>

      <OrderDetailDrawer
        visible={detailDrawerVisible}
        orderId={selectedOrderId}
        onClose={() => {
          setDetailDrawerVisible(false)
          setSelectedOrderId(null)
        }}
      />

      <Modal
        title={currentViewId ? '更新视图' : '保存视图'}
        open={saveViewModalVisible}
        onOk={() => saveViewMutation.mutate({ name: viewName, filters, is_default: isDefaultView })}
        onCancel={() => setSaveViewModalVisible(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="视图名称" value={viewName} onChange={(e) => setViewName(e.target.value)} />
          <Input.TextArea placeholder="视图描述" value={viewDescription} onChange={(e) => setViewDescription(e.target.value)} rows={3} />
        </Space>
      </Modal>
    </div>
  )
}

export default OrderList
