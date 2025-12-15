import { useQuery } from '@tanstack/react-query'
import { Table, Card, Row, Col, Spin, Tabs, Button, DatePicker, Space, Upload, message, Statistic, Tooltip, Modal, Progress, App } from 'antd'
import { DollarOutlined, RiseOutlined, ShoppingOutlined, FundOutlined, UploadOutlined, FileExcelOutlined, CheckCircleOutlined, RightOutlined, DownOutlined, WarningOutlined, CopyOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import LazyECharts from '@/components/LazyECharts'
import { analyticsApi, profitStatementApi } from '@/services/api'
import { getDailyCollectionForecast } from '@/services/orderCostApi'
import { statisticsApi } from '@/services/statisticsApi'
import dayjs from 'dayjs'
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore'
import { useEffect, useState, useMemo } from 'react'

// 扩展 dayjs 插件
dayjs.extend(isSameOrBefore)

const { RangePicker } = DatePicker

function Finance() {
  const [isMobile, setIsMobile] = useState(false)
  
  // 日期范围状态，默认为全部数据
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)
  
  // 是否选择全部历史数据，默认为true（显示全部数据）
  const [isAllData, setIsAllData] = useState(true)
  
  // 标签选择状态，从localStorage读取或使用默认值
  const [activeTabKey, setActiveTabKey] = useState<string>(() => {
    const savedTab = localStorage.getItem('finance_active_tab')
    return savedTab || 'estimated-collection'
  })
  
  // 利润表相关状态
  const [profitCollectionData, setProfitCollectionData] = useState<Array<{ parent_order_sn: string; sales_collection: number; sales_collection_after_discount: number; sales_reversal: number; shipping_collection: number; shipping_collection_after_discount: number }>>([])
  const [profitShippingData, setProfitShippingData] = useState<Array<{ order_sn: string; parent_order_sn?: string; shipping_cost: number; chargeable_weight?: number }>>([])
  const [profitDeductionData, setProfitDeductionData] = useState<Array<{ order_sn: string; parent_order_sn?: string; deduction: number }>>([])
  const [profitLastMileShippingData, setProfitLastMileShippingData] = useState<Array<{ order_sn: string; last_mile_cost: number }>>([])
  const [profitData, setProfitData] = useState<any>(null)
  const [calculating, setCalculating] = useState(false)
  const [revenueExpanded, setRevenueExpanded] = useState<Record<string, boolean>>({}) // 收入列展开状态
  
  // 从localStorage加载已保存的利润数据
  useEffect(() => {
    const savedProfitData = localStorage.getItem('profit_statement_data')
    if (savedProfitData) {
      try {
        const parsed = JSON.parse(savedProfitData)
        setProfitData(parsed)
      } catch (e) {
        console.error('加载保存的利润数据失败:', e)
      }
    }
  }, [])
  
  // 保存利润数据到localStorage
  useEffect(() => {
    if (profitData) {
      localStorage.setItem('profit_statement_data', JSON.stringify(profitData))
    }
  }, [profitData])

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
  const { isLoading: forecastLoading } = useQuery({
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

  // 从统计数据中获取签收订单信息（只统计DELIVERED状态）
  const deliveredOrderCount = deliveredOrdersStats?.order_count || 0
  const deliveredOrderTotalAmount = deliveredOrdersStats?.total_amount || 0
  
  // 计算已回款和待回款金额（按回款日期区分，回款日期 = 送达时间 + 8天）
  // 使用 collectionData，它已经按回款日期分组
  const today = dayjs().startOf('day')
  const tableData = collectionData?.table_data || []
  const collectedAmount = tableData.filter((item: any) => {
    const collectionDate = dayjs(item.date).startOf('day')
    return collectionDate.isSameOrBefore(today, 'day')
  }).reduce((sum: number, item: any) => sum + (item.total || 0), 0)
  
  const pendingAmount = tableData.filter((item: any) => {
    const collectionDate = dayjs(item.date).startOf('day')
    return collectionDate.isAfter(today, 'day')
  }).reduce((sum: number, item: any) => sum + (item.total || 0), 0)

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
    series: collectionData.chart_data.series.map((series: any) => ({
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
        activeKey={activeTabKey}
        onChange={(key) => {
          setActiveTabKey(key)
          localStorage.setItem('finance_active_tab', key)
        }}
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
              <LazyECharts 
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
          {
            key: 'profit-statement',
            label: '账单统计',
            children: (
              <ProfitStatementTab
                collectionData={profitCollectionData}
                shippingData={profitShippingData}
                deductionData={profitDeductionData}
                lastMileShippingData={profitLastMileShippingData}
                profitData={profitData}
                calculating={calculating}
                onCollectionUpload={(data) => setProfitCollectionData(data)}
                onShippingUpload={(data) => setProfitShippingData(data)}
                onDeductionUpload={(data) => setProfitDeductionData(data)}
                onLastMileShippingUpload={(data) => setProfitLastMileShippingData(data)}
                onCalculate={() => {
                  setCalculating(true)
                  profitStatementApi.calculateProfit({
                    collection_data: profitCollectionData as any,
                    shipping_data: profitShippingData,
                    deduction_data: profitDeductionData,
                    last_mile_shipping_data: profitLastMileShippingData,
                  }).then((result) => {
                    setProfitData(result.data)
                    // 使用静态 message，因为这是在 Finance 组件中
                    message.success(result.message || '利润计算完成')
                  }).catch((error) => {
                    message.error(error.response?.data?.detail || '计算失败')
                  }).finally(() => {
                    setCalculating(false)
                  })
                }}
                onProfitDataUpdate={(data) => {
                  setProfitData(data)
                }}
                revenueExpanded={revenueExpanded}
                onRevenueToggle={(key: string) => {
                  setRevenueExpanded(prev => ({
                    ...prev,
                    [key]: !prev[key]
                  }))
                }}
              />
            ),
          },
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
        /* 利润表固定列样式 - 深色主题下确保不透明度100%，避免重叠遮挡 */
        /* 通用固定列样式 - 确保完全不透明，但使用与普通列相同的背景色 */
        .theme-dark .profit-statement-table .ant-table-wrapper .ant-table-cell.ant-table-cell-fix {
          position: sticky !important;
          opacity: 1 !important;
          /* 不设置背景色，使用普通列的背景色 */
        }
        .theme-dark .profit-statement-table .ant-table-wrapper .ant-table-thead .ant-table-cell.ant-table-cell-fix {
          /* 不设置背景色，使用普通列的背景色 */
        }
        .theme-dark .profit-statement-table .ant-table-container {
          background: #161b22 !important;
          background-color: #161b22 !important;
        }
        .theme-dark .profit-statement-table .ant-table {
          background: #161b22 !important;
          background-color: #161b22 !important;
        }
        .theme-dark .profit-statement-table .ant-table-body {
          background: #161b22 !important;
          background-color: #161b22 !important;
        }
        /* 固定列单元格 - 深色主题下完全不透明，但使用与普通列相同的背景色 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right {
          opacity: 1 !important;
          /* 不设置背景色，使用普通列的背景色 */
          z-index: 1000 !important;
          position: relative !important;
        }
        /* 表头固定列 - 使用与普通表头相同的背景色 */
        .theme-dark .profit-statement-table .ant-table-thead > tr > th.ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-thead > tr > th.ant-table-cell-fix-right {
          opacity: 1 !important;
          /* 不设置背景色，使用普通表头的背景色 */
          z-index: 1001 !important;
        }
        /* 表体固定列 - 使用与普通单元格相同的背景色 */
        .theme-dark .profit-statement-table .ant-table-tbody > tr > td.ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-tbody > tr > td.ant-table-cell-fix-right {
          opacity: 1 !important;
          /* 不设置背景色，使用普通单元格的背景色 */
          z-index: 1000 !important;
        }
        /* 固定列hover状态 - 使用与普通单元格hover相同的背景色 */
        .theme-dark .profit-statement-table .ant-table-tbody > tr:hover > td.ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-tbody > tr:hover > td.ant-table-cell-fix-right {
          /* 不设置背景色，使用普通单元格hover的背景色 */
        }
        /* 固定列的伪元素（阴影效果）也要不透明 - 深色主题 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left-first::after,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right-first::after,
        .theme-dark .profit-statement-table .ant-table-cell-fix-left-last::after,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right-last::after {
          opacity: 1 !important;
          /* 不设置背景色，使用普通列的背景色 */
          z-index: 999 !important;
          display: none !important; /* 隐藏伪元素，避免遮挡 */
        }
        /* 确保固定列阴影效果 - 深色主题 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left {
          box-shadow: 2px 0 8px rgba(0, 0, 0, 0.8) !important;
          border-right: 1px solid #30363d !important;
        }
        .theme-dark .profit-statement-table .ant-table-cell-fix-right {
          box-shadow: -2px 0 8px rgba(0, 0, 0, 0.8) !important;
          border-left: 1px solid #30363d !important;
        }
        /* 确保固定列内的所有内容都可见 - 深色主题 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left *,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right * {
          opacity: 1 !important;
        }
        /* 确保固定列在滚动时始终在最上层 */
        .theme-dark .profit-statement-table .ant-table-body {
          position: relative;
        }
        .theme-dark .profit-statement-table .ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right {
          will-change: transform;
        }
        /* 确保固定列覆盖其他内容 - 深色主题 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left {
          position: sticky !important;
          left: 0 !important;
          /* 不设置背景色，使用普通列的背景色 */
        }
        .theme-dark .profit-statement-table .ant-table-cell-fix-right {
          position: sticky !important;
          right: 0 !important;
          /* 不设置背景色，使用普通列的背景色 */
        }
        /* 确保固定列文字颜色在深色主题下可见 */
        .theme-dark .profit-statement-table .ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-cell-fix-right {
          /* 不设置背景色，使用普通列的背景色 */
        }
        .theme-dark .profit-statement-table .ant-table-thead > tr > th.ant-table-cell-fix-left,
        .theme-dark .profit-statement-table .ant-table-thead > tr > th.ant-table-cell-fix-right {
          /* 不设置背景色，使用普通列的背景色 */
        }
      `}</style>
    </div>
  )
}

// 利润表Tab组件
function ProfitStatementTab({
  collectionData,
  shippingData,
  deductionData,
  lastMileShippingData,
  profitData,
  calculating,
  onCollectionUpload,
  onShippingUpload,
  onDeductionUpload,
  onLastMileShippingUpload,
  onCalculate,
  onProfitDataUpdate,
  revenueExpanded,
  onRevenueToggle,
}: {
  collectionData: Array<{ parent_order_sn: string; sales_collection: number; sales_collection_after_discount: number; sales_reversal: number; shipping_collection: number; shipping_collection_after_discount: number }>
  shippingData: Array<{ order_sn: string; parent_order_sn?: string; shipping_cost: number; chargeable_weight?: number }>
  deductionData: Array<{ order_sn: string; parent_order_sn?: string; deduction: number }>
  lastMileShippingData: Array<{ order_sn: string; last_mile_cost: number }>
  profitData: any
  calculating: boolean
  onCollectionUpload: (data: Array<{ parent_order_sn: string; sales_collection: number; sales_collection_after_discount: number; sales_reversal: number; shipping_collection: number; shipping_collection_after_discount: number }>) => void
  onShippingUpload: (data: Array<{ order_sn: string; parent_order_sn?: string; shipping_cost: number; chargeable_weight?: number }>) => void
  onDeductionUpload: (data: Array<{ order_sn: string; parent_order_sn?: string; deduction: number }>) => void
  onLastMileShippingUpload: (data: Array<{ order_sn: string; last_mile_cost: number }>) => void
  onCalculate: () => void
  onProfitDataUpdate: (data: any) => void
  revenueExpanded: Record<string, boolean>
  onRevenueToggle: (key: string) => void
}) {
  const { message: messageApi } = App.useApp()
  const [isMobile, setIsMobile] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{
    visible: boolean
    percent: number
    status: 'active' | 'success' | 'exception'
    text: string
  }>({
    visible: false,
    percent: 0,
    status: 'active',
    text: '正在上传文件...',
  })
  
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // 自动计算利润（使用所有已上传的数据）
  const autoCalculate = async (updatedCollectionData?: any, updatedShippingData?: any, updatedDeductionData?: any, updatedLastMileData?: any) => {
    // 使用传入的最新数据，如果没有则使用当前状态数据
    const currentCollectionData = updatedCollectionData || collectionData
    const currentShippingData = updatedShippingData || shippingData
    const currentDeductionData = updatedDeductionData || deductionData
    const currentLastMileData = updatedLastMileData || lastMileShippingData
    
    // 至少需要有结算数据才能计算
    if (currentCollectionData.length === 0) {
      return
    }
    
    try {
      const result = await profitStatementApi.calculateProfit({
        collection_data: currentCollectionData as any,
        shipping_data: currentShippingData,
        deduction_data: currentDeductionData,
        last_mile_shipping_data: currentLastMileData,
      })
      onProfitDataUpdate(result.data)
      // 不显示成功提示，避免频繁提示
    } catch (error: any) {
      console.error('自动计算失败:', error)
      // 不显示错误提示，因为可能只是缺少某些数据
    }
  }
  
  const handleUpload = async (type: 'collection' | 'shipping' | 'deduction' | 'lastMileShipping' | 'orderList', file: File) => {
    try {
      let result
      let updatedData: any = null
      
      if (type === 'collection') {
        result = await profitStatementApi.uploadCollection(file)
        updatedData = result.data
        onCollectionUpload(updatedData)
        // 上传结算表后，立即使用新数据计算
        await autoCalculate(updatedData, shippingData, deductionData, lastMileShippingData)
      } else if (type === 'shipping') {
        result = await profitStatementApi.uploadShipping(file)
        updatedData = result.data
        onShippingUpload(updatedData)
        // 上传头程运费表后，立即使用新数据计算
        await autoCalculate(collectionData, updatedData, deductionData, lastMileShippingData)
      } else if (type === 'deduction') {
        result = await profitStatementApi.uploadDeduction(file)
        updatedData = result.data
        onDeductionUpload(updatedData)
        // 上传延迟扣款表后，立即使用新数据计算
        await autoCalculate(collectionData, shippingData, updatedData, lastMileShippingData)
      } else if (type === 'lastMileShipping') {
        result = await profitStatementApi.uploadLastMileShipping(file)
        updatedData = result.data
        onLastMileShippingUpload(updatedData)
        // 上传尾程运费表后，立即使用新数据计算
        await autoCalculate(collectionData, shippingData, deductionData, updatedData)
      } else if (type === 'orderList') {
        // 显示上传进度Modal
        setUploadProgress({
          visible: true,
          percent: 10,
          status: 'active',
          text: '正在上传文件...',
        })
        
        // 模拟上传进度
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev.percent < 80) {
              return {
                ...prev,
                percent: Math.min(prev.percent + 10, 80),
              }
            }
            return prev
          })
        }, 200)
        
        try {
          result = await profitStatementApi.uploadOrderList(file)
          
          clearInterval(progressInterval)
          
          // 更新进度到90%
          setUploadProgress(prev => ({
            ...prev,
            percent: 90,
            text: '正在匹配订单并更新数据...',
          }))
          
          // 等待一小段时间让用户看到进度
          await new Promise(resolve => setTimeout(resolve, 300))
          
          // 上传订单列表后，显示处理结果
          if (result.data) {
            const { total, matched, updated, unmatched } = result.data
            
            // 如果有已计算的利润数据，自动重新计算以更新包裹号
            if (profitData && profitData.items && profitData.items.length > 0 && collectionData.length > 0) {
              // 更新进度：开始重新计算利润
              setUploadProgress(prev => ({
                ...prev,
                percent: 92,
                text: '正在重新计算利润表以更新包裹号...',
              }))
              
              try {
                // 等待一小段时间，确保数据库更新已完全提交
                await new Promise(resolve => setTimeout(resolve, 500))
                
                // 自动重新计算利润，这样会从数据库重新查询最新的包裹号
                await autoCalculate(collectionData, shippingData, deductionData, lastMileShippingData)
                
                // 更新进度到完成
                setUploadProgress({
                  visible: true,
                  percent: 100,
                  status: 'success',
                  text: `处理完成：共${total}条，匹配${matched}条，更新${updated}条${unmatched > 0 ? `，${unmatched}条未匹配` : ''}。利润表已更新包裹号。`,
                })
                
                // 获取包裹号列信息
                const packageColName = result.data?.package_sn_col_name
                const recordsWithPackage = result.data?.records_with_package || 0
                
                if (updated > 0) {
                  messageApi.success(
                    `订单列表处理完成：共${total}条，匹配${matched}条，更新${updated}条${unmatched > 0 ? `，${unmatched}条未匹配` : ''}${packageColName ? `（包裹号列：${packageColName}）` : ''}。利润表已自动更新包裹号信息。`,
                    5
                  )
                } else {
                  let warningMsg = `订单列表处理完成：共${total}条，匹配${matched}条，但更新了0条。`
                  if (!packageColName) {
                    warningMsg += `\n未识别到包裹号列，请确保文件包含包裹号列（如列名"包裹号"或"Y"列）。`
                  } else if (recordsWithPackage === 0) {
                    warningMsg += `\n已识别包裹号列"${packageColName}"，但该列数据为空或无效。`
                  } else {
                    warningMsg += `\n已识别包裹号列"${packageColName}"（包含${recordsWithPackage}条包裹号数据），但未更新任何记录。可能是订单已有相同包裹号。`
                  }
                  warningMsg += `\n已重新计算利润表。`
                  messageApi.warning(warningMsg, 8)
                }
              } catch (error) {
                // 重新计算失败，但订单列表已成功上传
                setUploadProgress({
                  visible: true,
                  percent: 100,
                  status: 'success',
                  text: `处理完成：共${total}条，匹配${matched}条，更新${updated}条${unmatched > 0 ? `，${unmatched}条未匹配` : ''}`,
                })
                messageApi.warning('订单列表已更新，但重新计算利润表失败，请手动点击"计算利润"按钮更新包裹号信息', 5)
              }
            } else {
              // 没有利润数据，直接完成
              setUploadProgress({
                visible: true,
                percent: 100,
                status: 'success',
                text: `处理完成：共${total}条，匹配${matched}条，更新${updated}条${unmatched > 0 ? `，${unmatched}条未匹配` : ''}`,
              })
              
              // 获取包裹号列信息
              const packageColName = result.data?.package_sn_col_name
              const recordsWithPackage = result.data?.records_with_package || 0
              
              if (updated > 0) {
                messageApi.success(
                  `订单列表处理完成：共${total}条，匹配${matched}条，更新${updated}条${unmatched > 0 ? `，${unmatched}条未匹配` : ''}${packageColName ? `（包裹号列：${packageColName}）` : ''}`,
                  5
                )
              } else {
                let warningMsg = `订单列表处理完成：共${total}条，匹配${matched}条，但更新了0条。`
                if (!packageColName) {
                  warningMsg += `\n未识别到包裹号列，请确保文件包含包裹号列（如列名"包裹号"或"Y"列）。`
                } else if (recordsWithPackage === 0) {
                  warningMsg += `\n已识别包裹号列"${packageColName}"，但该列数据为空或无效。`
                } else {
                  warningMsg += `\n已识别包裹号列"${packageColName}"（包含${recordsWithPackage}条包裹号数据），但未更新任何记录。可能是订单已有相同包裹号。`
                }
                messageApi.warning(warningMsg, 8)
              }
            }
            
            // 1.5秒后关闭Modal
            setTimeout(() => {
              setUploadProgress({
                visible: false,
                percent: 0,
                status: 'active',
                text: '',
              })
            }, 2000)
          } else {
            setUploadProgress({
              visible: true,
              percent: 100,
              status: 'success',
              text: result.message || '上传成功',
            })
            setTimeout(() => {
              setUploadProgress({
                visible: false,
                percent: 0,
                status: 'active',
                text: '',
              })
            }, 1500)
            messageApi.success(result.message || '上传成功')
          }
        } catch (error: any) {
          clearInterval(progressInterval)
          setUploadProgress({
            visible: false,
            percent: 0,
            status: 'exception',
            text: '',
          })
          messageApi.error(error.response?.data?.detail || '上传失败')
        }
        return // 订单列表上传不需要触发计算
      }
      
      messageApi.success(result.message || '上传成功，数据已自动更新')
      
    } catch (error: any) {
      messageApi.error(error.response?.data?.detail || '上传失败')
    }
  }
  
  // 复制到剪贴板
  const copyToClipboard = (text: string) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        messageApi.success('已复制到剪贴板')
      }).catch(() => {
        // 降级方案
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.opacity = '0'
        document.body.appendChild(textArea)
        textArea.select()
        try {
          document.execCommand('copy')
          messageApi.success('已复制到剪贴板')
        } catch (err) {
          messageApi.error('复制失败')
        }
        document.body.removeChild(textArea)
      })
    } else {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        messageApi.success('已复制到剪贴板')
      } catch (err) {
        message.error('复制失败')
      }
      document.body.removeChild(textArea)
    }
  }
  
  // 根据屏幕宽度决定显示哪些列
  const getVisibleColumns = () => {
    const baseColumns: ColumnsType<any> = [
      {
        title: 'PO单号',
        dataIndex: 'parent_order_sn',
        key: 'parent_order_sn',
        width: 180,
        fixed: 'left' as const,
        ellipsis: true,
        render: (val: string) => {
          if (!val) return '-'
          return (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '4px',
              fontSize: '11px',
              fontFamily: 'monospace',
            }}>
              <span style={{ 
                overflow: 'hidden', 
                textOverflow: 'ellipsis', 
                whiteSpace: 'nowrap',
                flex: 1,
              }}>
                {val}
              </span>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined style={{ fontSize: '11px' }} />}
                onClick={(e) => {
                  e.stopPropagation()
                  copyToClipboard(val)
                }}
                style={{ 
                  padding: '0 4px', 
                  minWidth: 'auto', 
                  height: '20px', 
                  flexShrink: 0,
                  opacity: 0.7,
                }}
              />
            </div>
          )
        },
      },
      {
        title: '匹配订单数',
        dataIndex: 'matched_order_count',
        key: 'matched_order_count',
        width: 100,
        align: 'right' as const,
        render: (val: number, record: any) => {
          if (!val) return '-'
          const matchedParentSns = record.matched_parent_order_sns || []
          const isExactMatch = matchedParentSns.length === 1 && matchedParentSns[0] === record.parent_order_sn
          
          return (
            <Tooltip 
              title={
                <div>
                  <div>匹配的父订单号：</div>
                  {matchedParentSns.length > 0 ? (
                    matchedParentSns.map((sn: string, idx: number) => (
                      <div key={idx} style={{ marginTop: '4px' }}>
                        {sn === record.parent_order_sn ? (
                          <span style={{ color: '#52c41a' }}>✓ {sn}</span>
                        ) : (
                          <span style={{ color: '#f5222d' }}>✗ {sn}</span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div>无匹配的父订单号</div>
                  )}
                  {record.matched_order_sns && record.matched_order_sns.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <div>匹配的子订单号：</div>
                      {record.matched_order_sns.slice(0, 5).map((sn: string, idx: number) => (
                        <div key={idx} style={{ fontSize: '11px', marginTop: '2px' }}>{sn}</div>
                      ))}
                      {record.matched_order_sns.length > 5 && (
                        <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '2px' }}>
                          等{record.matched_order_sns.length}个订单
                        </div>
                      )}
                    </div>
                  )}
                </div>
              }
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                {isExactMatch ? (
                  <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '14px' }} />
                ) : (
                  <WarningOutlined style={{ color: '#faad14', fontSize: '14px' }} />
                )}
                <span>{val}</span>
              </div>
            </Tooltip>
          )
        },
      },
      {
        title: '包裹号',
        dataIndex: 'package_sn',
        key: 'package_sn',
        width: 150,
        ellipsis: true,
        render: (val: string) => {
          if (!val) return '-'
          return (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '4px',
              fontSize: '11px',
              fontFamily: 'monospace',
            }}>
              <span style={{ 
                overflow: 'hidden', 
                textOverflow: 'ellipsis', 
                whiteSpace: 'nowrap',
                flex: 1,
              }}>
                {val}
              </span>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined style={{ fontSize: '11px' }} />}
                onClick={(e) => {
                  e.stopPropagation()
                  copyToClipboard(val)
                }}
                style={{ 
                  padding: '0 4px', 
                  minWidth: 'auto', 
                  height: '20px', 
                  flexShrink: 0,
                  opacity: 0.7,
                }}
              />
            </div>
          )
        },
      },
    ]
    
    // 根据屏幕宽度决定是否显示某些列
    const screenWidth = window.innerWidth
    const showAllColumns = screenWidth >= 1400  // 宽度大于1400px时显示所有列
    const showMostColumns = screenWidth >= 1200  // 宽度大于1200px时显示大部分列
    
    const optionalColumns: ColumnsType<any> = [
      {
        title: '商品名称',
        dataIndex: 'product_name',
        key: 'product_name',
        width: 250,
        ellipsis: true,
        render: (val: string, record: any) => {
          if (!val) return '-'
          const displayText = val.length > 20 ? val.substring(0, 20) + '...' : val
          
          if (record.product_names && record.product_names.length > 1) {
            return (
              <Tooltip title={val}>
                <div>
                  <div>{displayText}</div>
                  <div style={{ fontSize: '12px', color: '#8b949e' }}>
                    等{record.product_names.length}个商品
                  </div>
                </div>
              </Tooltip>
            )
          }
          
          return (
            <Tooltip title={val}>
              <span>{displayText}</span>
            </Tooltip>
          )
        },
      },
      {
        title: 'SKU',
        dataIndex: 'sku',
        key: 'sku',
        width: 120,
        render: (val: string, record: any) => {
          if (record.skus && record.skus.length > 1) {
            return (
              <div>
                <div>{val}</div>
                <div style={{ fontSize: '12px', color: '#8b949e' }}>
                  等{record.skus.length}个SKU
                </div>
              </div>
            )
          }
          return val || '-'
        },
      },
      {
        title: '数量',
        dataIndex: 'quantity',
        key: 'quantity',
        width: 80,
        align: 'right' as const,
      },
    ]
    
    // 收入列（默认折叠，点击展开显示详细类目）
    const revenueColumn: ColumnsType<any>[0] = {
      title: '收入（回款）',
      dataIndex: 'revenue',
      key: 'revenue',
      width: 150,
      align: 'right' as const,
      render: (val: number, record: any) => {
        const isExpanded = revenueExpanded[record.parent_order_sn] || false
        return (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '4px',
                cursor: 'pointer',
                userSelect: 'none',
              }}
              onClick={() => onRevenueToggle(record.parent_order_sn)}
            >
              {isExpanded ? (
                <DownOutlined style={{ fontSize: '12px', color: '#8b949e' }} />
              ) : (
                <RightOutlined style={{ fontSize: '12px', color: '#8b949e' }} />
              )}
              <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                ¥{val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            {isExpanded && (
              <div style={{ 
                marginTop: '8px', 
                paddingTop: '8px', 
                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                flexDirection: 'row',
                gap: '16px',
                flexWrap: 'wrap',
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px', minWidth: '140px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ color: '#8b949e' }}>销售回款:</span>
                    <span style={{ fontWeight: 500 }}>{record.sales_collection ? `¥${record.sales_collection.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ color: '#8b949e' }}>销售回款已减优惠:</span>
                    <span style={{ fontWeight: 500 }}>{record.sales_collection_after_discount ? `¥${record.sales_collection_after_discount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ color: '#8b949e' }}>销售冲回:</span>
                    <span style={{ fontWeight: 500, color: record.sales_reversal < 0 ? '#f5222d' : undefined }}>
                      {record.sales_reversal ? `¥${record.sales_reversal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ color: '#8b949e' }}>运费回款:</span>
                    <span style={{ fontWeight: 500 }}>{record.shipping_collection ? `¥${record.shipping_collection.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                    <span style={{ color: '#8b949e' }}>运费回款已减优惠:</span>
                    <span style={{ fontWeight: 500 }}>{record.shipping_collection_after_discount ? `¥${record.shipping_collection_after_discount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      },
    }
    
    const costColumns: ColumnsType<any> = [
      {
        title: '进货成本',
        dataIndex: 'product_cost',
        key: 'product_cost',
        width: 120,
        align: 'right' as const,
        render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
      {
        title: '头程运费',
        dataIndex: 'shipping_cost',
        key: 'shipping_cost',
        width: 120,
        align: 'right' as const,
        render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
      {
        title: '收费重 (KG)',
        dataIndex: 'chargeable_weight',
        key: 'chargeable_weight',
        width: 100,
        align: 'right' as const,
        render: (val: number) => val !== undefined && val !== null ? `${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
      {
        title: '尾程运费',
        dataIndex: 'last_mile_cost',
        key: 'last_mile_cost',
        width: 120,
        align: 'right' as const,
        render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
      {
        title: '扣款',
        dataIndex: 'deduction',
        key: 'deduction',
        width: 100,
        align: 'right' as const,
        render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
      {
        title: '总成本',
        dataIndex: 'total_cost',
        key: 'total_cost',
        width: 120,
        align: 'right' as const,
        render: (val: number) => val ? `¥${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-',
      },
    ]
    
    const profitColumn: ColumnsType<any>[0] = {
      title: '利润 / 利润率',
      key: 'profit_and_rate',
      width: 180,
      align: 'right' as const,
      fixed: 'right' as const,
      render: (_: any, record: any) => {
        const profit = record.profit || 0
        const profitRate = record.profit_rate || 0
        const profitColor = profit >= 0 ? '#52c41a' : '#f5222d'
        
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
            <span style={{ 
              fontWeight: 'bold', 
              color: profitColor,
              fontSize: '14px',
            }}>
              ¥{profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span style={{ 
              fontWeight: 500, 
              color: profitColor,
              fontSize: '12px',
              opacity: 0.8,
            }}>
              {profitRate.toFixed(2)}%
            </span>
          </div>
        )
      },
    }
    
    // 根据屏幕宽度决定显示哪些列
    if (showAllColumns) {
      // 显示所有列
      return [...baseColumns, ...optionalColumns, revenueColumn, ...costColumns, profitColumn]
    } else if (showMostColumns) {
      // 显示大部分列，隐藏SKU
      return [...baseColumns, optionalColumns[0], optionalColumns[2], revenueColumn, ...costColumns, profitColumn]
    } else {
      // 只显示核心列：PO单号、匹配订单数、数量、收入、利润
      return [...baseColumns, optionalColumns[2], revenueColumn, profitColumn]
    }
  }
  
  // 使用useMemo根据屏幕宽度动态生成列
  const profitColumns = useMemo(() => getVisibleColumns(), [isMobile, revenueExpanded, onRevenueToggle])
  
  return (
    <div>
      {/* 文件上传区域 */}
      <Card 
        className="chart-card" 
        style={{ marginBottom: 24 }}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileExcelOutlined />
            <span>上传账单文件</span>
          </div>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card 
              size="small"
              style={{ 
                background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(82, 196, 26, 0.05) 100%)',
                border: '1px solid rgba(82, 196, 26, 0.3)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: 8,
                }}>
                  {collectionData.length > 0 ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <UploadOutlined />
                  )}
                  <span style={{ fontWeight: 500 }}>Temu结算表</span>
                </div>
                <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: 8 }}>
                  {collectionData.length > 0 ? `已上传 ${collectionData.length} 个PO单号` : '请上传Temu结算表文件（包含PO单号和5个结算字段）'}
                </div>
              </div>
              <Upload
                accept=".csv,.xlsx,.xls"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload('collection', file)
                  return false
                }}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />}
                >
                  {collectionData.length > 0 ? '重新上传Temu结算表' : '上传Temu结算表'}
                </Button>
              </Upload>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              size="small"
              style={{ 
                background: 'linear-gradient(135deg, rgba(24, 144, 255, 0.1) 0%, rgba(24, 144, 255, 0.05) 100%)',
                border: '1px solid rgba(24, 144, 255, 0.3)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: 8,
                }}>
                  {shippingData.length > 0 ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <UploadOutlined />
                  )}
                  <span style={{ fontWeight: 500 }}>头程运费表</span>
                </div>
                <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: 8 }}>
                  {shippingData.length > 0 ? `已上传 ${shippingData.length} 条记录` : '请上传头程运费表文件'}
                </div>
              </div>
              <Upload
                accept=".csv,.xlsx,.xls"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload('shipping', file)
                  return false
                }}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />}
                >
                  {shippingData.length > 0 ? '重新上传头程运费表' : '上传头程运费表'}
                </Button>
              </Upload>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              size="small"
              style={{ 
                background: 'linear-gradient(135deg, rgba(250, 173, 20, 0.1) 0%, rgba(250, 173, 20, 0.05) 100%)',
                border: '1px solid rgba(250, 173, 20, 0.3)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: 8,
                }}>
                  {lastMileShippingData.length > 0 ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <UploadOutlined />
                  )}
                  <span style={{ fontWeight: 500 }}>尾程运费表</span>
                </div>
                <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: 8 }}>
                  {lastMileShippingData.length > 0 ? `已上传 ${lastMileShippingData.length} 条记录` : '请上传尾程运费表文件'}
                </div>
              </div>
              <Upload
                accept=".csv,.xlsx,.xls"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload('lastMileShipping', file)
                  return false
                }}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />}
                >
                  {lastMileShippingData.length > 0 ? '重新上传尾程运费表' : '上传尾程运费表'}
                </Button>
              </Upload>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              size="small"
              style={{ 
                background: 'linear-gradient(135deg, rgba(245, 34, 45, 0.1) 0%, rgba(245, 34, 45, 0.05) 100%)',
                border: '1px solid rgba(245, 34, 45, 0.3)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: 8,
                }}>
                  {deductionData.length > 0 ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <UploadOutlined />
                  )}
                  <span style={{ fontWeight: 500 }}>延迟扣款表</span>
                </div>
                <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: 8 }}>
                  {deductionData.length > 0 ? `已上传 ${deductionData.length} 条记录` : '请上传延迟扣款表文件'}
                </div>
              </div>
              <Upload
                accept=".csv,.xlsx,.xls"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload('deduction', file)
                  return false
                }}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />}
                >
                  {deductionData.length > 0 ? '重新上传延迟扣款表' : '上传延迟扣款表'}
                </Button>
              </Upload>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              size="small"
              style={{ 
                background: 'linear-gradient(135deg, rgba(114, 46, 209, 0.1) 0%, rgba(114, 46, 209, 0.05) 100%)',
                border: '1px solid rgba(114, 46, 209, 0.3)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: 8,
                }}>
                  <UploadOutlined />
                  <span style={{ fontWeight: 500 }}>订单列表</span>
                </div>
                <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: 8 }}>
                  上传订单列表，匹配订单号并更新包裹号和收货地址信息
                </div>
              </div>
              <Upload
                accept=".csv,.xlsx,.xls"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload('orderList', file)
                  return false
                }}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />}
                >
                  上传订单列表
                </Button>
              </Upload>
            </Card>
          </Col>
        </Row>
        
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            loading={calculating}
            disabled={collectionData.length === 0 && shippingData.length === 0 && deductionData.length === 0}
            onClick={onCalculate}
            style={{
              background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
              border: 'none',
              height: '48px',
              padding: '0 32px',
              fontSize: '16px',
            }}
          >
            {calculating ? '计算中...' : '计算利润'}
          </Button>
        </div>
      </Card>
      
      {/* 统计摘要 */}
      {profitData?.summary && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总PO单数"
                value={profitData.summary.total_orders}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="匹配PO单数"
                value={profitData.summary.matched_orders}
                suffix="个"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总收入"
                value={profitData.summary.total_revenue}
                prefix="¥"
                precision={2}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总利润"
                value={profitData.summary.total_profit}
                prefix="¥"
                precision={2}
                valueStyle={{ 
                  color: profitData.summary.total_profit >= 0 ? '#52c41a' : '#f5222d' 
                }}
              />
            </Card>
          </Col>
        </Row>
      )}
      
      {/* 利润明细表格 */}
      {profitData?.items && (
        <Card 
          className="chart-card"
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <DollarOutlined />
              <span>利润明细</span>
            </div>
          }
        >
          <Table
            columns={profitColumns}
            dataSource={profitData.items}
            scroll={{ x: 'max-content' }}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            rowKey="parent_order_sn"
            className="profit-statement-table"
          />
        </Card>
      )}
      
      {/* 上传进度Modal */}
      <Modal
        open={uploadProgress.visible}
        closable={false}
        footer={null}
        centered
        maskClosable={false}
        width={400}
      >
        <div style={{ padding: '20px 0' }}>
          <div style={{ textAlign: 'center', marginBottom: 20, fontSize: 16, fontWeight: 500 }}>
            {uploadProgress.text}
          </div>
          <Progress
            percent={uploadProgress.percent}
            status={uploadProgress.status}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>
      </Modal>
    </div>
  )
}

export default Finance
