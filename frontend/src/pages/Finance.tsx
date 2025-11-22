import { useQuery, useMutation } from '@tanstack/react-query'
import { Table, Card, Row, Col, Statistic, Spin, Tabs, Button, message, Select, Space, DatePicker } from 'antd'
import { DollarOutlined, RiseOutlined, CalculatorOutlined, SyncOutlined, ShoppingOutlined, FundOutlined, CalendarOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import ReactECharts from 'echarts-for-react'
import { analyticsApi, orderApi } from '@/services/api'
import { calculateOrderCosts, getDailyCollectionForecast } from '@/services/orderCostApi'
import { statisticsApi } from '@/services/statisticsApi'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'

const { RangePicker } = DatePicker

function Finance() {
  const [isMobile, setIsMobile] = useState(false)
  // 日期范围状态，默认显示全部数据
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // 获取统计数据
  // 使用与销量统计页面相同的数据源，确保数据一致
  const { data: monthlyStats, isLoading: monthlyStatsLoading } = useQuery({
    queryKey: ['sales-overview', dateRange],
    queryFn: () => {
      const startDate = dateRange?.[0]?.format('YYYY-MM-DD')
      const endDate = dateRange?.[1]?.format('YYYY-MM-DD')
      return analyticsApi.getSalesOverview({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      })
    },
    staleTime: 0,
  })

  // 获取订单状态统计（用于显示总订单数和已送达订单数）
  const { data: orderStatusStats, isLoading: orderStatusStatsLoading } = useQuery({
    queryKey: ['order-status-statistics', dateRange],
    queryFn: () => {
      const params: any = {}
      if (dateRange) {
        params.start_date = dateRange[0].toISOString()
        params.end_date = dateRange[1].toISOString()
      }
      return orderApi.getStatusStatistics(params)
    },
    staleTime: 30000, // 30秒缓存
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
            {dateRange 
              ? `${dateRange[0].format('YYYY年MM月DD日')} - ${dateRange[1].format('YYYY年MM月DD日')} 财务数据`
              : `${dayjs().format('YYYY年MM月')} 财务数据`
            }
          </span>
        )}
        {isMobile && (
          <span style={{ color: '#8b949e', fontSize: '12px' }}>
            {dateRange 
              ? `${dateRange[0].format('MM-DD')} - ${dateRange[1].format('MM-DD')}`
              : `${dayjs().format('MM月')} 数据`
            }
          </span>
        )}
      </div>
      
      {/* 日期范围选择器 */}
      <div style={{ marginBottom: 24 }}>
        <Card 
          bordered={false}
          style={{ 
            background: 'transparent',
            border: '1px solid #30363d',
          }}
        >
          <Space size="large" wrap style={{ width: '100%' }}>
            <Space>
              <CalendarOutlined style={{ color: '#00d1b2' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 500 }}>时间范围：</span>
              {/* 快捷时间选择下拉框 */}
              <Select
                placeholder="快捷选择"
                allowClear
                style={{ width: 120 }}
                onChange={(value) => {
                  if (!value) {
                    // 清除时恢复默认全部数据
                    setDateRange(null)
                    return
                  }
                  
                  let start: Dayjs
                  let end: Dayjs = dayjs()
                  
                  switch (value) {
                    case 'today':
                      start = dayjs().startOf('day')
                      end = dayjs().endOf('day')
                      break
                    case 'yesterday':
                      start = dayjs().subtract(1, 'day').startOf('day')
                      end = dayjs().subtract(1, 'day').endOf('day')
                      break
                    case 'last7days':
                      start = dayjs().subtract(6, 'day').startOf('day')
                      end = dayjs().endOf('day')
                      break
                    case 'last30days':
                      start = dayjs().subtract(29, 'day').startOf('day')
                      end = dayjs().endOf('day')
                      break
                    case 'thisMonth':
                      start = dayjs().startOf('month')
                      end = dayjs().endOf('month')
                      break
                    case 'lastMonth':
                      start = dayjs().subtract(1, 'month').startOf('month')
                      end = dayjs().subtract(1, 'month').endOf('month')
                      break
                    default:
                      return
                  }
                  
                  setDateRange([start, end])
                }}
                options={[
                  { label: '今天', value: 'today' },
                  { label: '昨天', value: 'yesterday' },
                  { label: '最近7天', value: 'last7days' },
                  { label: '最近30天', value: 'last30days' },
                  { label: '本月', value: 'thisMonth' },
                  { label: '上月', value: 'lastMonth' },
                ]}
              />
              <RangePicker
                value={dateRange}
                onChange={(dates) => setDateRange(dates)}
                format="YYYY-MM-DD"
                placeholder={['开始日期', '结束日期']}
                allowClear
                style={{ width: 240 }}
              />
            </Space>
          </Space>
        </Card>
      </div>
      
      {/* 财务概览 */}
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ 
          color: '#8b949e', 
          fontSize: '14px', 
          marginBottom: 16,
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}>
          财务概览
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
                  }}>总收入</span>
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
                  }}>总利润</span>
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
                    {monthlyStats?.total_gmv && monthlyStats?.total_gmv > 0 
                      ? ((monthlyStats?.total_profit || 0) / monthlyStats.total_gmv * 100).toFixed(2)
                      : '0.00'
                    }%
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

          {/* 订单统计卡片 - 总订单数、已送达订单数和送达率 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={8} lg={8}>
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
                  {orderStatusStatsLoading ? (
                    <span style={{ fontSize: isMobile ? '12px' : '14px', color: '#8b949e' }}>加载中...</span>
                  ) : (
                    <>
                      {(orderStatusStats?.total_orders || 0).toLocaleString('zh-CN')}
                      <span style={{ fontSize: isMobile ? '12px' : '14px', marginLeft: '4px', color: '#8b949e' }}>单</span>
                    </>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8} lg={8}>
              <Card 
                className="stat-card" 
                bordered={false} 
                style={{ 
                  height: '140px',
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
                  <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>已送达订单数</span>
                </div>
                <div style={{ 
                  color: '#52c41a',
                  fontSize: isMobile ? '24px' : '28px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.3',
                  textShadow: '0 0 15px rgba(82, 196, 26, 0.4)',
                }}>
                  {orderStatusStatsLoading ? (
                    <span style={{ fontSize: isMobile ? '12px' : '14px', color: '#8b949e' }}>加载中...</span>
                  ) : (
                    <>
                      {(orderStatusStats?.delivered || 0).toLocaleString('zh-CN')}
                      <span style={{ fontSize: isMobile ? '12px' : '14px', marginLeft: '4px', color: '#8b949e' }}>单</span>
                    </>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8} lg={8}>
              <Card 
                className="stat-card" 
                bordered={false} 
                style={{ 
                  height: '140px',
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
                    <CheckCircleOutlined style={{ fontSize: '18px', color: '#fff' }} />
                  </div>
                  <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>送达率</span>
                </div>
                <div style={{ 
                  color: '#1890ff',
                  fontSize: isMobile ? '24px' : '28px',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: '1.3',
                  textShadow: '0 0 15px rgba(24, 144, 255, 0.4)',
                }}>
                  {orderStatusStatsLoading ? (
                    <span style={{ fontSize: isMobile ? '12px' : '14px', color: '#8b949e' }}>加载中...</span>
                  ) : (
                    <>
                      {orderStatusStats?.total_orders && orderStatusStats.total_orders > 0
                        ? ((orderStatusStats.delivered || 0) / orderStatusStats.total_orders * 100).toFixed(2)
                        : '0.00'
                      }%
                    </>
                  )}
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
