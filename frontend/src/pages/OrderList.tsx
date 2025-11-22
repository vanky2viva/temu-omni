import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Space, Select, DatePicker, Tag, Tooltip, Button, message, Card, Row, Col, Statistic, Input } from 'antd'
import { CopyOutlined, SearchOutlined } from '@ant-design/icons'
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
  const [isMobile, setIsMobile] = useState(false)
  const [shopId, setShopId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [orderSn, setOrderSn] = useState<string>('')
  const [productName, setProductName] = useState<string>('')
  const [productSku, setProductSku] = useState<string>('')
  
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
  const { data: statusStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['order-status-statistics', shopId, dateRange],
    queryFn: async () => {
      const params: any = {}
      if (shopId) params.shop_id = shopId
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      return await orderApi.getStatusStatistics(params)
    },
    staleTime: 30000, // 30秒缓存
  })

  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })

  // 获取订单列表（使用分页）
  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['orders', shopId, dateRange, statusFilter, searchKeyword, orderSn, productName, productSku, pagination.current, pagination.pageSize],
    queryFn: async () => {
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
      if (searchKeyword) params.search = searchKeyword
      if (orderSn) params.order_sn = orderSn
      if (productName) params.product_name = productName
      if (productSku) params.product_sku = productSku
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
        {/* 统计卡片 */}
        {statusStats && (
          <Row gutter={[8, 8]}>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="总订单数"
                    value={statusStats.total_orders || 0}
                    valueStyle={{ fontSize: isMobile ? '18px' : '22px', lineHeight: '1.2' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="未发货"
                    value={statusStats.processing || 0}
                    valueStyle={{ fontSize: isMobile ? '18px' : '22px', color: '#faad14', lineHeight: '1.2' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="已发货"
                    value={statusStats.shipped || 0}
                    valueStyle={{ fontSize: isMobile ? '18px' : '22px', color: '#1890ff', lineHeight: '1.2' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="已送达"
                    value={statusStats.delivered || 0}
                    valueStyle={{ fontSize: isMobile ? '18px' : '22px', color: '#52c41a', lineHeight: '1.2' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="延误订单"
                    value={statusStats.delayed_orders || 0}
                    valueStyle={{ fontSize: isMobile ? '18px' : '22px', color: '#ff4d4f', lineHeight: '1.2' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={8} lg={4}>
                <Card 
                  size="small" 
                  loading={isLoadingStats}
                  style={{ height: '100%', minHeight: isMobile ? '80px' : '100px' }}
                  bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
                >
                  <Statistic
                    title="延误率"
                    value={statusStats.delay_rate || 0}
                    precision={2}
                    suffix="%"
                    valueStyle={{ 
                      fontSize: isMobile ? '18px' : '22px', 
                      color: statusStats.delay_rate > 10 ? '#ff4d4f' : '#52c41a',
                      lineHeight: '1.2',
                      whiteSpace: 'nowrap'
                    }}
                  />
                </Card>
              </Col>
            </Row>
        )}
      </div>
      
        {/* 模糊搜索 */}
        <div style={{ marginBottom: '16px' }}>
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
              width: isMobile ? '100%' : '400px',
              maxWidth: '100%'
            }}
          />
        </div>

        {/* 详细筛选条件 */}
        <Space 
          size={isMobile ? "small" : "middle"} 
          wrap 
          direction={isMobile ? "vertical" : "horizontal"}
          style={{ width: '100%' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>店铺：</span>
            <Select
              style={{ width: isMobile ? '100%' : 200 }}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>状态：</span>
            <Select
              style={{ width: isMobile ? '100%' : 140 }}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
            <span style={{ color: 'var(--color-fg)', opacity: 0.7, fontSize: '14px', minWidth: isMobile ? '60px' : 'auto' }}>日期：</span>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                setDateRange(dates as any)
                handleFilterChange()
              }}
              format="YYYY-MM-DD"
              style={{ width: isMobile ? '100%' : 240 }}
            />
          </div>
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
        </Space>
      
      <div style={{ marginTop: '20px', overflowX: 'auto' }}>
        <Table
          columns={columns}
          dataSource={processedOrders}
          rowKey="id"
          loading={isLoading}
          bordered={false}
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
            onShowSizeChange: (current, size) => {
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
    </div>
  )
}

export default OrderList

