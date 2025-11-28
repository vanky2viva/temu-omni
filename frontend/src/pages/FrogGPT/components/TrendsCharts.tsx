/**
 * 运营图表区组件
 * 显示 GMV/订单/利润趋势、退款率趋势、SKU Top 表格
 */
import React, { useMemo } from 'react'
import { Card, Table, Tag, Tooltip } from 'antd'
import ReactECharts from 'echarts-for-react'
import { LineChartOutlined, BarChartOutlined } from '@ant-design/icons'
import type { TrendData, SkuRankingItem } from '../types'
import dayjs from 'dayjs'

interface TrendsChartsProps {
  trendData?: TrendData[]
  skuRanking?: SkuRankingItem[]
  dateRange?: [string, string]
}

const TrendsCharts: React.FC<TrendsChartsProps> = ({ 
  trendData = [], 
  skuRanking = [],
  dateRange 
}) => {
  // GMV/订单/利润趋势图配置
  const trendsChartOption = useMemo(() => {
    const dates = trendData.map(item => dayjs(item.date).format('MM-DD'))
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#1890ff',
        borderWidth: 1,
        textStyle: { color: '#fff' },
      },
      legend: {
        data: ['GMV', '订单数', '利润'],
        bottom: 8,
        textStyle: { color: '#8b949e', fontSize: 11 },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '12%',
        top: '8%',
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
          fontSize: 11,
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '金额（元）',
          nameTextStyle: { color: '#8b949e', fontSize: 11 },
          axisLine: { lineStyle: { color: '#30363d' } },
          axisLabel: { color: '#8b949e', fontSize: 11 },
          splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
        },
        {
          type: 'value',
          name: '订单数',
          nameTextStyle: { color: '#8b949e', fontSize: 11 },
          axisLine: { lineStyle: { color: '#30363d' } },
          axisLabel: { color: '#8b949e', fontSize: 11 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: 'GMV',
          type: 'line',
          data: trendData.map(item => (item.gmv / 1000).toFixed(1)),
          smooth: true,
          lineStyle: { width: 3, color: '#ffdd57' },
          itemStyle: { color: '#ffdd57' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(255, 221, 87, 0.3)' },
                { offset: 1, color: 'rgba(255, 221, 87, 0.05)' },
              ],
            },
          },
        },
        {
          name: '订单数',
          type: 'line',
          yAxisIndex: 1,
          data: trendData.map(item => item.orders),
          smooth: true,
          lineStyle: { width: 3, color: '#3273dc' },
          itemStyle: { color: '#3273dc' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(50, 115, 220, 0.3)' },
                { offset: 1, color: 'rgba(50, 115, 220, 0.05)' },
              ],
            },
          },
        },
        {
          name: '利润',
          type: 'line',
          data: trendData.map(item => (item.profit / 1000).toFixed(1)),
          smooth: true,
          lineStyle: { width: 3, color: '#48c774' },
          itemStyle: { color: '#48c774' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(72, 199, 116, 0.3)' },
                { offset: 1, color: 'rgba(72, 199, 116, 0.05)' },
              ],
            },
          },
        },
      ],
    }
  }, [trendData])

 // 退款率趋势图配置
  // SKU Top 表格列配置
  const skuColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      align: 'center' as const,
      render: (rank: number) => (
        <Tag color={rank <= 3 ? '#f14668' : '#00d1b2'} style={{ margin: 0 }}>
          {rank}
        </Tag>
      ),
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 120,
      render: (sku: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#00d1b2' }}>
          {sku}
        </span>
      ),
    },
    {
      title: '商品名称',
      dataIndex: 'productName',
      key: 'productName',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span style={{ color: '#c9d1d9', fontSize: '11px' }}>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right' as const,
      render: (qty: number) => (
        <span style={{ color: '#48c774', fontWeight: 600, fontSize: '11px' }}>
          {qty.toLocaleString()}
        </span>
      ),
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 100,
      align: 'right' as const,
      render: (gmv: number) => (
        <span style={{ color: '#ffdd57', fontSize: '11px' }}>
          ¥{(gmv / 1000).toFixed(1)}k
        </span>
      ),
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      align: 'right' as const,
      render: (profit: number) => (
        <span style={{ 
          color: profit >= 0 ? '#48c774' : '#f14668',
          fontSize: '11px',
          fontWeight: 600,
        }}>
          ¥{(profit / 1000).toFixed(1)}k
        </span>
      ),
    },
    {
      title: '退款率',
      dataIndex: 'refundRate',
      key: 'refundRate',
      width: 80,
      align: 'right' as const,
      render: (rate: number) => (
        <span style={{ 
          color: rate > 5 ? '#f14668' : rate > 3 ? '#faad14' : '#48c774',
          fontSize: '11px',
        }}>
          {rate.toFixed(2)}%
        </span>
      ),
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* GMV/订单/利润趋势图 */}
      <Card
        className="frog-gpt-section-card"
        title={
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <LineChartOutlined style={{ color: '#00d1b2' }} />
            <span>运营趋势分析</span>
          </span>
        }
        styles={{
          header: {
            background: 'transparent',
            borderBottom: '1px solid #1E293B',
            color: '#e2e8f0',
          },
          body: { padding: '12px' },
        }}
      >
        <ReactECharts
          option={trendsChartOption}
          style={{ height: '280px' }}
          opts={{ renderer: 'svg' }}
        />
      </Card>

      {/* SKU Top 表格 */}
      <Card
        className="frog-gpt-section-card"
        title={
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChartOutlined style={{ color: '#60a5fa' }} />
            <span>SKU Top 排行</span>
          </span>
        }
        styles={{
          header: {
            background: 'transparent',
            borderBottom: '1px solid #1E293B',
            color: '#e2e8f0',
          },
          body: { padding: '12px' },
        }}
      >
        <Table
          columns={skuColumns}
          dataSource={skuRanking}
          rowKey="sku"
          pagination={false}
          size="small"
          scroll={{ y: 300 }}
          style={{ background: 'transparent' }}
        />
      </Card>
    </div>
  )
}

export default TrendsCharts
