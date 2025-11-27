import { useQuery, useMutation } from '@tanstack/react-query'
import { Table, Card, Row, Col, Statistic, Spin, Tabs, Button, message, DatePicker, Space } from 'antd'
import { DollarOutlined, RiseOutlined, CalculatorOutlined, SyncOutlined, ShoppingOutlined, FundOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import ReactECharts from 'echarts-for-react'
import { analyticsApi, orderApi } from '@/services/api'
import { calculateOrderCosts, getDailyCollectionForecast } from '@/services/orderCostApi'
import { statisticsApi } from '@/services/statisticsApi'
import dayjs from 'dayjs'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'
import { useEffect, useState } from 'react'

// 扩展 dayjs 插件
dayjs.extend(isSameOrBefore)

const { RangePicker } = DatePicker

function Finance() {
  const [isMobile, setIsMobile] = useState(false)
  
  // 日期范围状态，默认为全部数据
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  
  // 是否选择全部历史数据，默认为true（显示全部数据）
  const [isAllData, setIsAllData] = useState(true)

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // 获取快捷日期范围的辅助函数
  const getQuickDateRange = (type: 'today' | 'week' | 'month' | 'lastMonth' | 'last7Days' | 'last30Days' | 'all'): [Dayjs, Dayjs] | null => {
    switch (type) {
      case 'today':
        return [dayjs().startOf('day'), dayjs().endOf('day')]
      case 'week':
        return [dayjs().startOf('week'), dayjs().endOf('week')]
      case 'month':
        return [dayjs().startOf('month'), dayjs().endOf('month')]
      case 'lastMonth':
        return [dayjs().subtract(1, 'month').startOf('month'), dayjs().subtract(1, 'month').endOf('month')]
      case 'last7Days':
        return [dayjs().subtract(6, 'day').startOf('day'), dayjs().endOf('day')]
      case 'last30Days':
        return [dayjs().subtract(29, 'day').startOf('day'), dayjs().endOf('day')]
      case 'all':
        return null
      default:
        return [dayjs().startOf('month'), dayjs().endOf('month')]
    }
  }
  
  // 快捷时间选择函数
  const handleQuickDateSelect = (type: 'today' | 'week' | 'month' | 'lastMonth' | 'last7Days' | 'last30Days' | 'all') => {
    if (type === 'all') {
      setIsAllData(true)
      setDateRange(null)
    } else {
      const range = getQuickDateRange(type)
      if (range) {
        setIsAllData(false)
        setDateRange(range)
      }
    }
  }
  
  // 检查当前日期范围是否匹配某个快捷选项
  const isQuickDateActive = (type: 'today' | 'week' | 'month' | 'lastMonth' | 'last7Days' | 'last30Days' | 'all'): boolean => {
    if (type === 'all') {
      return isAllData
    }
    if (!dateRange) return false
    const expectedRange = getQuickDateRange(type)
    if (!expectedRange) return false
    return dateRange[0].isSame(expectedRange[0], 'day') && dateRange[1].isSame(expectedRange[1], 'day')
  }
  
  // 获取统计数据（使用选择的日期范围）
  const { data: monthlyStats, isLoading: monthlyStatsLoading } = useQuery({
    queryKey: ['sales-overview', isAllData ? 'all' : (dateRange ? `${dateRange[0].format('YYYY-MM-DD')}_${dateRange[1].format('YYYY-MM-DD')}` : 'month')],
    queryFn: () => {
      if (isAllData) {
        // 选择全部时，不传日期参数
        return analyticsApi.getSalesOverview({})
      } else if (dateRange) {
        return analyticsApi.getSalesOverview({
          start_date: dateRange[0].format('YYYY-MM-DD'),
          end_date: dateRange[1].format('YYYY-MM-DD'),
        })
      } else {
        // 默认本月
        return analyticsApi.getSalesOverview({
          start_date: dayjs().startOf('month').format('YYYY-MM-DD'),
          end_date: dayjs().endOf('month').format('YYYY-MM-DD'),
        })
      }
    },
    staleTime: 0,
  })

  // 获取回款统计数据（获取更多天数以确保包含所有回款数据）
  const { data: collectionData, isLoading: collectionLoading } = useQuery({
    queryKey: ['payment-collection', 'all'],
    queryFn: () => analyticsApi.getPaymentCollection({ days: 365 }), // 获取一年内的回款数据
    staleTime: 0,
  })

  // 获取每日预估回款数据
  const { data: dailyForecastData, isLoading: forecastLoading, refetch: refetchForecast } = useQuery({
    queryKey: ['daily-collection-forecast'],
    queryFn: () => getDailyCollectionForecast(),
    staleTime: 0,
  })

  // 获取签收订单统计数据（只统计DELIVERED状态，不包括COMPLETED）
  // 使用统计API而不是直接查询所有订单，避免limit限制问题
  const { data: deliveredOrdersStats, isLoading: deliveredOrdersLoading } = useQuery({
    queryKey: ['delivered-orders-statistics'],
    queryFn: async () => {
      try {
        // 只获取DELIVERED状态的统计数据（已送达订单）
        const deliveredStats = await statisticsApi.getOverview({ status: 'DELIVERED' })
        
        return {
          order_count: deliveredStats?.total_orders || 0,
          total_amount: deliveredStats?.total_gmv || 0,
        }
      } catch (error) {
        console.error('获取签收订单统计失败:', error)
        // 返回默认值，避免页面崩溃
        return {
          order_count: 0,
          total_amount: 0,
        }
      }
    },
    staleTime: 0,
  })

  // 获取订单状态统计数据
  const { data: orderStatusStats, isLoading: orderStatusStatsLoading } = useQuery({
    queryKey: ['order-status-statistics'],
    queryFn: () => orderApi.getStatusStatistics(),
    staleTime: 0,
  })
  
  // 从统计数据中获取签收订单信息（只统计DELIVERED状态）
  const deliveredOrderCount = deliveredOrdersStats?.order_count || 0
  const deliveredOrderTotalAmount = deliveredOrdersStats?.total_amount || 0
  
  // 计算已回款和待回款金额（按回款日期区分，回款日期 = 送达时间 + 8天）
  // 使用 collectionData，它已经按回款日期分组
  const today = dayjs().startOf('day')
  const tableData = collectionData?.table_data || []
  const collectedAmount = tableData.filter(item => {
    const collectionDate = dayjs(item.date).startOf('day')
    return collectionDate.isSameOrBefore(today, 'day')
  }).reduce((sum: number, item: any) => sum + (item.total || 0), 0)
  
  const pendingAmount = tableData.filter(item => {
    const collectionDate = dayjs(item.date).startOf('day')
    return collectionDate.isAfter(today, 'day')
  }).reduce((sum: number, item: any) => sum + (item.total || 0), 0)

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
            {isAllData ? '全部历史数据' : (dateRange ? `${dateRange[0].format('YYYY年MM月DD日')} - ${dateRange[1].format('YYYY年MM月DD日')}` : '')} 财务数据
          </span>
        )}
        {isMobile && (
          <span style={{ color: '#8b949e', fontSize: '12px' }}>
            {isAllData ? '全部数据' : (dateRange ? `${dateRange[0].format('MM/DD')} - ${dateRange[1].format('MM/DD')}` : '')}
          </span>
        )}
      </div>
      
      {/* 本月财务概览 */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ 
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          <div style={{ 
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '8px',
            flex: 1,
            minWidth: isMobile ? '100%' : 'auto',
          }}>
            {/* 日期范围选择器 - 放在最前面 */}
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setIsAllData(false)
                  setDateRange([dates[0], dates[1]])
                } else {
                  setIsAllData(false)
                  setDateRange(null)
                }
              }}
              size="small"
              format="YYYY-MM-DD"
              disabled={isAllData}
              style={{
                width: isMobile ? '100%' : '240px',
                flexShrink: 0,
              }}
              className="finance-date-picker"
              placeholder={['开始日期', '结束日期']}
            />
            {/* 快捷时间选择按钮 */}
            <Space size={8} wrap style={{ flex: 1 }}>
              {(['all', 'today', 'week', 'month', 'lastMonth', 'last7Days', 'last30Days'] as const).map((type) => {
                const labels: Record<typeof type, string> = {
                  all: '全部',
                  today: '今天',
                  week: '本周',
                  month: '本月',
                  lastMonth: '上月',
                  last7Days: '近7天',
                  last30Days: '近30天',
                }
                const isActive = isQuickDateActive(type)
                return (
                  <Button
                    key={type}
                    size="small"
                    type={isActive ? 'primary' : 'default'}
                    onClick={() => handleQuickDateSelect(type)}
                    style={{
                      background: isActive 
                        ? 'linear-gradient(135deg, rgba(88, 166, 255, 0.3) 0%, rgba(88, 166, 255, 0.2) 100%)' 
                        : 'rgba(30, 41, 59, 0.6)',
                      border: isActive 
                        ? '1px solid rgba(88, 166, 255, 0.8)' 
                        : '1px solid rgba(99, 102, 241, 0.3)',
                      color: isActive ? '#58a6ff' : '#cbd5e1',
                      fontWeight: isActive ? 'bold' : 'normal',
                      boxShadow: isActive ? '0 2px 4px rgba(88, 166, 255, 0.2)' : 'none',
                    }}
                  >
                    {labels[type]}
                  </Button>
                )
              })}
            </Space>
          </div>
          <h3 style={{ 
            color: '#8b949e', 
            fontSize: '14px', 
            margin: 0,
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            flexShrink: 0,
            }}>
            {isAllData ? '全部概览' : (dateRange ? `${dateRange[0].format('YYYY年MM月DD日')} - ${dateRange[1].format('YYYY年MM月DD日')} 概览` : '本月概览')}
          </h3>
        </div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8} lg={8}>
          <Card 
            className="stat-card" 
            variant="borderless" 
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
                  }}>GMV</span>
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
            variant="borderless" 
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
                  }}>利润</span>
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
            variant="borderless" 
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

          {/* 汇总统计卡片 */}
          {deliveredOrdersLoading || forecastLoading ? (
            <Card className="chart-card" style={{ marginBottom: 24 }}>
              <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />
            </Card>
          ) : (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  variant="borderless" 
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
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>签收订单数</span>
                  </div>
                  <div style={{ 
                    color: '#fa8c16',
                    fontSize: isMobile ? '24px' : '28px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(250, 140, 22, 0.4)',
                  }}>
                    {deliveredOrderCount.toLocaleString('zh-CN')}
                    <span style={{ fontSize: isMobile ? '12px' : '14px', marginLeft: '4px', color: '#8b949e' }}>单</span>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  variant="borderless" 
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
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>签收订单总价</span>
                  </div>
                  <div style={{ 
                    color: '#1890ff',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(24, 144, 255, 0.4)',
                  }}>
                    ¥{(deliveredOrderTotalAmount / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {deliveredOrderTotalAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  variant="borderless" 
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
                      <DollarOutlined style={{ fontSize: '18px', color: '#fff' }} />
                    </div>
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>已回款金额</span>
                  </div>
                  <div style={{ 
                    color: '#52c41a',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(82, 196, 26, 0.4)',
                  }}>
                    ¥{(collectedAmount / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {collectedAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6} lg={6}>
                <Card 
                  className="stat-card" 
                  variant="borderless" 
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
                    <span style={{ color: '#8b949e', fontSize: '12px', fontWeight: 500 }}>待回款金额</span>
                  </div>
                  <div style={{ 
                    color: '#f5222d',
                    fontSize: isMobile ? '20px' : '24px',
                    fontWeight: 700,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.3',
                    textShadow: '0 0 15px rgba(245, 34, 45, 0.4)',
                  }}>
                    ¥{(pendingAmount / 1000).toFixed(1)}k
                    {!isMobile && (
                      <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px', fontWeight: 400 }}>
                        {pendingAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CNY
                      </div>
                    )}
                  </div>
                </Card>
              </Col>
            </Row>
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
      {/* DatePicker 暗色主题样式 */}
      <style>{`
        .finance-date-picker .ant-picker {
          background: rgba(30, 41, 59, 0.6) !important;
          border: 1px solid rgba(99, 102, 241, 0.3) !important;
          color: #cbd5e1 !important;
        }
        .finance-date-picker .ant-picker:hover {
          border-color: rgba(99, 102, 241, 0.5) !important;
        }
        .finance-date-picker .ant-picker-input > input {
          color: #cbd5e1 !important;
        }
        .finance-date-picker .ant-picker-input > input::placeholder {
          color: #64748b !important;
        }
        .finance-date-picker.ant-picker-disabled {
          background: rgba(30, 41, 59, 0.3) !important;
          border-color: rgba(99, 102, 241, 0.2) !important;
          opacity: 0.5;
        }
        .finance-date-picker .ant-picker-separator {
          color: #cbd5e1 !important;
        }
        .finance-date-picker .ant-picker-suffix {
          color: #cbd5e1 !important;
        }
        /* DatePicker 下拉面板暗色主题 */
        .ant-picker-dropdown {
          background: rgba(15, 23, 42, 0.95) !important;
          border: 1px solid rgba(99, 102, 241, 0.3) !important;
        }
        .ant-picker-dropdown .ant-picker-panel {
          background: rgba(15, 23, 42, 0.95) !important;
        }
        .ant-picker-dropdown .ant-picker-header {
          border-bottom: 1px solid rgba(99, 102, 241, 0.3) !important;
        }
        .ant-picker-dropdown .ant-picker-header button {
          color: #cbd5e1 !important;
        }
        .ant-picker-dropdown .ant-picker-content th {
          color: #8b949e !important;
        }
        .ant-picker-dropdown .ant-picker-cell {
          color: #cbd5e1 !important;
        }
        .ant-picker-dropdown .ant-picker-cell:hover:not(.ant-picker-cell-disabled):not(.ant-picker-cell-selected) .ant-picker-cell-inner {
          background: rgba(99, 102, 241, 0.2) !important;
        }
        .ant-picker-dropdown .ant-picker-cell-selected .ant-picker-cell-inner {
          background: rgba(88, 166, 255, 0.3) !important;
          color: #58a6ff !important;
        }
        .ant-picker-dropdown .ant-picker-cell-in-range::before {
          background: rgba(99, 102, 241, 0.1) !important;
        }
      `}</style>
    </div>
  )
}

export default Finance