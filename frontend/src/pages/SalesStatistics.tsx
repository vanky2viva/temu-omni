import { useState, useMemo, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Select,
  Space,
  Tabs,
  Table,
  Tag,
  Button,
  Badge,
  Tooltip,
  DatePicker,
  Dropdown,
} from 'antd'
import type { MenuProps } from 'antd'
import type { Dayjs } from 'dayjs'
import {
  ShoppingOutlined,
  DollarOutlined,
  RiseOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  TeamOutlined,
  ReloadOutlined,
  FilterOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  TrophyOutlined,
  GlobalOutlined,
  PercentageOutlined,
} from '@ant-design/icons'
import LazyECharts from '@/components/LazyECharts'
import { shopApi, analyticsApi } from '@/services/api'
import dayjs from 'dayjs'

function SalesStatistics() {
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

  // 筛选条件
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)
  const [quickSelectValue, setQuickSelectValue] = useState<string>('all') // 默认选择"全部"
  const [shopIds, setShopIds] = useState<number[]>([])
  const [manager, setManager] = useState<string | undefined>()
  const [region, setRegion] = useState<string | undefined>()
  const [activeTab, setActiveTab] = useState('sku')

  const { RangePicker } = DatePicker

  const queryClient = useQueryClient()

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 刷新时间戳（用于强制刷新并传递 refresh_cache 参数）
  const [refreshTimestamp, setRefreshTimestamp] = useState<number>(0)
  
  // 获取销量总览数据 - 使用与仪表盘相同的数据源
  const { data: salesOverview } = useQuery({
    queryKey: ['sales-overview', dateRange, shopIds, manager, region, refreshTimestamp],
    queryFn: async () => {
      try {
        const params: any = {}
        // 使用 start_date 和 end_date 参数
        if (dateRange && dateRange[0] && dateRange[1]) {
          params.start_date = dateRange[0].format('YYYY-MM-DD')
          params.end_date = dateRange[1].format('YYYY-MM-DD')
        }
        // 如果没有日期范围，不传日期参数，后端会使用默认值（最近30天）
        if (shopIds.length > 0) params.shop_ids = shopIds
        if (manager) params.manager = manager
        if (region) params.region = region
        // 如果 refreshTimestamp > 0，说明是手动刷新，传递 refresh_cache 参数
        if (refreshTimestamp > 0) {
          params.refresh_cache = true
        }
        return await analyticsApi.getSalesOverview(params)
      } catch (error: any) {
        console.error('Failed to fetch sales overview:', error)
        // 返回空数据，避免页面崩溃
        return {
          total_quantity: 0,
          total_orders: 0,
          total_gmv: 0,
          total_profit: 0,
          daily_trends: [],
          shop_trends: {},
        }
      }
    },
  })

  // 获取SKU销量排行
  const { data: skuRanking, isLoading: skuLoading } = useQuery({
    queryKey: ['sku-sales-ranking', dateRange, shopIds, manager, region, refreshTimestamp],
    queryFn: async () => {
      try {
        const params: any = { limit: 100 }
        // 使用 start_date 和 end_date 参数
        if (dateRange && dateRange[0] && dateRange[1]) {
          params.start_date = dateRange[0].format('YYYY-MM-DD')
          params.end_date = dateRange[1].format('YYYY-MM-DD')
        }
        // 如果没有日期范围，不传日期参数，后端会使用默认值（最近30天）
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (manager) params.manager = manager
      if (region) params.region = region
        // 如果 refreshTimestamp > 0，说明是手动刷新，传递 refresh_cache 参数
        if (refreshTimestamp > 0) {
          params.refresh_cache = true
        }
        return await analyticsApi.getSkuSalesRanking(params)
      } catch (error: any) {
        console.error('Failed to fetch SKU ranking:', error)
        console.error('Error details:', error.response?.data || error.message)
        // 返回空数据而不是抛出错误，避免页面崩溃
        return { ranking: [] }
      }
    },
    enabled: activeTab === 'sku',
  })

  // 获取负责人销量统计
  const { data: managerSales, isLoading: managerLoading } = useQuery({
    queryKey: ['manager-sales', dateRange, shopIds, region, refreshTimestamp],
    queryFn: async () => {
      try {
        const params: any = {}
        if (dateRange && dateRange[0] && dateRange[1]) {
          params.start_date = dateRange[0].format('YYYY-MM-DD')
          params.end_date = dateRange[1].format('YYYY-MM-DD')
        }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (region) params.region = region
        // 如果 refreshTimestamp > 0，说明是手动刷新，传递 refresh_cache 参数
        if (refreshTimestamp > 0) {
          params.refresh_cache = true
        }
      return await analyticsApi.getManagerSales(params)
      } catch (error: any) {
        console.error('Failed to fetch manager sales:', error)
        console.error('Error details:', error.response?.data || error.message)
        // 返回空数据而不是抛出错误，避免页面崩溃
        return { managers: [] }
      }
    },
    enabled: activeTab === 'manager',
  })

  // 获取负责人选项
  const managerOptions = useMemo(() => {
    const managers = new Set<string>()
    if (!skuRanking?.ranking) return []
    skuRanking.ranking.forEach((item: any) => {
      if (item.manager && item.manager !== '-') {
        managers.add(item.manager)
      }
    })
    return Array.from(managers).map(m => ({ label: m, value: m }))
  }, [skuRanking])

  // 准备趋势图数据 - 使用与仪表盘相同的数据结构（订单量）
  const chartOption = useMemo(() => {
    if (!salesOverview) return null
    const dailyTrends = salesOverview.daily_trends || []
    const shopTrends = salesOverview.shop_trends || {}
    const dates = dailyTrends.map((item: any) => item.date)

    // 构建图表系列数据 - 与仪表盘一致
    const series: any[] = []
    
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
      z: 1,
    })
    
    // 各店铺订单量
    const colors = ['#1890ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2']
    const shopNames = Object.keys(shopTrends)
    
    shopNames.forEach((shopName, index) => {
      const shopData = shopTrends[shopName]
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

    return {
      backgroundColor: 'transparent',
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
        textStyle: { color: '#fff' },
      },
      legend: {
        data: ['总订单量', ...shopNames],
        bottom: 4,
        textStyle: { color: '#8b949e', fontSize: 10 },
        itemGap: 8,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '5%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: { lineStyle: { color: '#30363d' } },
        axisLabel: {
          color: '#8b949e',
          rotate: 45,
          formatter: (value: string) => dayjs(value).format('MM-DD'),
        },
      },
      yAxis: {
        type: 'value',
        name: '订单量（单）',
        nameTextStyle: { color: '#8b949e', fontSize: 11 },
        axisLine: { lineStyle: { color: '#30363d' } },
        axisLabel: { color: '#8b949e', fontSize: 11 },
        splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
      },
      series,
    }
  }, [salesOverview])

  // 准备每日销量表格数据（按日期倒序排序，最新日期在前）
  const dailySalesTableData = useMemo(() => {
    if (!salesOverview) return []
    const dailyTrends = salesOverview.daily_trends || []
    const shopTrends = salesOverview.shop_trends || {}
    const shopNames = Object.keys(shopTrends)

    const tableData = dailyTrends.map((day: any) => {
      const row: any = {
        key: day.date,
        date: day.date,
        totalOrders: day.orders || 0,  // 总订单数
        totalQuantity: day.quantity || 0,  // 总件数
      }
      
      // 添加每个店铺的订单数和件数
      shopNames.forEach((shopName) => {
        const shopData = shopTrends[shopName]
        const dayData = shopData.find((d: any) => d.date === day.date)
        row[`${shopName}_orders`] = dayData ? (dayData.orders || 0) : 0
        row[`${shopName}_quantity`] = dayData ? (dayData.quantity || 0) : 0
      })
      
      return row
    })
    
    // 按日期倒序排序（最新的日期在前）
    return tableData.sort((a: any, b: any) => {
      return dayjs(b.date).valueOf() - dayjs(a.date).valueOf()
    })
  }, [salesOverview])

  // 每日销量表格列配置
  const dailySalesColumns = useMemo(() => {
    if (!salesOverview) return []
    const shopTrends = salesOverview.shop_trends || {}
    const shopNames = Object.keys(shopTrends)

    // 移动端和桌面端的列宽和字体大小
    const dateWidth = isMobile ? 60 : 65
    const subColWidth = isMobile ? 65 : 70
    const fontSize = isMobile ? '12px' : '13px'

    const columns: any[] = [
      {
        title: '日期',
        dataIndex: 'date',
        key: 'date',
        width: dateWidth,
        fixed: isMobile ? 'left' as const : undefined,
        render: (date: string) => (
          <span style={{ color: '#c9d1d9', fontFamily: 'monospace', fontSize }}>
            {dayjs(date).format('MM-DD')}
          </span>
        ),
      },
    ]

    // 添加每个店铺的列（订单数和件数）
    shopNames.forEach((shopName) => {
      columns.push({
        title: shopName,
        key: shopName,
        align: 'center' as const,
        children: [
          {
            title: '订单数',
            dataIndex: `${shopName}_orders`,
            key: `${shopName}_orders`,
            width: subColWidth,
            align: 'right' as const,
            render: (value: number) => (
              <span style={{ 
                color: '#3273dc',
                fontWeight: 500,
                fontSize,
              }}>
                {value.toLocaleString()}
              </span>
            ),
          },
          {
            title: '件数',
            dataIndex: `${shopName}_quantity`,
            key: `${shopName}_quantity`,
            width: subColWidth,
            align: 'right' as const,
            render: (value: number) => (
              <span style={{ 
                color: '#48c774',
                fontWeight: 500,
                fontSize,
              }}>
                {value.toLocaleString()}
              </span>
            ),
          },
        ],
      })
    })

    // 添加总计列（订单数和件数）
    columns.push({
      title: '合计',
      key: 'total',
      align: 'center' as const,
      fixed: isMobile ? 'right' as const : undefined,
      children: [
        {
          title: '订单数',
          dataIndex: 'totalOrders',
          key: 'totalOrders',
          width: subColWidth,
          align: 'right' as const,
          render: (value: number) => (
            <span style={{ 
              color: '#3273dc',
              fontWeight: 600,
              fontSize,
            }}>
              {value.toLocaleString()}
            </span>
          ),
        },
        {
          title: '件数',
          dataIndex: 'totalQuantity',
          key: 'totalQuantity',
          width: subColWidth,
          align: 'right' as const,
          render: (value: number) => (
            <span style={{ 
              color: '#00d1b2',
              fontWeight: 600,
              fontSize,
            }}>
              {value.toLocaleString()}
            </span>
          ),
        },
      ],
    })

    return columns
  }, [salesOverview, isMobile])

  // SKU销量排行表格列
  const skuColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      align: 'center' as const,
      render: (rank: number) => (
        <Badge
          count={rank}
          style={{
            backgroundColor: rank <= 3 ? '#f14668' : '#00d1b2',
            boxShadow: '0 0 0 1px #fff inset',
          }}
        />
      ),
    },
    {
      title: (
        <Tooltip title="商品的SKU ID（非SKU货号）">
          <span>SKU ID</span>
        </Tooltip>
      ),
      dataIndex: 'sku',
      key: 'sku',
      width: 120,
      render: (sku: string) => (
        <span style={{ 
          fontFamily: 'monospace', 
          fontSize: '11px',
          color: '#00d1b2',
          fontWeight: 500,
        }}>
          {sku || '-'}
        </span>
      ),
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
      width: 200,
      render: (text: string) => (
        <Tooltip title={text}>
          <span style={{ color: '#c9d1d9', fontSize: '11px' }}>{text || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 100,
      render: (manager: string) => (
        <Tag color="cyan" style={{ fontSize: '11px', padding: '2px 8px' }}>{manager || '-'}</Tag>
      ),
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.quantity - b.quantity,
      render: (quantity: number) => (
        <span style={{ 
          fontSize: '11px',
          fontWeight: 600,
          color: '#48c774',
        }}>
          {quantity.toLocaleString()}
        </span>
      ),
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 80,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.orders - b.orders,
      render: (orders: number) => (
        <span style={{ 
          fontSize: '11px',
          fontWeight: 500,
          color: '#3273dc',
        }}>
          {orders.toLocaleString()}
        </span>
      ),
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => (a.gmv || 0) - (b.gmv || 0),
      render: (gmv: number | null | undefined) => {
        const value = gmv ?? 0
        return (
          <span style={{ color: '#ffdd57', fontSize: '11px', fontWeight: 500 }}>
            ¥{value.toLocaleString()}
          </span>
        )
      },
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => (a.profit || 0) - (b.profit || 0),
      render: (profit: number | null | undefined) => {
        const value = profit ?? 0
        return (
          <span style={{ 
            color: value >= 0 ? '#48c774' : '#f14668',
            fontWeight: 600,
            fontSize: '11px',
          }}>
            ¥{value.toLocaleString()}
          </span>
        )
      },
    },
  ]

  // 负责人销量表格列
  const managerColumns = [
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 150,
      render: (manager: string) => (
        <Space>
          <TeamOutlined style={{ color: '#3273dc' }} />
          <span style={{ fontWeight: 600, color: '#c9d1d9' }}>{manager}</span>
        </Space>
      ),
    },
    {
      title: '订单数',
      dataIndex: 'order_count',
      key: 'order_count',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.order_count - b.order_count,
      render: (count: number) => (
        <span style={{ 
          fontSize: '14px',
          fontWeight: 600,
          color: '#3273dc',
        }}>
          {count.toLocaleString()}
        </span>
      ),
    },
    {
      title: '销售件数',
      dataIndex: 'total_quantity',
      key: 'total_quantity',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.total_quantity - b.total_quantity,
      render: (quantity: number) => (
        <span style={{ 
          fontSize: '14px',
          fontWeight: 600,
          color: '#48c774',
        }}>
          {quantity.toLocaleString()}
        </span>
      ),
    },
    {
      title: 'GMV',
      dataIndex: 'total_gmv',
      key: 'total_gmv',
      width: 150,
      align: 'right' as const,
      render: (gmv: number | null) => gmv ? (
        <span style={{ color: '#ffdd57', fontWeight: 600 }}>
          ¥{gmv.toLocaleString()}
        </span>
      ) : (
        <span style={{ color: '#8b949e' }}>-</span>
      ),
    },
    {
      title: '利润',
      dataIndex: 'total_profit',
      key: 'total_profit',
      width: 150,
      align: 'right' as const,
      render: (profit: number | null) => {
        if (!profit && profit !== 0) return <span style={{ color: '#8b949e' }}>-</span>
        return (
          <span style={{ 
            color: profit >= 0 ? '#48c774' : '#f14668',
            fontWeight: 600,
          }}>
            ¥{profit.toLocaleString()}
          </span>
        )
      },
    },
  ]

  // 快速筛选菜单 - 日期范围快捷选项
  const quickFilterMenu: MenuProps['items'] = [
    {
      key: '7',
      label: '最近7天',
      icon: <CalendarOutlined />,
      onClick: () => setDateRange([dayjs().subtract(6, 'day'), dayjs()]) 
    },
    {
      key: '30',
      label: '最近30天',
      icon: <CalendarOutlined />,
      onClick: () => setDateRange([dayjs().subtract(29, 'day'), dayjs()]) 
    },
    {
      key: '90',
      label: '最近90天',
      icon: <CalendarOutlined />,
      onClick: () => setDateRange([dayjs().subtract(89, 'day'), dayjs()]) 
    },
    {
      key: 'clear', 
      label: '清除筛选', 
      icon: <CalendarOutlined />,
      onClick: () => setDateRange(null) 
    },
  ]

  // 自动刷新相关状态
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [countdown, setCountdown] = useState(300) // 5分钟 = 300秒
  const AUTO_REFRESH_INTERVAL = 300 // 5分钟（秒）

  // 刷新所有数据 - 立即重新获取并计算（清除缓存）
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    try {
      // 设置刷新时间戳，这会触发新的查询（queryKey 变化，包含 refreshTimestamp）
      // 新的查询会传递 refresh_cache=true 参数给后端
      const newTimestamp = Date.now()
      setRefreshTimestamp(newTimestamp)
      
      // 清除相关查询的缓存，强制重新获取
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['shops'] }),
        queryClient.invalidateQueries({ queryKey: ['sales-overview'] }),
        queryClient.invalidateQueries({ queryKey: ['sku-sales-ranking'] }),
        queryClient.invalidateQueries({ queryKey: ['manager-sales'] }),
      ])
      
      // 立即重新获取所有数据（使用新的 queryKey，会传递 refresh_cache=true）
      // 使用 refetchQueries 匹配所有相关查询，确保立即执行
      await Promise.all([
        queryClient.refetchQueries({ queryKey: ['shops'] }),
        queryClient.refetchQueries({ queryKey: ['sales-overview'] }),
        activeTab === 'sku' 
          ? queryClient.refetchQueries({ queryKey: ['sku-sales-ranking'] })
          : Promise.resolve(),
        activeTab === 'manager' 
          ? queryClient.refetchQueries({ queryKey: ['manager-sales'] })
          : Promise.resolve(),
      ])
      
      // 刷新成功后重置倒计时
      setCountdown(AUTO_REFRESH_INTERVAL)
    } catch (error) {
      console.error('刷新数据失败:', error)
    } finally {
      // 重置刷新状态
      setIsRefreshing(false)
    }
  }, [queryClient, activeTab, AUTO_REFRESH_INTERVAL])

  // 自动刷新和倒计时：使用同一个定时器管理
  useEffect(() => {
    // 自动刷新定时器：每5分钟执行一次
    const autoRefreshInterval = setInterval(() => {
      handleRefresh()
    }, AUTO_REFRESH_INTERVAL * 1000)

    // 倒计时定时器：每秒更新一次（刷新时暂停）
    const countdownInterval = setInterval(() => {
      // 如果正在刷新，暂停倒计时
      if (isRefreshing) {
        return
      }
      
      setCountdown((prev) => {
        if (prev <= 1) {
          // 倒计时到0时，重置为初始值（自动刷新会由上面的定时器触发）
          return AUTO_REFRESH_INTERVAL
        }
        return prev - 1
      })
    }, 1000)

    return () => {
      clearInterval(autoRefreshInterval)
      clearInterval(countdownInterval)
    }
  }, [handleRefresh, AUTO_REFRESH_INTERVAL, isRefreshing])

  // 格式化倒计时显示（MM:SS）
  const formatCountdown = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 计算核心指标
  const totalQuantity = salesOverview?.total_quantity || 0
  const totalOrders = salesOverview?.total_orders || 0
  const totalGmv = salesOverview?.total_gmv || 0
  const totalProfit = salesOverview?.total_profit ?? null
  const profitMargin = totalGmv > 0 && totalProfit !== null && totalProfit !== undefined 
    ? ((totalProfit / totalGmv) * 100).toFixed(2) 
    : '0.00'
  const avgOrderValue = totalOrders > 0 && totalGmv > 0 
    ? (totalGmv / totalOrders).toFixed(2) 
    : '0.00'

  return (
    <div className="bulma-section bulma-grid-bg" style={{ 
      padding: isMobile ? '8px' : '12px',
      background: 'linear-gradient(135deg, #0d1117 0%, #161b22 100%)',
      height: '100vh',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* 页面头部 - Bulma 风格 */}
      <div style={{ 
        marginBottom: isMobile ? 8 : 12,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: isMobile ? 'wrap' : 'nowrap',
        gap: 8,
        flexShrink: 0,
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 className="bulma-title" style={{ 
            margin: 0,
            fontSize: isMobile ? '18px' : '24px',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <RocketOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '18px' : '24px' }} />
            <span style={{
              background: 'linear-gradient(135deg, #00d1b2 0%, #3273dc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            销售数据分析
            </span>
          </h1>
        </div>
        <Space wrap direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
          <Tooltip title={isRefreshing ? "正在刷新数据..." : "刷新数据"}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={isRefreshing}
              disabled={isRefreshing}
              className="bulma-button"
              block={isMobile}
            >
              {isRefreshing ? '刷新中...' : '刷新'}
            </Button>
          </Tooltip>
          {!isMobile && (
            <span style={{ 
              color: isRefreshing ? '#00d1b2' : '#8b949e', 
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}>
              <span style={{ color: isRefreshing ? '#00d1b2' : '#8b949e' }}>⏱</span>
              <span>{isRefreshing ? '正在刷新...' : `自动刷新: ${formatCountdown(countdown)}`}</span>
            </span>
          )}
          {isMobile && (
            <div style={{ 
              color: isRefreshing ? '#00d1b2' : '#8b949e', 
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              width: '100%',
              justifyContent: 'center',
            }}>
              <span style={{ color: isRefreshing ? '#00d1b2' : '#8b949e' }}>⏱</span>
              <span>{isRefreshing ? '正在刷新...' : `自动刷新: ${formatCountdown(countdown)}`}</span>
            </div>
          )}
          <Dropdown menu={{ items: quickFilterMenu }} placement="bottomRight">
            <Button
              icon={<FilterOutlined />}
              className="bulma-button"
              block={isMobile}
            >
              快速筛选
            </Button>
          </Dropdown>
        </Space>
      </div>

      {/* 筛选区域 - Bulma Card 风格 */}
      <div className="bulma-card" style={{ 
          marginBottom: isMobile ? 8 : 12,
        padding: isMobile ? '8px' : '12px',
        flexShrink: 0,
      }}>
        <Space 
          size={isMobile ? "middle" : "large"} 
          wrap 
          direction={isMobile ? "vertical" : "horizontal"}
          style={{ width: '100%' }}
        >
          <Space direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: isMobile ? '100%' : 'auto' }}>
              <CalendarOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '16px' : '14px' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 500, fontSize: isMobile ? '14px' : '13px', whiteSpace: 'nowrap' }}>时间范围：</span>
            </div>
            {/* 快捷时间选择下拉框 */}
            <Select
              placeholder="快捷选择"
              value={quickSelectValue}
              style={{ width: isMobile ? '100%' : 120 }}
              onChange={(value) => {
                setQuickSelectValue(value)
                
                if (value === 'all' || !value) {
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
                { label: '全部', value: 'all' },
                { label: '今天', value: 'today' },
                { label: '昨天', value: 'yesterday' },
                { label: '最近7天', value: 'last7days' },
                { label: '最近30天', value: 'last30days' },
                { label: '本月', value: 'thisMonth' },
                { label: '上月', value: 'lastMonth' },
              ]}
              className="bulma-input"
            />
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                setDateRange(dates)
                // 当手动选择日期时，如果清空则设置为"全部"
                if (!dates) {
                  setQuickSelectValue('all')
                }
                // 手动选择日期时，不自动更新快捷选择的值，保持当前选择或显示为自定义
              }}
              format="YYYY-MM-DD"
              placeholder={['开始日期', '结束日期']}
              allowClear
              style={{ width: isMobile ? '100%' : 240 }}
              className="bulma-input"
            />
          </Space>

          <Space direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: isMobile ? '100%' : 'auto' }}>
              <AppstoreOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '16px' : '14px' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 500, fontSize: isMobile ? '14px' : '13px', whiteSpace: 'nowrap' }}>店铺：</span>
            </div>
            <Select
              mode="multiple"
              style={{ width: isMobile ? '100%' : 200 }}
              placeholder="全部店铺"
              allowClear
              value={shopIds}
              onChange={setShopIds}
              className="bulma-input"
              options={shops?.map((shop: any) => ({
                label: shop.shop_name,
                value: shop.id,
              }))}
            />
          </Space>

          <Space direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: isMobile ? '100%' : 'auto' }}>
              <TeamOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '16px' : '14px' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 500, fontSize: isMobile ? '14px' : '13px', whiteSpace: 'nowrap' }}>负责人：</span>
            </div>
            <Select
              style={{ width: isMobile ? '100%' : 150 }}
              placeholder="全部负责人"
              allowClear
              value={manager}
              onChange={setManager}
              className="bulma-input"
              options={managerOptions}
            />
          </Space>

          <Space direction={isMobile ? "vertical" : "horizontal"} style={{ width: isMobile ? '100%' : 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: isMobile ? '100%' : 'auto' }}>
              <GlobalOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '16px' : '14px' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 500, fontSize: isMobile ? '14px' : '13px', whiteSpace: 'nowrap' }}>地区：</span>
            </div>
            <Select
              style={{ width: isMobile ? '100%' : 120 }}
              placeholder="全部地区"
              allowClear
              value={region}
              onChange={setRegion}
              className="bulma-input"
              options={[
                { label: '美国', value: 'us' },
                { label: '欧洲', value: 'eu' },
                { label: '全球', value: 'global' },
              ]}
            />
          </Space>

          </Space>
      </div>

      {/* 核心指标卡片 - Bulma Card 风格 */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, 1fr)',
        gap: isMobile ? 8 : 10,
        marginBottom: isMobile ? 8 : 12,
        flexShrink: 0,
      }}>
        {/* 总销量 */}
        <div className="bulma-card bulma-glow" style={{ 
          padding: isMobile ? '10px' : '14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            background: 'linear-gradient(135deg, rgba(0, 209, 178, 0.1) 0%, transparent 100%)',
            borderRadius: '50%',
            transform: 'translate(30%, -30%)',
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: isMobile ? 6 : 8,
            }}>
              <span style={{ 
                color: '#8b949e', 
                fontSize: isMobile ? '11px' : '12px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <ShoppingOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '12px' : '12px' }} />
                  总销量
                </span>
              <ThunderboltOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '14px' : '16px', opacity: 0.3 }} />
            </div>
            <div className="bulma-stat-value" style={{ 
              fontSize: isMobile ? '18px' : '24px',
              marginBottom: isMobile ? 4 : 4,
            }}>
              {totalQuantity.toLocaleString()}
            </div>
            <div style={{ color: '#8b949e', fontSize: isMobile ? '10px' : '11px' }}>件</div>
          </div>
        </div>

        {/* 总订单数 */}
        <div className="bulma-card bulma-glow" style={{ 
          padding: isMobile ? '10px' : '14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            background: 'linear-gradient(135deg, rgba(50, 115, 220, 0.1) 0%, transparent 100%)',
            borderRadius: '50%',
            transform: 'translate(30%, -30%)',
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: isMobile ? 6 : 8,
            }}>
              <span style={{ 
                color: '#8b949e', 
                fontSize: isMobile ? '11px' : '12px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <BarChartOutlined style={{ color: '#3273dc', fontSize: isMobile ? '12px' : '12px' }} />
                  总订单数
                </span>
              <CheckCircleOutlined style={{ color: '#3273dc', fontSize: isMobile ? '14px' : '16px', opacity: 0.3 }} />
            </div>
            <div className="bulma-stat-value" style={{ 
              fontSize: isMobile ? '18px' : '24px',
              marginBottom: isMobile ? 4 : 4,
              background: 'linear-gradient(135deg, #3273dc 0%, #2366d1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {totalOrders.toLocaleString()}
            </div>
            <div style={{ color: '#8b949e', fontSize: isMobile ? '10px' : '11px' }}>单</div>
          </div>
        </div>

        {/* GMV */}
        <div className="bulma-card bulma-glow" style={{ 
          padding: isMobile ? '10px' : '14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            background: 'linear-gradient(135deg, rgba(255, 221, 87, 0.1) 0%, transparent 100%)',
            borderRadius: '50%',
            transform: 'translate(30%, -30%)',
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: isMobile ? 6 : 8,
            }}>
              <span style={{ 
                color: '#8b949e', 
                fontSize: isMobile ? '11px' : '12px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <DollarOutlined style={{ color: '#ffdd57', fontSize: isMobile ? '12px' : '12px' }} />
                  GMV
                </span>
              <RiseOutlined style={{ color: '#ffdd57', fontSize: isMobile ? '14px' : '16px', opacity: 0.3 }} />
            </div>
            <div className="bulma-stat-value" style={{ 
              fontSize: isMobile ? '18px' : '24px',
              marginBottom: isMobile ? 4 : 4,
              background: 'linear-gradient(135deg, #ffdd57 0%, #ffd83d 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {totalGmv > 0 ? `¥${(totalGmv / 1000).toFixed(1)}k` : '暂无数据'}
            </div>
            <div style={{ color: '#8b949e', fontSize: isMobile ? '10px' : '11px' }}>
              {totalGmv > 0 && `平均: ¥${avgOrderValue}`}
            </div>
          </div>
        </div>

        {/* 利润 */}
        <div className="bulma-card bulma-glow" style={{ 
          padding: isMobile ? '10px' : '14px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '100px',
            height: '100px',
            background: totalProfit >= 0
              ? 'linear-gradient(135deg, rgba(72, 199, 116, 0.1) 0%, transparent 100%)'
              : 'linear-gradient(135deg, rgba(241, 70, 104, 0.1) 0%, transparent 100%)',
            borderRadius: '50%',
            transform: 'translate(30%, -30%)',
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: isMobile ? 6 : 8,
            }}>
              <span style={{ 
                color: '#8b949e', 
                fontSize: isMobile ? '11px' : '12px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <TrophyOutlined style={{ 
                  color: totalProfit >= 0 ? '#48c774' : '#f14668',
                  fontSize: isMobile ? '12px' : '12px',
                }} />
                  利润
                </span>
              <TrophyOutlined style={{ 
                color: totalProfit >= 0 ? '#48c774' : '#f14668', 
                fontSize: isMobile ? '14px' : '16px',
                opacity: 0.3 
              }} />
            </div>
            <div className="bulma-stat-value" style={{ 
              fontSize: isMobile ? '18px' : '24px',
              marginBottom: isMobile ? 4 : 4,
              background: totalProfit >= 0
                ? 'linear-gradient(135deg, #48c774 0%, #3ec46d 100%)'
                : 'linear-gradient(135deg, #f14668 0%, #ef2e55 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              {totalProfit !== null && totalProfit !== undefined 
                ? `¥${(totalProfit / 1000).toFixed(1)}k` 
                : '暂无数据'}
            </div>
            <div style={{ 
              color: '#8b949e', 
              fontSize: isMobile ? '10px' : '11px',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}>
              {totalProfit !== null && totalProfit !== undefined && (
                <>
                  <PercentageOutlined style={{ fontSize: isMobile ? '9px' : '10px' }} />
                  {profitMargin}%
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 销量趋势分析 - 左侧表格，右侧图表 */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : '0.8fr 1.2fr',
        gap: isMobile ? 6 : 8,
        marginBottom: isMobile ? 8 : 12,
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
      }}>
        {/* 左侧：每日销量表格 */}
        <div className="bulma-card" style={{ 
          padding: isMobile ? '4px' : '6px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          height: '100%',
        }}>
          <header style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: 4,
            paddingBottom: 4,
            borderBottom: '1px solid #30363d',
            flexShrink: 0,
          }}>
            <BarChartOutlined style={{ color: '#00d1b2', fontSize: '11px', marginRight: 4 }} />
            <span style={{ 
              color: '#c9d1d9', 
              fontWeight: 600,
              fontSize: '11px',
            }}>
              每日店铺订单与销量
            </span>
          </header>
          <div style={{ 
            flex: 1,
            overflowY: 'auto', 
            overflowX: isMobile ? 'auto' : 'hidden',
            WebkitOverflowScrolling: 'touch',
            touchAction: 'pan-x pan-y',
            minHeight: 0,
          }}>
            <Table
              columns={dailySalesColumns}
              dataSource={dailySalesTableData}
              pagination={false}
              scroll={{ 
                y: 'calc(100vh - 650px)',
                x: isMobile ? 'max-content' : undefined,
              }}
              size={isMobile ? "small" : "small"}
              style={{ background: 'transparent', width: '100%', minWidth: isMobile ? '600px' : 'auto' }}
              className="compact-table"
              components={{
                body: {
                  cell: (props: any) => (
                    <td {...props} style={{ 
                      ...props.style, 
                      padding: isMobile ? '6px 8px' : '2px 6px', 
                      lineHeight: '1.4',
                      fontSize: isMobile ? '12px' : '13px',
                    }} />
                  ),
                  row: (props: any) => (
                    <tr {...props} style={{ 
                      ...props.style, 
                      height: isMobile ? '40px' : '32px',
                      minHeight: isMobile ? '40px' : '32px',
                    }} />
                  ),
                },
                header: {
                  cell: (props: any) => (
                    <th {...props} style={{ 
                      ...props.style, 
                      padding: isMobile ? '8px 6px' : '4px 6px', 
                      fontSize: isMobile ? '11px' : '13px', 
                      fontWeight: 600, 
                      lineHeight: '1.4',
                      whiteSpace: 'nowrap',
                    }} />
                  ),
                },
              }}
            />
          </div>
        </div>

        {/* 右侧：销量趋势图表 */}
      {chartOption && (
          <div className="bulma-card" style={{ 
            padding: isMobile ? '4px' : '6px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            height: '100%',
          }}>
            <header style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 4,
              paddingBottom: 4,
              borderBottom: '1px solid #30363d',
              flexShrink: 0,
            }}>
              <LineChartOutlined style={{ color: '#00d1b2', fontSize: isMobile ? '11px' : '12px', marginRight: 4 }} />
              <span style={{ 
                color: '#c9d1d9', 
                fontWeight: 600,
                fontSize: isMobile ? '11px' : '12px',
              }}>
                店铺业绩对比
              </span>
            </header>
            <div style={{ flex: 1, minHeight: 0, marginTop: '-4px' }}>
          <LazyECharts 
            option={chartOption} 
                style={{ height: '100%', minHeight: '200px' }}
            opts={{ renderer: 'svg' }}
          />
            </div>
          </div>
        )}
      </div>

      {/* Tab切换 - Bulma Card 风格 */}
      <div className="bulma-card" style={{ 
        padding: isMobile ? '8px' : '12px',
        flex: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
          items={[
            {
              key: 'sku',
              label: (
                <Space>
                  <AppstoreOutlined />
                  <span>SKU销量排行</span>
                </Space>
              ),
              children: (
                <div style={{ padding: 0, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <Table
                  columns={skuColumns}
                  dataSource={skuRanking?.ranking || []}
                  rowKey={(record, index) => record?.sku || record?.rank?.toString() || `sku-${index}`}
                  loading={skuLoading}
                  pagination={{
                    pageSize: 15,
                    showSizeChanger: true,
                    showTotal: (total) => (
                      <span style={{ color: '#8b949e' }}>
                          共 <strong style={{ color: '#00d1b2' }}>{total}</strong> 条记录
                      </span>
                    ),
                  }}
                    style={{ background: 'transparent', flex: 1 }}
                    scroll={{ y: 'calc(100vh - 750px)' }}
                />
                </div>
              ),
            },
            {
              key: 'manager',
              label: (
                <Space>
                  <TeamOutlined />
                  <span>负责人业绩</span>
                </Space>
              ),
              children: (
                <div style={{ padding: 0, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                  <Table
                    columns={managerColumns}
                    dataSource={managerSales?.managers || []}
                    rowKey="manager"
                    loading={managerLoading}
                    pagination={{
                      pageSize: 15,
                      showSizeChanger: true,
                      showTotal: (total) => (
                        <span style={{ color: '#8b949e' }}>
                          共 <strong style={{ color: '#00d1b2' }}>{total}</strong> 条记录
                        </span>
                      ),
                    }}
                    style={{ background: 'transparent', flex: 1 }}
                    scroll={{ y: 'calc(100vh - 750px)' }}
                  />
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  )
}

export default SalesStatistics
