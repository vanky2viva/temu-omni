import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Table, Space, Select, DatePicker, Row, Col } from 'antd'
import ReactECharts from 'echarts-for-react'
import { shopApi } from '@/services/api'
import axios from 'axios'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

function SkuAnalysis() {
  const [selectedShops, setSelectedShops] = useState<number[]>([])
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])
  const [limit, setLimit] = useState(20)

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取SKU销量数据
  const { data: skuData, isLoading } = useQuery({
    queryKey: ['sku-sales', selectedShops, dateRange, limit],
    queryFn: async () => {
      const params: any = { limit }
      if (selectedShops.length > 0) {
        params.shop_ids = selectedShops
      }
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      const response = await axios.get('/api/analytics/sku-sales', { params })
      return response.data
    },
  })

  // 销量柱状图配置
  const quantityChartOption = {
    title: {
      text: 'SKU销量排行',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>销量: ${data.value} 件`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: skuData?.map((item: any) => item.sku) || [],
      axisLabel: {
        interval: 0,
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: '销量（件）',
    },
    series: [
      {
        name: '销量',
        type: 'bar',
        data: skuData?.map((item: any) => item.quantity) || [],
        itemStyle: {
          color: '#5470c6',
        },
      },
    ],
  }

  // GMV柱状图配置
  const gmvChartOption = {
    title: {
      text: 'SKU GMV排行',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>GMV: $${data.value.toFixed(2)}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: skuData?.map((item: any) => item.sku) || [],
      axisLabel: {
        interval: 0,
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: 'GMV (CNY)',
    },
    series: [
      {
        name: 'GMV',
        type: 'bar',
        data: skuData?.map((item: any) => item.gmv) || [],
        itemStyle: {
          color: '#91cc75',
        },
      },
    ],
  }

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '店铺',
      dataIndex: 'shop',
      key: 'shop',
      width: 120,
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.quantity - b.quantity,
      render: (val: number) => `${val} 件`,
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 100,
      align: 'right' as const,
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.gmv - b.gmv,
      render: (val: number) => `$${val.toFixed(2)}`,
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.profit - b.profit,
      render: (val: number) => (
        <span style={{ color: val >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          ${val.toFixed(2)}
        </span>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>SKU销量分析</h2>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle" wrap>
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

          <span>日期范围：</span>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as any)}
            format="YYYY-MM-DD"
          />

          <span>显示数量：</span>
          <Select
            value={limit}
            onChange={setLimit}
            style={{ width: 100 }}
            options={[
              { label: 'Top 10', value: 10 },
              { label: 'Top 20', value: 20 },
              { label: 'Top 50', value: 50 },
              { label: 'Top 100', value: 100 },
            ]}
          />
        </Space>
      </Card>

      {/* 图表 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card loading={isLoading}>
            <ReactECharts option={quantityChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card loading={isLoading}>
            <ReactECharts option={gmvChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      {/* 表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={skuData}
          rowKey="sku"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个SKU`,
          }}
        />
      </Card>
    </div>
  )
}

export default SkuAnalysis

