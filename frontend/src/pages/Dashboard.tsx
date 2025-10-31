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
import axios from 'axios'

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

  // 获取销量总览数据
  const { data: salesOverview, isLoading: salesLoading } = useQuery({
    queryKey: ['sales-overview', 30],
    queryFn: async () => {
      const response = await axios.get('/api/analytics/sales-overview', { params: { days: 30 } })
      return response.data
    },
  })

  // 趋势图配置 - 每日订单量柱状图和总订单量曲线图
  const trendChartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '近30天销售趋势',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#c9d1d9',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: {
          color: '#58a6ff',
        },
      },
      backgroundColor: '#161b22',
      borderColor: '#30363d',
      borderWidth: 1,
      textStyle: {
        color: '#c9d1d9',
        fontSize: 12,
      },
    },
    legend: {
      data: ['每日订单量', '总订单量'],
      bottom: 0,
      textStyle: {
        fontSize: 12,
        color: '#8b949e',
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
      data: dailyData?.map((item: any) => dayjs(item.date).format('MM-DD')) || [],
      axisLine: {
        lineStyle: {
          color: '#30363d',
        },
      },
      axisLabel: {
        color: '#8b949e',
        fontSize: 11,
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '每日订单量',
        position: 'left',
        axisLine: {
          lineStyle: {
            color: '#30363d',
          },
        },
        axisLabel: {
          color: '#8b949e',
          fontSize: 11,
        },
        nameTextStyle: {
          color: '#8b949e',
          fontSize: 11,
        },
        splitLine: {
          lineStyle: {
            color: '#21262d',
          },
        },
      },
      {
        type: 'value',
        name: '总订单量',
        position: 'right',
        axisLine: {
          lineStyle: {
            color: '#30363d',
          },
        },
        axisLabel: {
          color: '#8b949e',
          fontSize: 11,
        },
        nameTextStyle: {
          color: '#8b949e',
          fontSize: 11,
        },
        splitLine: {
          show: false,
        },
      },
    ],
    series: [
      {
        name: '每日订单量',
        type: 'bar',
        yAxisIndex: 0,
        data: dailyData?.map((item: any) => item.orders) || [],
        itemStyle: { 
          color: '#faad14',
        },
      },
      {
        name: '总订单量',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: (() => {
          let cumulative = 0
          return dailyData?.map((item: any) => {
            cumulative += item.orders || 0
            return cumulative
          }) || []
        })(),
        itemStyle: { 
          color: '#58a6ff',
        },
        lineStyle: {
          width: 2,
        },
      },
    ],
  }

  // 销量趋势图配置 - 与销量统计中一致
  const salesChartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '店铺业绩对比',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#c9d1d9',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#1890ff',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
      },
    },
    legend: {
      data: salesOverview?.shop_trends 
        ? ['总销量', ...Object.keys(salesOverview.shop_trends)] 
        : ['总销量'],
      bottom: 10,
      textStyle: {
        color: '#fff',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: salesOverview?.daily_trends?.map((item: any) => item.date) || [],
      axisLine: {
        lineStyle: {
          color: '#30363d',
        },
      },
      axisLabel: {
        color: '#8b949e',
        rotate: 45,
        formatter: (value: string) => dayjs(value).format('MM-DD'),
      },
    },
    yAxis: {
      type: 'value',
      name: '销量（件）',
      nameTextStyle: {
        color: '#8b949e',
      },
      axisLine: {
        lineStyle: {
          color: '#30363d',
        },
      },
      axisLabel: {
        color: '#8b949e',
      },
      splitLine: {
        lineStyle: {
          color: '#21262d',
          type: 'dashed',
        },
      },
    },
    series: (() => {
      const series: any[] = []
      const dailyTrends = salesOverview?.daily_trends || []
      const shopTrends = salesOverview?.shop_trends || {}
      
      // 总销量
      series.push({
        name: '总销量',
        type: 'line',
        data: dailyTrends.map((item: any) => item.quantity),
        smooth: true,
        lineStyle: {
          width: 3,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#1890ff' },
              { offset: 1, color: '#722ed1' },
            ],
          },
        },
        itemStyle: {
          color: '#1890ff',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
            ],
          },
        },
      })
      
      // 各店铺销量
      const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']
      Object.keys(shopTrends).forEach((shopName, index) => {
        const shopData = shopTrends[shopName]
        const dates = dailyTrends.map((item: any) => item.date)
        const quantities: number[] = dates.map((date: string) => {
          const dayData = shopData.find((d: any) => d.date === date)
          return dayData ? dayData.quantity : 0
        })
        
        series.push({
          name: shopName,
          type: 'line',
          data: quantities,
          smooth: true,
          lineStyle: {
            width: 2,
          },
          itemStyle: {
            color: colors[index % colors.length],
          },
          areaStyle: {
            opacity: 0.15,
          },
        })
      })
      
      return series
    })(),
  }

  if (overviewLoading) {
    return <Spin size="large" />
  }

  return (
    <div>
      <h2 style={{ 
        marginBottom: 24, 
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
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
          <Card className="chart-card" loading={salesLoading} bordered={false}>
            <ReactECharts option={salesChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

