import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Select, DatePicker, Table, Tag, Statistic, Space, Button, Empty } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import dayjs, { Dayjs } from 'dayjs'
import { logisticsApi, shopApi } from '@/services/api'

const { RangePicker } = DatePicker

interface CityOrderStats {
  city: string
  order_count: number
  country?: string
}

interface DeliveryHeatmapData {
  city_stats: CityOrderStats[]
  total_orders: number
  unique_cities: number
}

function Logistics() {
  const [selectedShopId, setSelectedShopId] = useState<number | undefined>(undefined)
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null]>([null, null])

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取配送热力图数据
  const { data: heatmapData, isLoading, refetch } = useQuery<DeliveryHeatmapData>({
    queryKey: ['delivery-heatmap', selectedShopId, dateRange],
    queryFn: () =>
      logisticsApi.getDeliveryHeatmap({
        shop_id: selectedShopId,
        start_date: dateRange[0] ? dateRange[0].format('YYYY-MM-DD') : undefined,
        end_date: dateRange[1] ? dateRange[1].format('YYYY-MM-DD') : undefined,
      }),
  })

  // 准备地图数据
  const prepareMapData = () => {
    if (!heatmapData || !heatmapData.city_stats || heatmapData.city_stats.length === 0) {
      return {
        scatterData: [],
        barData: [],
        pieData: [],
      }
    }

    // 散点图数据（用于地图热力图，使用更合理的布局）
    const maxOrders = Math.max(...heatmapData.city_stats.map((item) => item.order_count))
    const scatterData = heatmapData.city_stats
      .slice(0, 100) // 取前100个城市
      .map((item, index) => {
        // 根据订单数量生成相对坐标，订单多的城市分布在中心区域
        const radius = Math.sqrt(item.order_count / maxOrders) * 4
        const angle = (index / heatmapData.city_stats.length) * Math.PI * 2
        const x = 5 + radius * Math.cos(angle)
        const y = 5 + radius * Math.sin(angle)
        return {
          name: item.city,
          value: [x, y, item.order_count],
          orderCount: item.order_count,
          country: item.country || '未知',
        }
      })

    // 柱状图数据（城市排名）
    const barData = heatmapData.city_stats.slice(0, 20).map((item) => ({
      name: item.city.length > 8 ? item.city.substring(0, 8) + '...' : item.city,
      value: item.order_count,
    }))

    // 饼图数据（TOP 15城市）
    const pieData = heatmapData.city_stats.slice(0, 15).map((item) => ({
      name: item.city,
      value: item.order_count,
    }))

    // 如果有其他城市，合并为"其他"
    if (heatmapData.city_stats.length > 15) {
      const otherCount = heatmapData.city_stats
        .slice(15)
        .reduce((sum, item) => sum + item.order_count, 0)
      if (otherCount > 0) {
        pieData.push({
          name: '其他',
          value: otherCount,
        })
      }
    }

    return { scatterData, barData, pieData }
  }

  const { scatterData, barData, pieData } = prepareMapData()

  // 地图散点图配置（热力图效果）
  const scatterMapOption = {
    backgroundColor: 'transparent',
    title: {
      text: '订单配送城市分布热力图',
      subtext: `${heatmapData?.unique_cities || 0} 个城市 | ${heatmapData?.total_orders || 0} 个订单`,
      left: 'center',
      textStyle: {
        color: '#c9d1d9',
      },
      subtextStyle: {
        color: '#8b949e',
        fontSize: 12,
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.data) {
          return `<div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 4px;">${params.data.name}</div>
            <div>订单数量: <span style="color: #1890ff; font-weight: bold;">${params.data.orderCount}</span></div>
            <div>国家: ${params.data.country}</div>
            <div>占比: ${((params.data.orderCount / (heatmapData?.total_orders || 1)) * 100).toFixed(2)}%</div>
          </div>`
        }
        return ''
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(...scatterData.map((d: any) => d.orderCount), 1),
      calculable: true,
      inRange: {
        color: ['#50a3ba', '#eac736', '#d94e5d'],
      },
      textStyle: {
        color: '#c9d1d9',
      },
      left: 'left',
      bottom: 'bottom',
    },
    xAxis: {
      type: 'value',
      show: false,
      min: 0,
      max: 10,
    },
    yAxis: {
      type: 'value',
      show: false,
      min: 0,
      max: 10,
    },
    series: [
      {
        name: '订单分布',
        type: 'scatter',
        data: scatterData,
        symbolSize: (val: number[]) => {
          if (scatterData.length === 0) return 10
          const maxCount = Math.max(...scatterData.map((d: any) => d.orderCount))
          const size = Math.sqrt(val[2] / maxCount) * 40 + 8
          return Math.max(Math.min(size, 60), 8)
        },
        itemStyle: {
          opacity: 0.7,
          borderColor: '#fff',
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            opacity: 1,
            borderWidth: 2,
          },
        },
        label: {
          show: true,
          position: 'right',
          formatter: (params: any) => {
            // 只显示订单数较多的城市标签
            const maxCount = Math.max(...scatterData.map((d: any) => d.orderCount))
            if (params.data.orderCount > maxCount * 0.1) {
              return params.data.name
            }
            return ''
          },
          fontSize: 10,
          color: '#c9d1d9',
        },
      },
    ],
  }

  // 城市分布饼图配置
  const pieChartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '城市订单分布 TOP 15',
      left: 'center',
      textStyle: {
        color: '#c9d1d9',
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        color: '#c9d1d9',
      },
    },
    series: [
      {
        name: '订单数量',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: '{b}: {d}%',
          color: '#c9d1d9',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        data: pieData,
      },
    ],
  }

  // 城市排名柱状图配置
  const cityRankOption = {
    backgroundColor: 'transparent',
    title: {
      text: '城市订单量排名 TOP 20',
      left: 'center',
      textStyle: {
        color: '#c9d1d9',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%',
    },
    xAxis: {
      type: 'category',
      data: barData.map((item) => item.name),
      axisLabel: {
        rotate: 45,
        color: '#c9d1d9',
        fontSize: 10,
      },
    },
    yAxis: {
      type: 'value',
      name: '订单数量',
      nameTextStyle: {
        color: '#c9d1d9',
      },
      axisLabel: {
        color: '#c9d1d9',
      },
    },
    series: [
      {
        name: '订单数量',
        type: 'bar',
        data: barData.map((item) => item.value),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' },
            ],
          },
        },
        emphasis: {
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#2378f7' },
                { offset: 0.7, color: '#2378f7' },
                { offset: 1, color: '#83bff6' },
              ],
            },
          },
        },
      },
    ],
  }

  // 表格列定义
  const columns: ColumnsType<CityOrderStats> = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      width: 150,
    },
    {
      title: '国家',
      dataIndex: 'country',
      key: 'country',
      width: 100,
      render: (country: string) => country || '未知',
    },
    {
      title: '订单数量',
      dataIndex: 'order_count',
      key: 'order_count',
      width: 120,
      sorter: (a, b) => a.order_count - b.order_count,
      render: (count: number) => (
        <Tag color="blue" style={{ margin: 0 }}>
          {count}
        </Tag>
      ),
    },
    {
      title: '占比',
      key: 'percentage',
      width: 120,
      render: (_: any, record: CityOrderStats) => {
        if (!heatmapData || heatmapData.total_orders === 0) return '-'
        const percentage = ((record.order_count / heatmapData.total_orders) * 100).toFixed(2)
        return `${percentage}%`
      },
    },
  ]

  return (
    <div>
      <h2
        style={{
          marginBottom: 24,
          color: '#c9d1d9',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        🚚 物流管理 - 配送地址热力图
      </h2>

      {/* 筛选卡片 */}
      <Card className="chart-card" style={{ marginBottom: 16 }}>
        <Space size="large" wrap>
          <Space>
            <span style={{ color: '#c9d1d9' }}>店铺:</span>
            <Select
              style={{ width: 200 }}
              placeholder="选择店铺（不选则显示所有）"
              allowClear
              value={selectedShopId}
              onChange={setSelectedShopId}
              options={
                shops?.map((shop: any) => ({
                  label: shop.shop_name,
                  value: shop.id,
                })) || []
              }
            />
          </Space>
          <Space>
            <span style={{ color: '#c9d1d9' }}>日期范围:</span>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [Dayjs | null, Dayjs | null])}
              format="YYYY-MM-DD"
            />
          </Space>
          <Button type="primary" onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </Card>

      {/* 统计卡片 */}
      {heatmapData && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Card className="chart-card">
              <Statistic
                title="总订单数"
                value={heatmapData.total_orders}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card className="chart-card">
              <Statistic
                title="覆盖城市数"
                value={heatmapData.unique_cities}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card className="chart-card">
              <Statistic
                title="平均每城订单"
                value={
                  heatmapData.unique_cities > 0
                    ? Math.round(heatmapData.total_orders / heatmapData.unique_cities)
                    : 0
                }
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 图表展示 */}
      {isLoading ? (
        <Card className="chart-card">
          <div style={{ textAlign: 'center', padding: '40px', color: '#c9d1d9' }}>
            加载中...
          </div>
        </Card>
      ) : !heatmapData || !heatmapData.city_stats || heatmapData.city_stats.length === 0 ? (
        <Card className="chart-card">
          <Empty description="暂无配送地址数据" />
        </Card>
      ) : (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={24}>
              <Card className="chart-card">
                <ReactECharts
                  option={scatterMapOption}
                  style={{ height: 500 }}
                  opts={{ renderer: 'canvas' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card className="chart-card">
                <ReactECharts
                  option={pieChartOption}
                  style={{ height: 400 }}
                  opts={{ renderer: 'canvas' }}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card className="chart-card">
                <ReactECharts
                  option={cityRankOption}
                  style={{ height: 400 }}
                  opts={{ renderer: 'canvas' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 详细表格 */}
          <Card className="chart-card">
            <Table
              columns={columns}
              dataSource={heatmapData.city_stats}
              rowKey={(record, index) => `${record.city}-${index}`}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个城市`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
            />
          </Card>
        </>
      )}
    </div>
  )
}

export default Logistics
