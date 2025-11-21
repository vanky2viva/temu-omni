import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Space, Select, DatePicker, Tag, Tooltip } from 'antd'
import { orderApi, shopApi } from '@/services/api'
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
  const [shopId, setShopId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  
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

  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  })

  // 获取订单列表（使用分页）
  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['orders', shopId, dateRange, statusFilter, pagination.current, pagination.pageSize],
    queryFn: () => {
      const params: any = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      }
      if (shopId) params.shop_id = shopId
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      if (statusFilter) params.status_filter = statusFilter
      return orderApi.getOrders(params)
    },
    staleTime: 30000, // 30秒缓存
    onSuccess: (data) => {
      // 更新分页总数
      if (data && typeof data === 'object' && 'total' in data) {
        setPagination(prev => ({ ...prev, total: data.total as number }))
      } else if (Array.isArray(data)) {
        // 兼容旧的数据结构（直接返回数组）
        setPagination(prev => ({ ...prev, total: data.length }))
      }
    },
  })

  // 兼容新旧数据结构
  const orders = Array.isArray(ordersData) 
    ? ordersData  // 旧格式：直接返回数组
    : (ordersData?.items || [])  // 新格式：分页响应对象

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

  const columns = [
    {
      title: '父订单号',
      dataIndex: 'parent_order_sn',
      key: 'parent_order_sn',
      width: 220,
      fixed: 'left' as const,
      render: (parentSn: string, record: any) => {
        if (!record._hasParent) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: { rowSpan: 1 },
          }
        }
        
        if (record._isFirstInGroup && record._groupSize > 1) {
          return {
            children: (
              <div style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                {parentSn}
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
            <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>{parentSn}</div>
          ),
          props: { rowSpan: 1 },
        }
      },
    },
    {
      title: '子订单号',
      dataIndex: 'order_sn',
      key: 'order_sn',
      width: 220,
      fixed: 'left' as const,
      render: (sn: string) => (
        <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>{sn}</div>
      ),
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
    <div style={{ 
      background: 'var(--color-bg)',
      borderRadius: '8px',
      border: '1px solid var(--border-color, #e1e4e8)',
      overflow: 'hidden'
    }}>
      <div style={{ 
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-color, #e1e4e8)',
        background: 'var(--color-bg)'
      }}>
        <h2 style={{ 
          margin: 0,
          marginBottom: '16px',
          fontSize: '20px',
          fontWeight: 600,
          color: 'var(--color-fg)'
        }}>
          订单管理
        </h2>
        <Space size="middle" wrap>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px' }}>店铺：</span>
            <Select
              style={{ width: 200 }}
              placeholder="全部店铺"
              allowClear
              value={shopId}
              onChange={(value) => {
                setShopId(value)
                handleFilterChange()
              }}
              options={Array.isArray(shops) ? shops.map((shop: any) => ({
                label: shop.shop_name,
                value: shop.id,
              })) : []}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px' }}>状态：</span>
            <Select
              style={{ width: 140 }}
              placeholder="全部状态"
              allowClear
              value={statusFilter}
              onChange={(value) => {
                setStatusFilter(value)
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px' }}>日期：</span>
            <RangePicker
              onChange={(dates) => {
                setDateRange(dates as any)
                handleFilterChange()
              }}
              format="YYYY-MM-DD"
              style={{ width: 240 }}
            />
          </div>
        </Space>
      </div>

      <div style={{ padding: '0' }}>
        <Table
          columns={columns}
          dataSource={processedOrders}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: 2000 }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条订单`,
            pageSizeOptions: ['20', '50', '100', '200'],
            onChange: (page, pageSize) => {
              setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: pageSize || prev.pageSize,
              }))
            },
            onShowSizeChange: (current, size) => {
              setPagination(prev => ({
                ...prev,
                current: 1,
                pageSize: size,
              }))
            },
            style: { 
              padding: '16px 24px',
              background: 'var(--color-bg)',
              borderTop: '1px solid var(--border-color, #e1e4e8)'
            }
          }}
          style={{
            background: 'var(--color-bg)',
          }}
          className="order-list-table"
        />
      </div>
    </div>
  )
}

export default OrderList

