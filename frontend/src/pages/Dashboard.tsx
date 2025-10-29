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
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#667eea',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: {
          color: '#667eea',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#667eea',
      borderWidth: 2,
      textStyle: {
        color: '#333',
      },
    },
    legend: {
      data: ['GMV', '利润', '订单量'],
      bottom: 0,
      textStyle: {
        fontSize: 13,
        fontWeight: 'bold',
      },
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
      axisLine: {
        lineStyle: {
          color: '#667eea',
        },
      },
    },
    yAxis: [
      {
        type: 'value',
        name: 'GMV/利润',
        position: 'left',
        axisLine: {
          lineStyle: {
            color: '#667eea',
          },
        },
      },
      {
        type: 'value',
        name: '订单量',
        position: 'right',
        axisLine: {
          lineStyle: {
            color: '#f093fb',
          },
        },
      },
    ],
    series: [
      {
        name: 'GMV',
        type: 'line',
        smooth: true,
        data: dailyData?.map((item: any) => item.gmv) || [],
        itemStyle: { 
          color: '#667eea',
        },
        lineStyle: {
          width: 3,
          shadowColor: 'rgba(102, 126, 234, 0.5)',
          shadowBlur: 10,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0.05)' },
            ],
          },
        },
      },
      {
        name: '利润',
        type: 'line',
        smooth: true,
        data: dailyData?.map((item: any) => item.profit) || [],
        itemStyle: { 
          color: '#52c41a',
        },
        lineStyle: {
          width: 3,
          shadowColor: 'rgba(82, 196, 26, 0.5)',
          shadowBlur: 10,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
              { offset: 1, color: 'rgba(82, 196, 26, 0.05)' },
            ],
          },
        },
      },
      {
        name: '订单量',
        type: 'bar',
        yAxisIndex: 1,
        data: dailyData?.map((item: any) => item.orders) || [],
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#f093fb' },
              { offset: 1, color: '#f5d0fe' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
          shadowColor: 'rgba(240, 147, 251, 0.5)',
          shadowBlur: 10,
        },
      },
    ],
  }

  // 店铺对比图配置
  const shopChartOption = {
    title: {
      text: '店铺业绩对比',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#667eea',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(102, 126, 234, 0.1)',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#667eea',
      borderWidth: 2,
      textStyle: {
        color: '#333',
      },
    },
    legend: {
      data: ['GMV', '利润'],
      bottom: 0,
      textStyle: {
        fontSize: 13,
        fontWeight: 'bold',
      },
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
        color: '#667eea',
        fontWeight: 'bold',
      },
      axisLine: {
        lineStyle: {
          color: '#667eea',
        },
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#667eea',
        },
      },
    },
    series: [
      {
        name: 'GMV',
        type: 'bar',
        data: shopComparison?.map((item: any) => item.gmv) || [],
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' },
            ],
          },
          borderRadius: [8, 8, 0, 0],
          shadowColor: 'rgba(102, 126, 234, 0.5)',
          shadowBlur: 10,
        },
        barWidth: '30%',
      },
      {
        name: '利润',
        type: 'bar',
        data: shopComparison?.map((item: any) => item.profit) || [],
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#f093fb' },
              { offset: 1, color: '#f5d0fe' },
            ],
          },
          borderRadius: [8, 8, 0, 0],
          shadowColor: 'rgba(240, 147, 251, 0.5)',
          shadowBlur: 10,
        },
        barWidth: '30%',
      },
    ],
  }

  if (overviewLoading) {
    return <Spin size="large" />
  }

  return (
    <div>
      <h2 style={{ 
        marginBottom: 32, 
        fontSize: '28px',
        fontWeight: 'bold',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }}>
        📊 数据总览
      </h2>
      
      {/* 核心指标卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
        <Col span={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="总订单量"
              value={overview?.total_orders || 0}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card" bordered={false}>
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
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="总利润"
              value={overview?.total_profit || 0}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card" bordered={false}>
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
            />
          </Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card className="chart-card" loading={dailyLoading} bordered={false}>
            <ReactECharts option={trendChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      {/* 店铺对比图表 */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card className="chart-card" loading={shopLoading} bordered={false}>
            <ReactECharts option={shopChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

