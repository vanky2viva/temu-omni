import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Select, Tabs } from 'antd'
import ReactECharts from 'echarts-for-react'
import { statisticsApi, shopApi } from '@/services/api'

function Statistics() {
  const [selectedShops, setSelectedShops] = useState<number[]>([])
  const [activeTab, setActiveTab] = useState('daily')

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取每日统计
  const { data: dailyData } = useQuery({
    queryKey: ['daily', selectedShops, 30],
    queryFn: () =>
      statisticsApi.getDaily({
        shop_ids: selectedShops.length > 0 ? selectedShops : undefined,
        days: 30,
      }),
  })

  // 获取每周统计
  const { data: weeklyData } = useQuery({
    queryKey: ['weekly', selectedShops, 12],
    queryFn: () =>
      statisticsApi.getWeekly({
        shop_ids: selectedShops.length > 0 ? selectedShops : undefined,
        weeks: 12,
      }),
  })

  // 获取每月统计
  const { data: monthlyData } = useQuery({
    queryKey: ['monthly', selectedShops, 12],
    queryFn: () =>
      statisticsApi.getMonthly({
        shop_ids: selectedShops.length > 0 ? selectedShops : undefined,
        months: 12,
      }),
  })

  // 获取销量趋势
  const { data: trendData } = useQuery({
    queryKey: ['trend', selectedShops, 30],
    queryFn: () =>
      statisticsApi.getTrend({
        shop_ids: selectedShops.length > 0 ? selectedShops : undefined,
        days: 30,
      }),
  })

  const getChartData = () => {
    switch (activeTab) {
      case 'daily':
        return dailyData || []
      case 'weekly':
        return weeklyData || []
      case 'monthly':
        return monthlyData || []
      default:
        return []
    }
  }

  const getXAxisData = () => {
    const data = getChartData()
    switch (activeTab) {
      case 'daily':
        return data.map((item: any) => item.date)
      case 'weekly':
        return data.map((item: any) => item.period)
      case 'monthly':
        return data.map((item: any) => item.period)
      default:
        return []
    }
  }

  // GMV和利润图表
  const gmvProfitChartOption = {
    title: {
      text: 'GMV与利润趋势',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['GMV', '成本', '利润'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: getXAxisData(),
      axisLabel: {
        interval: 0,
        rotate: activeTab === 'daily' ? 45 : 0,
      },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: 'GMV',
        type: 'bar',
        data: getChartData().map((item: any) => item.gmv),
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '成本',
        type: 'bar',
        data: getChartData().map((item: any) => item.cost),
        itemStyle: { color: '#ff7875' },
      },
      {
        name: '利润',
        type: 'line',
        data: getChartData().map((item: any) => item.profit),
        itemStyle: { color: '#52c41a' },
      },
    ],
  }

  // 订单量趋势图
  const orderTrendChartOption = {
    title: {
      text: '订单量趋势',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['订单量', '7日移动平均'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: trendData?.trend?.map((item: any) => item.date) || [],
      axisLabel: {
        interval: 0,
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '订单量',
        type: 'bar',
        data: trendData?.trend?.map((item: any) => item.orders) || [],
        itemStyle: { color: '#faad14' },
      },
      {
        name: '7日移动平均',
        type: 'line',
        smooth: true,
        data: trendData?.trend?.map((item: any) => item.gmv_ma7 / 100) || [],
        itemStyle: { color: '#722ed1' },
      },
    ],
  }

  const tabItems = [
    { key: 'daily', label: '每日统计' },
    { key: 'weekly', label: '每周统计' },
    { key: 'monthly', label: '每月统计' },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据统计</h2>

      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span>店铺筛选：</span>
          <Select
            mode="multiple"
            style={{ flex: 1, maxWidth: 500 }}
            placeholder="全部店铺"
            allowClear
            onChange={setSelectedShops}
            options={shops?.map((shop: any) => ({
              label: shop.shop_name,
              value: shop.id,
            }))}
          />
        </div>
      </Card>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      <Row gutter={16}>
        <Col span={24}>
          <Card>
            <ReactECharts option={gmvProfitChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card>
            <ReactECharts option={orderTrendChartOption} style={{ height: 400 }} />
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <span style={{ fontSize: 16 }}>
                增长率：
                <span
                  style={{
                    fontSize: 20,
                    fontWeight: 'bold',
                    color: (trendData?.growth_rate || 0) >= 0 ? '#52c41a' : '#ff4d4f',
                  }}
                >
                  {trendData?.growth_rate || 0}%
                </span>
              </span>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Statistics

