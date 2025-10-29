import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Spin } from 'antd'
import {
  ShoppingOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { statisticsApi } from '@/services/api'
import dayjs from 'dayjs'

function Dashboard() {
  // 获取总览数据
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: () => statisticsApi.getOverview(),
  })

  // 获取每日趋势数据
  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['daily', 30],
    queryFn: () => statisticsApi.getDaily({ days: 30 }),
  })

  // 获取店铺对比数据
  const { data: shopComparison, isLoading: shopLoading } = useQuery({
    queryKey: ['shopComparison'],
    queryFn: () => statisticsApi.getShopComparison(),
  })

  // 趋势图配置
  const trendChartOption = {
    title: {
      text: '近30天销售趋势',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['GMV', '利润', '订单量'],
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
      boundaryGap: false,
      data: dailyData?.map((item: any) => dayjs(item.date).format('MM-DD')) || [],
    },
    yAxis: [
      {
        type: 'value',
        name: 'GMV/利润',
        position: 'left',
      },
      {
        type: 'value',
        name: '订单量',
        position: 'right',
      },
    ],
    series: [
      {
        name: 'GMV',
        type: 'line',
        smooth: true,
        data: dailyData?.map((item: any) => item.gmv) || [],
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '利润',
        type: 'line',
        smooth: true,
        data: dailyData?.map((item: any) => item.profit) || [],
        itemStyle: { color: '#52c41a' },
      },
      {
        name: '订单量',
        type: 'bar',
        yAxisIndex: 1,
        data: dailyData?.map((item: any) => item.orders) || [],
        itemStyle: { color: '#faad14' },
      },
    ],
  }

  // 店铺对比图配置
  const shopChartOption = {
    title: {
      text: '店铺业绩对比',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: ['GMV', '利润'],
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
      data: shopComparison?.map((item: any) => item.shop_name) || [],
      axisLabel: {
        interval: 0,
        rotate: 30,
      },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: 'GMV',
        type: 'bar',
        data: shopComparison?.map((item: any) => item.gmv) || [],
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '利润',
        type: 'bar',
        data: shopComparison?.map((item: any) => item.profit) || [],
        itemStyle: { color: '#52c41a' },
      },
    ],
  }

  if (overviewLoading) {
    return <Spin size="large" />
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据总览</h2>
      
      {/* 核心指标卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总订单量"
              value={overview?.total_orders || 0}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总GMV"
              value={overview?.total_gmv || 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总利润"
              value={overview?.total_profit || 0}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="USD"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="利润率"
              value={overview?.profit_margin || 0}
              precision={2}
              suffix="%"
              prefix={
                (overview?.profit_margin || 0) >= 0 ? (
                  <RiseOutlined />
                ) : (
                  <FallOutlined />
                )
              }
              valueStyle={{
                color: (overview?.profit_margin || 0) >= 0 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={16}>
        <Col span={24}>
          <Card loading={dailyLoading}>
            <ReactECharts option={trendChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      {/* 店铺对比图表 */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card loading={shopLoading}>
            <ReactECharts option={shopChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

