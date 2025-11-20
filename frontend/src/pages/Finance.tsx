import { useQuery } from '@tanstack/react-query'
import { Table, Card, Row, Col, Statistic, Spin } from 'antd'
import { DollarOutlined, RiseOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import { analyticsApi } from '@/services/api'
import dayjs from 'dayjs'

function Finance() {
  // 获取回款统计数据
  const { data: collectionData, isLoading: collectionLoading } = useQuery({
    queryKey: ['payment-collection', 30],
    queryFn: () => analyticsApi.getPaymentCollection({ days: 30 }),
    staleTime: 0,
  })

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
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
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
      text: '回款趋势',
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
      top: '10%',
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
        color: series.name === '总计' ? '#1890ff' : undefined,
      },
      itemStyle: {
        color: series.name === '总计' ? '#1890ff' : undefined,
      },
      areaStyle: series.name === '总计' ? {
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
      } : undefined,
    })),
  } : null

  return (
    <div>
      <h2 style={{ 
        marginBottom: 24, 
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        💰 财务管理
      </h2>
      
      {/* 财务统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="本月总收入"
              value={74403.62}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="CNY"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="本月总利润"
              value={33502.25}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="CNY"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="利润率"
              value={45.03}
              precision={2}
              suffix="%"
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {collectionLoading ? (
        <Card className="chart-card">
          <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />
        </Card>
      ) : (
        <>
          {/* 回款统计汇总 */}
          <Card className="chart-card" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="总回款金额"
                  value={collectionData?.summary?.total_amount || 0}
                  precision={2}
                  prefix={<DollarOutlined />}
                  suffix="CNY"
                  valueStyle={{ color: '#3f8600', fontSize: '24px' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="回款订单数"
                  value={collectionData?.summary?.total_orders || 0}
                  suffix="单"
                  valueStyle={{ fontSize: '24px' }}
                />
              </Col>
            </Row>
          </Card>

          {/* 回款统计表格 */}
          <Card className="chart-card" style={{ marginBottom: 16 }}>
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

          {/* 回款趋势折线图 */}
          {collectionChartOption && (
            <Card className="chart-card">
              <ReactECharts option={collectionChartOption} style={{ height: 400 }} />
            </Card>
          )}
        </>
      )}
    </div>
  )
}

export default Finance
