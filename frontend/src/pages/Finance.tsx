import { useQuery, useMutation } from '@tanstack/react-query'
import { Table, Card, Row, Col, Statistic, Spin, Tabs, Button, message } from 'antd'
import { DollarOutlined, RiseOutlined, CalculatorOutlined, SyncOutlined, ShoppingOutlined, FundOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import { analyticsApi } from '@/services/api'
import { calculateOrderCosts, getDailyCollectionForecast } from '@/services/orderCostApi'
import { statisticsApi } from '@/services/statisticsApi'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'

function Finance() {
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
  // 获取本月统计数据
  const currentMonth = dayjs().startOf('month').format('YYYY-MM-DD')
  const { data: monthlyStats, isLoading: monthlyStatsLoading } = useQuery({
    queryKey: ['monthly-statistics', currentMonth],
    queryFn: () => statisticsApi.getOverview({
      start_date: currentMonth,
    }),
    staleTime: 0,
  })

  // 获取回款统计数据
  const { data: collectionData, isLoading: collectionLoading } = useQuery({
    queryKey: ['payment-collection', 30],
    queryFn: () => analyticsApi.getPaymentCollection({ days: 30 }),
    staleTime: 0,
  })

  // 获取每日预估回款数据
  const { data: dailyForecastData, isLoading: forecastLoading, refetch: refetchForecast } = useQuery({
    queryKey: ['daily-collection-forecast'],
    queryFn: () => getDailyCollectionForecast(),
    staleTime: 0,
  })

  // 计算订单成本
  const calculateCostsMutation = useMutation({
    mutationFn: calculateOrderCosts,
    onSuccess: (data) => {
      message.success(data.message)
      // 刷新每日预估回款数据
      refetchForecast()
    },
    onError: (error: any) => {
      message.error(`计算失败: ${error.response?.data?.detail || error.message}`)
    },
  })

  // 处理计算成本按钮点击
  const handleCalculateCosts = () => {
    calculateCostsMutation.mutate({
      force_recalculate: false
    })
  }

  // 回款统计表格列
  const collectionColumns: ColumnsType<any> = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 120,
      fixed: 'left' as const,
    },
    ...(collectionData?.summary?.shops?.map((shop: string) => ({
      title: shop,
      dataIndex: shop,
      key: shop,
      width: 150,
      align: 'right' as const,
      render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
    })) || []),
    {
      title: '总计',
      dataIndex: 'total',
      key: 'total',
      width: 150,
      align: 'right' as const,
      render: (val: number) => (
        <span style={{ fontWeight: 'bold', color: '#faad14' }}>
          ¥{val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
      fixed: 'right' as const,
    },
  ]

  // 回款统计折线图配置
  const collectionChartOption = collectionData ? {
    backgroundColor: 'transparent',
    title: {
      text: '📈 回款趋势分析',
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
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((item: any) => {
          result += `${item.marker}${item.seriesName}: ¥${item.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br/>`
        })
        return result
      },
    },
    legend: {
      data: collectionData.chart_data.series.map((s: any) => s.name),
      bottom: 0,
      textStyle: {
        fontSize: 12,
        color: '#8b949e',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: collectionData.chart_data.dates,
      axisLine: {
        lineStyle: {
          color: '#30363d',
        },
      },
      axisLabel: {
        color: '#8b949e',
        fontSize: 11,
        rotate: 45,
        formatter: (value: string) => dayjs(value).format('MM-DD'),
      },
    },
    yAxis: {
      type: 'value',
      name: '回款金额 (CNY)',
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
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`,
      },
      splitLine: {
        lineStyle: {
          color: '#21262d',
        },
      },
    },
    series: collectionData.chart_data.series.map((series: any, index: number) => ({
      name: series.name,
      type: 'line',
      data: series.data,
      smooth: true,
      lineStyle: {
        width: series.name === '总计' ? 3 : 2,
        color: series.name === '总计' ? '#faad14' : undefined, // 金色，更醒目
      },
      itemStyle: {
        color: series.name === '总计' ? '#faad14' : undefined, // 金色
      },
      areaStyle: series.name === '总计' ? {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(250, 173, 20, 0.3)' }, // 金色半透明
            { offset: 1, color: 'rgba(250, 173, 20, 0.05)' }, // 金色更透明
          ],
        },
      } : undefined,
    })),
  } : null

  return (
    <div style={{ padding: '0 4px' }}>
      {/* 页面标题 */}
      <div style={{ 
        marginBottom: 32,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
      <h2 style={{ 
          margin: 0,
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
          fontSize: isMobile ? '20px' : '24px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
      }}>
          <span style={{ fontSize: isMobile ? '24px' : '28px' }}>💰</span>
          财务管理
      </h2>
        {!isMobile && (
          <span style={{ color: '#8b949e', fontSize: '14px' }}>
            {dayjs().format('YYYY年MM月')} 财务数据
          </span>
        )}
        {isMobile && (
          <span style={{ color: '#8b949e', fontSize: '12px' }}>
            {dayjs().format('MM月')} 数据
          </span>
        )}
      </div>
      
      {/* 本月财务概览 */}
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ 
          color: '#8b949e', 
          fontSize: '14px', 
          marginBottom: 16,
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}>
          本月概览
        </h3>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8} lg={8}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: isMobile ? '140px' : '160px',
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
            {monthlyStatsLoading ? (
              <Spin />
            ) : (
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
                  }}>本月总收入</span>
                </div>
                <div>
                  <div style={{ 
                    color: '#58a6ff',
                    fontSize: isMobile ? '28px' : '32px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.2',
                    marginBottom: '4px',
                    textShadow: '0 0 20px rgba(88, 166, 255, 0.5)',
                  }}>
                    ¥{((monthlyStats?.total_gmv || 0) / 1000).toFixed(1)}k
                  </div>
                  {!isMobile && (
                    <div style={{ color: '#8b949e', fontSize: '12px' }}>
                      {(monthlyStats?.total_gmv || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CNY
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: isMobile ? '140px' : '160px',
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
            {monthlyStatsLoading ? (
              <Spin />
            ) : (
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
                  }}>本月总利润</span>
                </div>
                <div>
                  <div style={{ 
                    color: '#52c41a',
                    fontSize: isMobile ? '28px' : '32px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.2',
                    marginBottom: '4px',
                    textShadow: '0 0 20px rgba(82, 196, 26, 0.5)',
                  }}>
                    ¥{((monthlyStats?.total_profit || 0) / 1000).toFixed(1)}k
                  </div>
                  {!isMobile && (
                    <div style={{ color: '#8b949e', fontSize: '12px' }}>
                      {(monthlyStats?.total_profit || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CNY
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={8}>
          <Card 
            className="stat-card" 
            bordered={false} 
            style={{ 
              height: isMobile ? '140px' : '160px',
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
            {monthlyStatsLoading ? (
              <Spin />
            ) : (
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
                    <RiseOutlined style={{ fontSize: '20px', color: '#fff' }} />
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
                    fontSize: isMobile ? '36px' : '40px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.2',
                    marginBottom: '4px',
                    textShadow: '0 0 20px rgba(114, 46, 209, 0.5)',
                  }}>
                    {(monthlyStats?.profit_margin || 0).toFixed(2)}%
                  </div>
                  {!isMobile && (
                    <div style={{ color: '#8b949e', fontSize: '12px' }}>
                      盈利能力指标
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
      </div>

      {/* 详细数据 */}
      <Tabs
        defaultActiveKey="estimated-collection"
        style={{ marginTop: 8 }}
        items={[
          {
            key: 'estimated-collection',
            label: '预估回款',
            children: (
              <div>
      {collectionLoading ? (
        <Card className="chart-card">
          <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />
        </Card>
      ) : (
        <>
          {/* 汇总统计标题 */}
          <h3 style={{ 
            color: '#8b949e', 
            fontSize: '14px', 
            marginBottom: 16,
            marginTop: 0,
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}>
            汇总统计
          </h3>

          {/* 每日预估回款统计 - 汇总卡片 */}
          {forecastLoading ? (
            <Card className="chart-card" style={{ marginBottom: 24 }}>
              <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />
            </Card>
          ) : dailyForecastData && dailyForecastData.length > 0 ? (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card 
                  className="stat-card" 
                  bordered={false} 
                  style={{ 
                    height: '140px',
                    background: 'linear-gradient(135deg, rgba(250, 140, 22, 0.12) 0%, rgba(250, 140, 22, 0.04) 100%)',
                    border: '1px solid rgba(250, 140, 22, 0.25)',
                    boxShadow: '0 6px 24px rgba(250, 140, 22, 0.12)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.boxShadow = '0 10px 36px rgba(250, 140, 22, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 6px 24px rgba(250, 140, 22, 0.12)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 3px 10px rgba(250, 140, 22, 0.35)',
                    }}>
                      <ShoppingOutlined style={{ fontSize: '18px', color: '#fff' }} />
                    </div>
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>总订单数</span>
                  </div>
                  <div style={{ 
                    color: '#fa8c16',
                    fontSize: isMobile ? '24px' : '28px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(250, 140, 22, 0.4)',
                  }}>
                    {dailyForecastData.reduce((sum, item) => sum + item.order_count, 0).toLocaleString('zh-CN')}
                    <span style={{ fontSize: isMobile ? '12px' : '14px', marginLeft: '4px', color: '#8b949e' }}>单</span>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  bordered={false} 
                  style={{ 
                    height: isMobile ? '120px' : '140px',
                    background: 'linear-gradient(135deg, rgba(24, 144, 255, 0.12) 0%, rgba(24, 144, 255, 0.04) 100%)',
                    border: '1px solid rgba(24, 144, 255, 0.25)',
                    boxShadow: '0 6px 24px rgba(24, 144, 255, 0.12)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.boxShadow = '0 10px 36px rgba(24, 144, 255, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 6px 24px rgba(24, 144, 255, 0.12)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 3px 10px rgba(24, 144, 255, 0.35)',
                    }}>
                      <FundOutlined style={{ fontSize: '18px', color: '#fff' }} />
                    </div>
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>总销售额</span>
                  </div>
                  <div style={{ 
                    color: '#1890ff',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(24, 144, 255, 0.4)',
                  }}>
                    ¥{(dailyForecastData.reduce((sum, item) => sum + item.total_amount, 0) / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {dailyForecastData.reduce((sum, item) => sum + item.total_amount, 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  bordered={false} 
                  style={{ 
                    height: isMobile ? '120px' : '140px',
                    background: 'linear-gradient(135deg, rgba(245, 34, 45, 0.12) 0%, rgba(245, 34, 45, 0.04) 100%)',
                    border: '1px solid rgba(245, 34, 45, 0.25)',
                    boxShadow: '0 6px 24px rgba(245, 34, 45, 0.12)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.boxShadow = '0 10px 36px rgba(245, 34, 45, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 6px 24px rgba(245, 34, 45, 0.12)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #f5222d 0%, #cf1322 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 3px 10px rgba(245, 34, 45, 0.35)',
                    }}>
                      <DollarOutlined style={{ fontSize: '18px', color: '#fff' }} />
                    </div>
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>总成本</span>
                  </div>
                  <div style={{ 
                    color: '#f5222d',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(245, 34, 45, 0.4)',
                  }}>
                    ¥{(dailyForecastData.reduce((sum, item) => sum + item.total_cost, 0) / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {dailyForecastData.reduce((sum, item) => sum + item.total_cost, 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  bordered={false} 
                  style={{ 
                    height: isMobile ? '120px' : '140px',
                    background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.12) 0%, rgba(82, 196, 26, 0.04) 100%)',
                    border: '1px solid rgba(82, 196, 26, 0.25)',
                    boxShadow: '0 6px 24px rgba(82, 196, 26, 0.12)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.boxShadow = '0 10px 36px rgba(82, 196, 26, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 6px 24px rgba(82, 196, 26, 0.12)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 3px 10px rgba(82, 196, 26, 0.35)',
                    }}>
                      <RiseOutlined style={{ fontSize: '18px', color: '#fff' }} />
                    </div>
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>总利润</span>
                  </div>
                  <div style={{ 
                    color: '#52c41a',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(82, 196, 26, 0.4)',
                  }}>
                    ¥{(dailyForecastData.reduce((sum, item) => sum + item.total_profit, 0) / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {dailyForecastData.reduce((sum, item) => sum + item.total_profit, 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
            </Row>
          ) : (
            <Card className="chart-card" style={{ marginBottom: 24 }}>
              <div style={{ textAlign: 'center', padding: '50px', color: '#8c8c8c' }}>
                <p>暂无预估回款数据</p>
                <p>订单成本计算完成后将自动显示统计数据</p>
              </div>
            </Card>
          )}

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

          {/* 回款趋势折线图 - 移到表格上方 */}
          {collectionChartOption && (
            <Card className="chart-card" style={{ marginBottom: 32 }}>
              <ReactECharts 
                option={collectionChartOption} 
                style={{ height: isMobile ? 300 : 450 }} 
              />
          </Card>
          )}

          {/* 明细数据标题 */}
          <h3 style={{ 
            color: '#8b949e', 
            fontSize: '14px', 
            marginBottom: 16,
            marginTop: 0,
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}>
            明细数据
          </h3>

          {/* 回款统计表格 */}
          <Card className="chart-card">
            <Table 
              columns={collectionColumns} 
              dataSource={collectionData?.table_data || []}
              scroll={{ x: 'max-content' }}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
            />
          </Card>
        </>
      )}
              </div>
            ),
          },
          // 可以在这里添加更多标签页，例如：
          // {
          //   key: 'other-tab',
          //   label: '其他功能',
          //   children: <div>其他功能内容</div>,
          // },
        ]}
      />
    </div>
  )
}

export default Finance
