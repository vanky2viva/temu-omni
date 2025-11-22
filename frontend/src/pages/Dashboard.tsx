import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Spin, Button } from 'antd'
import {
  ShoppingOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { statisticsApi, analyticsApi } from '@/services/api'
import dayjs from 'dayjs'

// 格式化数字，添加千分位分隔符
const formatNumber = (value: number | undefined, precision: number = 0): string => {
  if (value === undefined || value === null) return '0'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  })
}

function Dashboard() {
  // 统一使用30天作为趋势统计时间范围
  const days = 30
  
  // 计算时间范围（最近30天，用于订单量和趋势图表）
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)
  
  // 自动刷新间隔（秒）- 默认5分钟刷新一次
  const REFRESH_INTERVAL = 5 * 60 * 1000 // 5分钟
  
  // 获取总览数据（所有历史订单 - 用于总订单量、总GMV、总利润、利润率）
  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useQuery({
    queryKey: ['overview-all'],
    queryFn: () => statisticsApi.getOverview(), // 不传时间参数，统计所有订单
    staleTime: 0,
    gcTime: 0, // React Query v5 中 cacheTime 改名为 gcTime
    refetchInterval: REFRESH_INTERVAL, // 每5分钟自动刷新
  })

  // 获取每日趋势数据
  const { data: dailyData, isLoading: dailyLoading, refetch: refetchDaily } = useQuery({
    queryKey: ['daily', days],
    queryFn: () => statisticsApi.getDaily({ days }),
    staleTime: 0,
    gcTime: 0, // React Query v5 中 cacheTime 改名为 gcTime
    refetchInterval: REFRESH_INTERVAL, // 每5分钟自动刷新
  })

  // 获取销量总览数据
  const { data: salesOverview, isLoading: salesLoading, refetch: refetchSales } = useQuery({
    queryKey: ['sales-overview', days],
    queryFn: () => analyticsApi.getSalesOverview({ days }),
    staleTime: 0,
    gcTime: 0, // React Query v5 中 cacheTime 改名为 gcTime
    refetchInterval: REFRESH_INTERVAL, // 每5分钟自动刷新
  })

  // 手动刷新所有数据
  const handleRefresh = () => {
    refetchOverview()
    refetchDaily()
    refetchSales()
  }

  // 趋势图配置 - 每日订单量柱状图和总订单量曲线图
  const trendChartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '📈 近30天销售趋势',
      left: 'left',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
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
      top: '18%',
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
        rotate: 45,
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
        data: dailyData?.map((item: any) => item.order_count) || [],
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
            cumulative += item.order_count || 0
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

  // 调试日志
  if (salesOverview && process.env.NODE_ENV === 'development') {
    console.log('📊 店铺业绩对比数据:', {
      daily_trends: salesOverview?.daily_trends?.length,
      shop_trends: Object.keys(salesOverview?.shop_trends || {})
    })
  }

  // 销量趋势图配置 - 与销量统计中一致
  const salesChartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '🏪 店铺业绩对比',
      left: 'left',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
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
        ? ['总订单量', ...Object.keys(salesOverview.shop_trends)] 
        : ['总订单量'],
      bottom: 10,
      textStyle: {
        color: '#8b949e',
        fontSize: 12,
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '18%',
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
      name: '订单量（单）',
      nameTextStyle: {
        color: '#8b949e',
        fontSize: 11,
      },
      axisLine: {
        lineStyle: {
          color: '#30363d',
        },
      },
      axisLabel: {
        color: '#8b949e',
        fontSize: 11,
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
      
      // 总订单量
      series.push({
        name: '总订单量',
        type: 'line',
        data: dailyTrends.map((item: any) => item.orders || 0),
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#faad14',  // 金色
        },
        itemStyle: {
          color: '#faad14',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(250, 173, 20, 0.3)' },
              { offset: 1, color: 'rgba(250, 173, 20, 0.05)' },
            ],
          },
        },
        z: 1,  // 确保在最上层
      })
      
      // 各店铺订单量
      const colors = ['#1890ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2']
      const shopNames = Object.keys(shopTrends)
      
      shopNames.forEach((shopName, index) => {
        const shopData = shopTrends[shopName]
        const dates = dailyTrends.map((item: any) => item.date)
        const orders: number[] = dates.map((date: string) => {
          const dayData = shopData.find((d: any) => d.date === date)
          return dayData ? (dayData.orders || 0) : 0
        })
        
        series.push({
          name: shopName,
          type: 'line',
          data: orders,
          smooth: true,
          lineStyle: {
            width: 2,
          },
          itemStyle: {
            color: colors[index % colors.length],
          },
          areaStyle: {
            opacity: 0.1,
          },
          z: 0,
        })
      })
      
      return series
    })(),
  }

  if (overviewLoading || dailyLoading || salesLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: '0 4px' }}>
      {/* 页面标题 */}
      <div style={{ 
        marginBottom: 32,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <h2 style={{ 
          margin: 0,
          color: '#c9d1d9',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '24px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <span style={{ fontSize: '28px' }}>📊</span>
          数据总览
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ color: '#8b949e', fontSize: '14px' }}>
            每5分钟自动刷新
        </span>
          <Button
            type="default"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={overviewLoading || dailyLoading || salesLoading}
            style={{
              borderColor: '#30363d',
              color: '#c9d1d9',
              background: '#161b22',
            }}
          >
            手动刷新
          </Button>
        </div>
      </div>
      
      {/* 核心指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12} md={12} lg={6}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: '160px',
              background: 'linear-gradient(135deg, rgba(250, 140, 22, 0.15) 0%, rgba(250, 140, 22, 0.05) 100%)',
              border: '1px solid rgba(250, 140, 22, 0.3)',
              boxShadow: '0 8px 32px rgba(250, 140, 22, 0.15)',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 48px rgba(250, 140, 22, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(250, 140, 22, 0.15)';
            }}
          >
            <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(250, 140, 22, 0.4)',
                }}>
                  <ShoppingOutlined style={{ fontSize: '20px', color: '#fff' }} />
                </div>
                <span style={{ 
                  color: '#8b949e',
                  fontSize: '13px',
                  fontWeight: 500,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}>总订单量</span>
              </div>
              <div>
                <div style={{ 
                  color: '#fa8c16',
                  fontSize: '36px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.2',
                  marginBottom: '4px',
                  textShadow: '0 0 20px rgba(250, 140, 22, 0.5)',
                }}>
                  {formatNumber(overview?.total_orders || 0, 0)}
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px' }}>
                  累计订单总数
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={12} lg={6}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: '160px',
              background: 'linear-gradient(135deg, rgba(88, 166, 255, 0.15) 0%, rgba(88, 166, 255, 0.05) 100%)',
              border: '1px solid rgba(88, 166, 255, 0.3)',
              boxShadow: '0 8px 32px rgba(88, 166, 255, 0.15)',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 48px rgba(88, 166, 255, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(88, 166, 255, 0.15)';
            }}
          >
            <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #58a6ff 0%, #1890ff 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(88, 166, 255, 0.4)',
                }}>
                  <DollarOutlined style={{ fontSize: '20px', color: '#fff' }} />
                </div>
                <span style={{ 
                  color: '#8b949e',
                  fontSize: '13px',
                  fontWeight: 500,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}>总GMV</span>
              </div>
              <div>
                <div style={{ 
                  color: '#58a6ff',
                  fontSize: '32px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.2',
                  marginBottom: '4px',
                  textShadow: '0 0 20px rgba(88, 166, 255, 0.5)',
                }}>
                  ¥{((overview?.total_gmv || 0) / 1000).toFixed(1)}k
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px' }}>
                  {formatNumber(overview?.total_gmv || 0, 2)} CNY
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={12} lg={6}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: '160px',
              background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.15) 0%, rgba(82, 196, 26, 0.05) 100%)',
              border: '1px solid rgba(82, 196, 26, 0.3)',
              boxShadow: '0 8px 32px rgba(82, 196, 26, 0.15)',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 48px rgba(82, 196, 26, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(82, 196, 26, 0.15)';
            }}
          >
            <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #52c41a 0%, #3f8600 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(82, 196, 26, 0.4)',
                }}>
                  <RiseOutlined style={{ fontSize: '20px', color: '#fff' }} />
                </div>
                <span style={{ 
                  color: '#8b949e',
                  fontSize: '13px',
                  fontWeight: 500,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}>总利润</span>
              </div>
              <div>
                <div style={{ 
                  color: '#52c41a',
                  fontSize: '32px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.2',
                  marginBottom: '4px',
                  textShadow: '0 0 20px rgba(82, 196, 26, 0.5)',
                }}>
                  ¥{((overview?.total_profit || 0) / 1000).toFixed(1)}k
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px' }}>
                  {formatNumber(overview?.total_profit || 0, 2)} CNY
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={12} lg={6}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: '160px',
              background: 'linear-gradient(135deg, rgba(114, 46, 209, 0.15) 0%, rgba(114, 46, 209, 0.05) 100%)',
              border: '1px solid rgba(114, 46, 209, 0.3)',
              boxShadow: '0 8px 32px rgba(114, 46, 209, 0.15)',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 48px rgba(114, 46, 209, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(114, 46, 209, 0.15)';
            }}
          >
            <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(114, 46, 209, 0.4)',
                }}>
                  {(overview?.profit_margin || 0) >= 0 ? (
                    <RiseOutlined style={{ fontSize: '20px', color: '#fff' }} />
                  ) : (
                    <FallOutlined style={{ fontSize: '20px', color: '#fff' }} />
                  )}
                </div>
                <span style={{ 
                  color: '#8b949e',
                  fontSize: '13px',
                  fontWeight: 500,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}>利润率</span>
              </div>
              <div>
                <div style={{ 
                  color: '#722ed1',
                  fontSize: '40px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.2',
                  marginBottom: '4px',
                  textShadow: '0 0 20px rgba(114, 46, 209, 0.5)',
                }}>
                  {formatNumber(overview?.profit_margin || 0, 2)}%
                </div>
                <div style={{ color: '#8b949e', fontSize: '12px' }}>
                  盈利能力指标
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 数据趋势 */}
      <h3 style={{ 
        color: '#8b949e', 
        fontSize: '14px', 
        marginBottom: 16,
        marginTop: 32,
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}>
        数据趋势
      </h3>

      {/* 趋势图表 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card className="chart-card" loading={dailyLoading} bordered={false}>
            <ReactECharts option={trendChartOption} style={{ height: 450 }} />
          </Card>
        </Col>
      </Row>

      {/* 店铺对比 */}
      <h3 style={{ 
        color: '#8b949e', 
        fontSize: '14px', 
        marginBottom: 16,
        marginTop: 32,
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}>
        店铺对比
      </h3>

      {/* 店铺对比图表 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card className="chart-card" loading={salesLoading} bordered={false}>
            <ReactECharts option={salesChartOption} style={{ height: 450 }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

