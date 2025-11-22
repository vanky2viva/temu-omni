import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Input,
  Space,
  Tabs,
  Table,
  Tag,
  Button,
  Badge,
  Tooltip,
  Dropdown,
} from 'antd'
import type { MenuProps } from 'antd'
import {
  ShoppingOutlined,
  DollarOutlined,
  RiseOutlined,
  SearchOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  TeamOutlined,
  ReloadOutlined,
  FilterOutlined,
  ExportOutlined,
  RocketOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  TrophyOutlined,
  GlobalOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import axios from 'axios'
import { shopApi } from '@/services/api'
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
  const [days, setDays] = useState(30)
  const [shopIds, setShopIds] = useState<number[]>([])
  const [manager, setManager] = useState<string | undefined>()
  const [region, setRegion] = useState<string | undefined>()
  const [skuSearch, setSkuSearch] = useState<string>('')
  const [activeTab, setActiveTab] = useState('spu')

  // 获取店铺列表
  const { data: shops, refetch: refetchShops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取销量总览数据
  const { data: salesOverview, isLoading: overviewLoading, refetch: refetchOverview } = useQuery({
    queryKey: ['sales-overview', days, shopIds, manager, region, skuSearch],
    queryFn: async () => {
      const params: any = { days }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (manager) params.manager = manager
      if (region) params.region = region
      if (skuSearch) params.sku_search = skuSearch
      const response = await axios.get('/api/analytics/sales-overview', { params })
      return response.data
    },
  })

  // 获取SPU销量排行
  const { data: spuRanking, isLoading: spuLoading, refetch: refetchSpu } = useQuery({
    queryKey: ['spu-sales-ranking', days, shopIds, manager, region, skuSearch],
    queryFn: async () => {
      const params: any = { days, limit: 100 }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (manager) params.manager = manager
      if (region) params.region = region
      if (skuSearch) params.sku_search = skuSearch
      const response = await axios.get('/api/analytics/spu-sales-ranking', { params })
      return response.data
    },
    enabled: activeTab === 'spu',
  })

  // 获取负责人销量统计
  const { data: managerSales, isLoading: managerLoading, refetch: refetchManager } = useQuery({
    queryKey: ['manager-sales', days, shopIds, region],
    queryFn: async () => {
      const params: any = { days }
      if (shopIds.length > 0) params.shop_ids = shopIds
      if (region) params.region = region
      const response = await axios.get('/api/analytics/manager-sales', { params })
      return response.data
    },
    enabled: activeTab === 'manager',
  })

  // 获取负责人选项（基于当前数据）
  const managerOptions = useMemo(() => {
    const managers = new Set<string>()
    // 从SPU销量排行数据中获取负责人列表
    if (!spuRanking?.ranking) return []
    spuRanking.ranking.forEach((item: any) => {
      if (item.manager && item.manager !== '-') {
        managers.add(item.manager)
      }
    })
    return Array.from(managers).map(m => ({ label: m, value: m }))
  }, [spuRanking])

  // 准备趋势图数据
  const chartOption = useMemo(() => {
    if (!salesOverview) return null
    const dailyTrends = salesOverview.daily_trends || []
    const shopTrends = salesOverview.shop_trends || {}

    const dates = dailyTrends.map((item: any) => item.date)
    const totalQuantities = dailyTrends.map((item: any) => item.quantity)

    // 构建每个店铺的系列数据
    const shopSeries = Object.keys(shopTrends).map((shopName, index) => {
      const shopData = shopTrends[shopName]
      const quantities: number[] = []
      dates.forEach((date: string) => {
        const dayData = shopData.find((d: any) => d.date === date)
        quantities.push(dayData ? dayData.quantity : 0)
      })

      const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']
      return {
        name: shopName,
        type: 'line' as const,
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
      }
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
        textStyle: {
          color: '#fff',
        },
      },
      legend: {
        data: ['总销量', ...Object.keys(shopTrends)],
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
        data: dates,
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
      series: [
        {
          name: '总销量',
          type: 'line',
          data: totalQuantities,
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
        },
        ...shopSeries,
      ] as any,
    }
  }, [salesOverview])

  // 负责人业绩图表配置
  const managerChartOption = useMemo(() => {
    if (!managerSales?.managers || managerSales.managers.length === 0) return null

    const managers = managerSales.managers
    const allDates = new Set<string>()
    
    managers.forEach((mgr: any) => {
      mgr.daily_trends?.forEach((day: any) => {
        allDates.add(day.date)
      })
    })
    
    const sortedDates = Array.from(allDates).sort()

    const series = managers.map((mgr: any) => {
      const orders: number[] = []
      sortedDates.forEach((date: string) => {
        const dayData = mgr.daily_trends?.find((d: any) => d.date === date)
        orders.push(dayData ? dayData.orders : 0)
      })

      return {
        name: mgr.manager,
        type: 'line' as const,
        data: orders,
        smooth: true,
        lineStyle: {
          width: 2,
        },
        areaStyle: {
          opacity: 0.15,
        },
      }
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
        textStyle: {
          color: '#fff',
        },
      },
      legend: {
        data: managers.map((m: any) => m.manager),
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
        data: sortedDates,
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
        name: '订单数（单）',
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
      series: series as any,
    }
  }, [managerSales])

  // SPU销量排行表格列
  const spuColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      align: 'center' as const,
      render: (rank: number) => (
        <Badge
          count={rank}
          style={{
            backgroundColor: rank <= 3 ? '#f5222d' : '#1890ff',
            boxShadow: '0 0 0 1px #fff inset',
          }}
        />
      ),
    },
    {
      title: 'SPU ID',
      dataIndex: 'spu_id',
      key: 'spu_id',
      width: 150,
      render: (spuId: string) => (
        <span style={{ 
          fontFamily: 'monospace', 
          fontSize: '13px',
          color: '#58a6ff',
          fontWeight: 500,
        }}>
          {spuId || '-'}
        </span>
      ),
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
      width: 300,
      render: (text: string) => (
        <Tooltip title={text}>
          <span style={{ color: '#c9d1d9' }}>{text || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 120,
      render: (manager: string) => (
        <Tag icon={<TeamOutlined />} color="blue">
          {manager || '-'}
        </Tag>
      ),
    },
    {
      title: 'SKU数量',
      dataIndex: 'sku_count',
      key: 'sku_count',
      width: 100,
      align: 'center' as const,
      render: (count: number) => (
        <Badge count={count} showZero style={{ backgroundColor: '#52c41a' }} />
      ),
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.quantity - b.quantity,
      render: (quantity: number) => (
        <span style={{ 
          fontSize: '14px',
          fontWeight: 600,
          color: '#52c41a',
        }}>
          {quantity.toLocaleString()}
        </span>
      ),
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.orders - b.orders,
      render: (orders: number) => (
        <span style={{ 
          fontSize: '14px',
          fontWeight: 500,
          color: '#1890ff',
        }}>
          {orders.toLocaleString()}
        </span>
      ),
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 120,
      align: 'right' as const,
      render: (gmv: number | null) => gmv ? (
        <span style={{ color: '#faad14' }}>${gmv.toLocaleString()}</span>
      ) : (
        <span style={{ color: '#8b949e' }}>-</span>
      ),
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 120,
      align: 'right' as const,
      render: (profit: number | null) => {
        if (!profit && profit !== 0) return <span style={{ color: '#8b949e' }}>-</span>
        return (
          <span style={{ 
            color: profit >= 0 ? '#52c41a' : '#f5222d',
            fontWeight: 600,
          }}>
            ${profit.toLocaleString()}
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
          <TeamOutlined style={{ color: '#1890ff' }} />
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
          color: '#1890ff',
        }}>
          {count.toLocaleString()}
        </span>
      ),
    },
    {
      title: '总销量',
      dataIndex: 'total_quantity',
      key: 'total_quantity',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.total_quantity - b.total_quantity,
      render: (quantity: number) => (
        <span style={{ 
          fontSize: '14px',
          fontWeight: 600,
          color: '#52c41a',
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
        <span style={{ color: '#faad14', fontWeight: 600 }}>
          ${gmv.toLocaleString()}
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
            color: profit >= 0 ? '#52c41a' : '#f5222d',
            fontWeight: 600,
          }}>
            ${profit.toLocaleString()}
          </span>
        )
      },
    },
  ]

  // 快速筛选菜单
  const quickFilterMenu: MenuProps['items'] = [
    {
      key: '7',
      label: '最近7天',
      icon: <CalendarOutlined />,
      onClick: () => setDays(7),
    },
    {
      key: '30',
      label: '最近30天',
      icon: <CalendarOutlined />,
      onClick: () => setDays(30),
    },
    {
      key: '90',
      label: '最近90天',
      icon: <CalendarOutlined />,
      onClick: () => setDays(90),
    },
    {
      key: '180',
      label: '最近180天',
      icon: <CalendarOutlined />,
      onClick: () => setDays(180),
    },
  ]

  // 刷新所有数据
  const handleRefresh = () => {
    refetchOverview()
    if (activeTab === 'spu') {
      refetchSpu()
    } else if (activeTab === 'manager') {
      refetchManager()
    }
  }

  return (
    <div style={{ 
      padding: '24px',
      background: 'linear-gradient(135deg, #0d1117 0%, #161b22 100%)',
      minHeight: '100vh',
    }}>
      {/* 页面头部 */}
      <div style={{ 
        marginBottom: 24,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <h1 style={{ 
            margin: 0,
            fontSize: '28px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            <RocketOutlined style={{ marginRight: 12, color: '#1890ff' }} />
            销售数据分析
          </h1>
          <p style={{ 
            margin: '8px 0 0 0',
            color: '#8b949e',
            fontSize: '14px',
          }}>
            实时监控销售业绩，洞察业务趋势
          </p>
        </div>
        <Space>
          <Tooltip title="刷新数据">
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              style={{
                background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                border: 'none',
                boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
              }}
            >
              刷新
            </Button>
          </Tooltip>
          <Dropdown menu={{ items: quickFilterMenu }} placement="bottomRight">
            <Button
              icon={<FilterOutlined />}
              style={{
                borderColor: '#30363d',
                color: '#c9d1d9',
              }}
            >
              快速筛选
            </Button>
          </Dropdown>
        </Space>
      </div>

      {/* 筛选区域 */}
      <Card 
        style={{ 
          marginBottom: 24,
          background: 'rgba(22, 27, 34, 0.8)',
          border: '1px solid #30363d',
          borderRadius: '12px',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}
        bodyStyle={{ padding: '20px' }}
      >
        <Space size="large" wrap style={{ width: '100%' }}>
          <Space>
            <CalendarOutlined style={{ color: '#1890ff' }} />
            <span style={{ color: '#c9d1d9', fontWeight: 500 }}>时间范围：</span>
            <Select
              style={{ width: 150 }}
              value={days}
              onChange={setDays}
              options={[
                { label: '最近7天', value: 7 },
                { label: '最近30天', value: 30 },
                { label: '最近90天', value: 90 },
                { label: '最近180天', value: 180 },
              ]}
              suffixIcon={<CalendarOutlined />}
            />
          </Space>

          <Space>
            <AppstoreOutlined style={{ color: '#1890ff' }} />
            <span style={{ color: '#c9d1d9', fontWeight: 500 }}>店铺：</span>
            <Select
              mode="multiple"
              style={{ width: 200 }}
              placeholder="全部店铺"
              allowClear
              value={shopIds}
              onChange={setShopIds}
              options={shops?.map((shop: any) => ({
                label: shop.shop_name,
                value: shop.id,
              }))}
              suffixIcon={<AppstoreOutlined />}
            />
          </Space>

          <Space>
            <TeamOutlined style={{ color: '#1890ff' }} />
            <span style={{ color: '#c9d1d9', fontWeight: 500 }}>负责人：</span>
            <Select
              style={{ width: 150 }}
              placeholder="全部负责人"
              allowClear
              value={manager}
              onChange={setManager}
              options={managerOptions}
              suffixIcon={<TeamOutlined />}
            />
          </Space>

          <Space>
            <GlobalOutlined style={{ color: '#1890ff' }} />
            <span style={{ color: '#c9d1d9', fontWeight: 500 }}>地区：</span>
            <Select
              style={{ width: 120 }}
              placeholder="全部地区"
              allowClear
              value={region}
              onChange={setRegion}
              options={[
                { label: '美国', value: 'us' },
                { label: '欧洲', value: 'eu' },
                { label: '全球', value: 'global' },
              ]}
              suffixIcon={<GlobalOutlined />}
            />
          </Space>

          <Space>
            <SearchOutlined style={{ color: '#1890ff' }} />
            <Input
              style={{ width: 200 }}
              placeholder="搜索SKU关键词"
              prefix={<SearchOutlined />}
              value={skuSearch}
              onChange={(e) => setSkuSearch(e.target.value)}
              allowClear
            />
          </Space>
        </Space>
      </Card>

      {/* 总览卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, rgba(24, 144, 255, 0.1) 0%, rgba(24, 144, 255, 0.05) 100%)',
              border: '1px solid rgba(24, 144, 255, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 4px 16px rgba(24, 144, 255, 0.2)',
              transition: 'all 0.3s ease',
            }}
            bodyStyle={{ padding: '20px' }}
          >
            <Statistic
              title={
                <span style={{ color: '#8b949e', fontSize: '14px' }}>
                  <ShoppingOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  总销量
                </span>
              }
              value={salesOverview?.total_quantity || 0}
              suffix="件"
              valueStyle={{ 
                color: '#1890ff',
                fontSize: '24px',
                fontWeight: 700,
              }}
              prefix={<ThunderboltOutlined style={{ color: '#1890ff', fontSize: '20px' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(82, 196, 26, 0.05) 100%)',
              border: '1px solid rgba(82, 196, 26, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 4px 16px rgba(82, 196, 26, 0.2)',
              transition: 'all 0.3s ease',
            }}
            bodyStyle={{ padding: '20px' }}
          >
            <Statistic
              title={
                <span style={{ color: '#8b949e', fontSize: '14px' }}>
                  <BarChartOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                  总订单数
                </span>
              }
              value={salesOverview?.total_orders || 0}
              suffix="单"
              valueStyle={{ 
                color: '#52c41a',
                fontSize: '24px',
                fontWeight: 700,
              }}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: '20px' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: 'linear-gradient(135deg, rgba(250, 173, 20, 0.1) 0%, rgba(250, 173, 20, 0.05) 100%)',
              border: '1px solid rgba(250, 173, 20, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 4px 16px rgba(250, 173, 20, 0.2)',
              transition: 'all 0.3s ease',
            }}
            bodyStyle={{ padding: '20px' }}
          >
            <Statistic
              title={
                <span style={{ color: '#8b949e', fontSize: '14px' }}>
                  <DollarOutlined style={{ marginRight: 8, color: '#faad14' }} />
                  GMV
                </span>
              }
              value={salesOverview?.total_gmv || '暂无数据'}
              suffix={salesOverview?.total_gmv ? 'CNY' : ''}
              valueStyle={{ 
                color: '#faad14',
                fontSize: '24px',
                fontWeight: 700,
              }}
              prefix={<RiseOutlined style={{ color: '#faad14', fontSize: '20px' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            style={{
              background: salesOverview?.total_profit 
                ? (salesOverview.total_profit >= 0 
                  ? 'linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(82, 196, 26, 0.05) 100%)'
                  : 'linear-gradient(135deg, rgba(245, 34, 45, 0.1) 0%, rgba(245, 34, 45, 0.05) 100%)')
                : 'linear-gradient(135deg, rgba(139, 148, 158, 0.1) 0%, rgba(139, 148, 158, 0.05) 100%)',
              border: `1px solid ${salesOverview?.total_profit 
                ? (salesOverview.total_profit >= 0 ? 'rgba(82, 196, 26, 0.3)' : 'rgba(245, 34, 45, 0.3)')
                : 'rgba(139, 148, 158, 0.3)'}`,
              borderRadius: '12px',
              boxShadow: `0 4px 16px ${salesOverview?.total_profit 
                ? (salesOverview.total_profit >= 0 ? 'rgba(82, 196, 26, 0.2)' : 'rgba(245, 34, 45, 0.2)')
                : 'rgba(139, 148, 158, 0.2)'}`,
              transition: 'all 0.3s ease',
            }}
            bodyStyle={{ padding: '20px' }}
          >
            <Statistic
              title={
                <span style={{ color: '#8b949e', fontSize: '14px' }}>
                  <TrophyOutlined style={{ marginRight: 8, color: salesOverview?.total_profit 
                    ? (salesOverview.total_profit >= 0 ? '#52c41a' : '#f5222d')
                    : '#8b949e' }} />
                  利润
                </span>
              }
              value={salesOverview?.total_profit || '暂无数据'}
              suffix={salesOverview?.total_profit ? 'CNY' : ''}
              valueStyle={{ 
                color: salesOverview?.total_profit 
                  ? (salesOverview.total_profit >= 0 ? '#52c41a' : '#f5222d')
                  : '#8b949e',
                fontSize: '24px',
                fontWeight: 700,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 销量趋势图 */}
      {chartOption && (
        <Card 
          title={
            <Space>
              <LineChartOutlined style={{ color: '#1890ff' }} />
              <span style={{ color: '#c9d1d9', fontWeight: 600 }}>销量趋势分析</span>
            </Space>
          }
          style={{ 
            marginBottom: 24,
            background: 'rgba(22, 27, 34, 0.8)',
            border: '1px solid #30363d',
            borderRadius: '12px',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          }}
          bodyStyle={{ padding: '20px' }}
        >
          <ReactECharts 
            option={chartOption} 
            style={{ height: '450px' }}
            opts={{ renderer: 'svg' }}
          />
        </Card>
      )}

      {/* Tab切换 */}
      <Card
        style={{
          background: 'rgba(22, 27, 34, 0.8)',
          border: '1px solid #30363d',
          borderRadius: '12px',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}
        bodyStyle={{ padding: '20px' }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'spu',
              label: (
                <Space>
                  <AppstoreOutlined />
                  <span>SPU销量排行</span>
                </Space>
              ),
              children: (
                <Table
                  columns={spuColumns}
                  dataSource={spuRanking?.ranking || []}
                  rowKey={(record, index) => record?.rank?.toString() || `spu-${index}`}
                  loading={spuLoading}
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showTotal: (total) => (
                      <span style={{ color: '#8b949e' }}>
                        共 <strong style={{ color: '#1890ff' }}>{total}</strong> 条记录
                      </span>
                    ),
                  }}
                  style={{
                    background: 'transparent',
                  }}
                />
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
                <div>
                  {managerChartOption && (
                    <Card 
                      title={
                        <Space>
                          <LineChartOutlined style={{ color: '#1890ff' }} />
                          <span style={{ color: '#c9d1d9', fontWeight: 600 }}>负责人订单量趋势</span>
                        </Space>
                      }
                      style={{ 
                        marginBottom: 16,
                        background: 'rgba(13, 17, 23, 0.6)',
                        border: '1px solid #30363d',
                        borderRadius: '8px',
                      }}
                      bodyStyle={{ padding: '20px' }}
                    >
                      <ReactECharts 
                        option={managerChartOption} 
                        style={{ height: '400px' }}
                        opts={{ renderer: 'svg' }}
                      />
                    </Card>
                  )}
                  <Table
                    columns={managerColumns}
                    dataSource={managerSales?.managers || []}
                    rowKey="manager"
                    loading={managerLoading}
                    pagination={{
                      pageSize: 20,
                      showSizeChanger: true,
                      showTotal: (total) => (
                        <span style={{ color: '#8b949e' }}>
                          共 <strong style={{ color: '#1890ff' }}>{total}</strong> 条记录
                        </span>
                      ),
                    }}
                    style={{
                      background: 'transparent',
                    }}
                  />
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default SalesStatistics