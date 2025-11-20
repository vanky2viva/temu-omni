import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Card, Space, Select, DatePicker, Tag } from 'antd'
import { orderApi, shopApi } from '@/services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const statusColors: Record<string, string> = {
  pending: 'default',
  paid: 'processing',
  processing: 'blue',
  shipped: 'warning',
  delivered: 'success',
  completed: 'success',
  cancelled: 'error',
  refunded: 'error',
}

const statusLabels: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
  processing: '处理中',
  shipped: '已发货',
  delivered: '已送达',
  completed: '已完成',
  cancelled: '已取消',
  refunded: '已退款',
}

function OrderList() {
  const [shopId, setShopId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
    cacheTime: 0,
  })

  // 获取订单列表
  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders', shopId, dateRange],
    queryFn: () => {
      const params: any = {
        skip: 0,
        limit: 10000, // 增加limit以获取更多订单
      }
      if (shopId) params.shop_id = shopId
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      return orderApi.getOrders(params)
    },
    staleTime: 0,
  })

  // 调试：打印订单数据
  if (error) {
    console.error('获取订单列表错误:', error)
  }
  if (orders) {
    console.log('订单列表数据:', orders?.length || 0, '条')
  }

  // 处理订单数据，按父订单号分组，用于合并显示
  const processedOrders = useMemo(() => {
    if (!orders) return []
    
    // 按父订单号分组（如果父订单号存在，使用父订单号；否则每个订单单独一组）
    const groupedByParent: Record<string, any[]> = {}
    orders.forEach((order: any) => {
      // 如果有父订单号，使用父订单号作为分组键；否则使用子订单号（单独一组）
      const parentKey = order.parent_order_sn || `single_${order.order_sn}`
      if (!groupedByParent[parentKey]) {
        groupedByParent[parentKey] = []
      }
      groupedByParent[parentKey].push(order)
    })
    
    // 展平数据，添加合并信息和计算最晚发货时间
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
      
      // 获取该组的签收时间（通常同一父订单的签收时间相同，取第一个非空的）
      const deliveryTime = group.find((o: any) => o.delivery_time)?.delivery_time || null
      
      group.forEach((order, index) => {
        result.push({
          ...order,
          _isFirstInGroup: index === 0,
          _groupSize: group.length,
          _parentKey: parentKey,
          _hasParent: !!order.parent_order_sn, // 标记是否有父订单号
          _latestShippingTime: latestShippingTime, // 该组最晚发货时间
          _groupDeliveryTime: deliveryTime, // 该组的签收时间（用于合并显示）
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
        // 如果没有父订单号，显示"-"
        if (!record._hasParent) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: 1,
            },
          }
        }
        
        // 只在第一行显示父订单号，其他行合并
        if (record._isFirstInGroup && record._groupSize > 1) {
          return {
            children: (
              <div style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                {parentSn}
              </div>
            ),
            props: {
              rowSpan: record._groupSize,
            },
          }
        } else if (record._groupSize > 1) {
          return {
            children: null,
            props: {
              rowSpan: 0,
            },
          }
        }
        // 单个订单，直接显示
        return {
          children: (
            <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>{parentSn}</div>
          ),
          props: {
            rowSpan: 1,
          },
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
    },
    {
      title: 'SKU',
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
      render: (price: number | null | undefined, record: any) => {
        if (price === null || price === undefined || price === 0) return '-'
        // 统一显示为人民币，使用￥符号
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
        const statusKey = status?.toLowerCase() || 'pending'
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
        // 如果有父订单且多个子订单，显示最晚发货时间并合并
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
          // 多个子订单，只在第一行显示最晚发货时间
          if (record._isFirstInGroup) {
            return {
              children: (
                <div style={{ fontSize: '12px' }}>
                  {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              ),
              props: {
                rowSpan: record._groupSize,
              },
            }
          } else {
            return {
              children: null,
              props: {
                rowSpan: 0,
              },
            }
          }
        }
        
        // 单个订单，直接显示
        return {
          children: (
            <div style={{ fontSize: '12px' }}>
              {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          ),
          props: {
            rowSpan: 1,
          },
        }
      },
    },
    {
      title: '签收时间',
      dataIndex: 'delivery_time',
      key: 'delivery_time',
      width: 180,
      render: (time: string, record: any) => {
        // 如果有父订单且多个子订单，使用组的签收时间；否则使用当前订单的签收时间
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
        
        // 如果有父订单且多个子订单，签收时间合并显示
        if (record._groupSize > 1 && record._hasParent) {
          if (record._isFirstInGroup) {
            return {
              children: (
                <div style={{ fontSize: '12px' }}>
                  {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              ),
              props: {
                rowSpan: record._groupSize,
              },
            }
          } else {
            return {
              children: null,
              props: {
                rowSpan: 0,
              },
            }
          }
        }
        
        // 单个订单，直接显示
        return {
          children: (
            <div style={{ fontSize: '12px' }}>
              {dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          ),
          props: {
            rowSpan: 1,
          },
        }
      },
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>订单管理</h2>

      <Card style={{ marginBottom: 16 }}>
        <Space size="middle">
          <span>店铺筛选：</span>
          <Select
            style={{ width: 200 }}
            placeholder="全部店铺"
            allowClear
            onChange={setShopId}
            options={shops?.map((shop: any) => ({
              label: shop.shop_name,
              value: shop.id,
            }))}
          />
          <span>日期范围：</span>
          <RangePicker
            onChange={(dates) => setDateRange(dates as any)}
            format="YYYY-MM-DD"
          />
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={processedOrders}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 2000 }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条订单`,
          defaultPageSize: 20,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
      />
    </div>
  )
}

export default OrderList

