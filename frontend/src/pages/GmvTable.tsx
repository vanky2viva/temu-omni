import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Card, Select, Space, DatePicker, Statistic, Row, Col } from 'antd'
import { DollarOutlined, RiseOutlined, ShoppingOutlined } from '@ant-design/icons'
import { statisticsApi, shopApi } from '@/services/api'
import axios from 'axios'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

function GmvTable() {
  const [isMobile, setIsMobile] = useState(false)

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  const [periodType, setPeriodType] = useState('month')
  const [periods, setPeriods] = useState(12)
  const [selectedShops, setSelectedShops] = useState<number[]>([])

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取GMV表格数据
  const { data: gmvData, isLoading } = useQuery({
    queryKey: ['gmv-table', periodType, periods, selectedShops],
    queryFn: async () => {
      const params: any = {
        period_type: periodType,
        periods: periods,
      }
      if (selectedShops.length > 0) {
        params.shop_ids = selectedShops
      }
      const response = await axios.get('/api/analytics/gmv-table', { params })
      return response.data
    },
  })

  // 计算总计
  const summary = gmvData?.data?.reduce(
    (acc: any, item: any) => ({
      orders: acc.orders + item.orders,
      gmv: acc.gmv + item.gmv,
      cost: acc.cost + item.cost,
      profit: acc.profit + item.profit,
    }),
    { orders: 0, gmv: 0, cost: 0, profit: 0 }
  )

  const columns = [
    {
      title: '周期',
      dataIndex: 'period',
      key: 'period',
      fixed: 'left' as const,
      width: 120,
    },
    {
      title: '店铺',
      dataIndex: 'shop',
      key: 'shop',
      width: 150,
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 100,
      align: 'right' as const,
    },
    {
      title: 'GMV (CNY)',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 130,
      align: 'right' as const,
      render: (val: number) => `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      sorter: (a: any, b: any) => a.gmv - b.gmv,
    },
    {
      title: '成本 (CNY)',
      dataIndex: 'cost',
      key: 'cost',
      width: 130,
      align: 'right' as const,
      render: (val: number) => `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: '利润 (CNY)',
      dataIndex: 'profit',
      key: 'profit',
      width: 130,
      align: 'right' as const,
      render: (val: number) => (
        <span style={{ color: val >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          ¥{val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
      sorter: (a: any, b: any) => a.profit - b.profit,
    },
    {
      title: '利润率',
      dataIndex: 'profit_margin',
      key: 'profit_margin',
      width: 100,
      align: 'right' as const,
      render: (val: number) => (
        <span style={{ color: val >= 20 ? '#52c41a' : val >= 10 ? '#faad14' : '#ff4d4f' }}>
          {val.toFixed(2)}%
        </span>
      ),
      sorter: (a: any, b: any) => a.profit_margin - b.profit_margin,
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: isMobile ? '18px' : '24px' }}>GMV数据表格</h2>

      {/* 汇总卡片 */}
      {summary && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="总订单量"
                value={summary.orders}
                prefix={<ShoppingOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="总GMV"
                value={summary.gmv}
                precision={2}
                prefix={<DollarOutlined />}
                suffix="CNY"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="总利润"
                value={summary.profit}
                precision={2}
                prefix={<RiseOutlined />}
                suffix="CNY"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="平均利润率"
                value={summary.gmv > 0 ? (summary.profit / summary.gmv * 100) : 0}
                precision={2}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size={isMobile ? "small" : "middle"} wrap direction={isMobile ? "vertical" : "horizontal"}>
          <span>周期类型：</span>
          <Select
            value={periodType}
            onChange={setPeriodType}
            style={{ width: 120 }}
            options={[
              { label: '按日', value: 'day' },
              { label: '按周', value: 'week' },
              { label: '按月', value: 'month' },
            ]}
          />
          
          <span>周期数量：</span>
          <Select
            value={periods}
            onChange={setPeriods}
            style={{ width: 120 }}
            options={[
              { label: '最近7天', value: 7 },
              { label: '最近15天', value: 15 },
              { label: '最近30天', value: 30 },
              { label: '最近60天', value: 60 },
              { label: '最近90天', value: 90 },
            ].filter((_, index) => periodType === 'day' ? index < 5 : true).concat(
              periodType === 'week' ? [
                { label: '最近12周', value: 12 },
                { label: '最近24周', value: 24 },
              ] : periodType === 'month' ? [
                { label: '最近6月', value: 6 },
                { label: '最近12月', value: 12 },
                { label: '最近24月', value: 24 },
              ] : []
            )}
          />

          <span>店铺筛选：</span>
          <Select
            mode="multiple"
            style={{ minWidth: 200 }}
            placeholder="全部店铺"
            allowClear
            value={selectedShops}
            onChange={setSelectedShops}
            options={shops?.map((shop: any) => ({
              label: shop.shop_name,
              value: shop.id,
            }))}
          />
        </Space>
      </Card>

      {/* GMV表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={gmvData?.data}
          rowKey={(record) => `${record.period}-${record.shop}`}
          loading={isLoading}
          scroll={{ x: 900 }}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </div>
  )
}

export default GmvTable

