import { useState } from 'react'
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

  const columns = [
    {
      title: '订单编号',
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
      title: '收货国家',
      dataIndex: 'shipping_country',
      key: 'shipping_country',
      width: 100,
      render: (country: string) => country || '-',
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
      title: '支付时间',
      dataIndex: 'payment_time',
      key: 'payment_time',
      width: 180,
      render: (time: string) => 
        time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '发货时间',
      dataIndex: 'shipping_time',
      key: 'shipping_time',
      width: 180,
      render: (time: string) => 
        time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
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
        dataSource={orders}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1800 }}
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

