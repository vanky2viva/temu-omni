import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Card, Space, Select, DatePicker, Tag } from 'antd'
import { orderApi, shopApi } from '@/services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const statusColors: Record<string, string> = {
  pending: 'default',
  paid: 'processing',
  shipped: 'warning',
  delivered: 'success',
  completed: 'success',
  cancelled: 'error',
  refunded: 'error',
}

const statusLabels: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
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
  })

  // 获取订单列表
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', shopId, dateRange],
    queryFn: () => {
      const params: any = {}
      if (shopId) params.shop_id = shopId
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      return orderApi.getOrders(params)
    },
  })

  const columns = [
    {
      title: '订单编号',
      dataIndex: 'order_sn',
      key: 'order_sn',
      width: 180,
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
    },
    {
      title: '单价',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 100,
      render: (price: number, record: any) => `${price} ${record.currency}`,
    },
    {
      title: '订单金额',
      dataIndex: 'total_price',
      key: 'total_price',
      width: 120,
      render: (price: number, record: any) => (
        <span style={{ fontWeight: 'bold' }}>
          {price} {record.currency}
        </span>
      ),
    },
    {
      title: '成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 100,
      render: (cost: number, record: any) =>
        cost ? `${cost} ${record.currency}` : '-',
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      render: (profit: number, record: any) => {
        if (!profit && profit !== 0) return '-'
        return (
          <span style={{ color: profit >= 0 ? '#52c41a' : '#ff4d4f' }}>
            {profit} {record.currency}
          </span>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      ),
    },
    {
      title: '下单时间',
      dataIndex: 'order_time',
      key: 'order_time',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
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
        scroll={{ x: 1200 }}
      />
    </div>
  )
}

export default OrderList

