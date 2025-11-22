import { Card, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import { useMemo } from 'react'

interface KPICardData {
  title: string
  value: number
  trend?: number[] // 7日趋势数据
  todayChange?: number // 今日新增/变化
  weekChange?: number // 周对比变化百分比
  valueStyle?: React.CSSProperties
  color?: string
  precision?: number // 精度
  suffix?: string // 后缀
  onClick?: () => void
  loading?: boolean
}

interface EnhancedKPICardProps {
  data: KPICardData
  isMobile?: boolean
}

/**
 * 增强的KPI卡片组件
 * 包含主数据、趋势图表、今日新增、周对比等功能
 */
export default function EnhancedKPICard({ data, isMobile = false }: EnhancedKPICardProps) {
  const {
    title,
    value,
    trend = [],
    todayChange,
    weekChange,
    valueStyle,
    color,
    precision,
    suffix,
    onClick,
    loading = false
  } = data

  // Mini图表配置
  const miniChartOption = useMemo(() => {
    const dates = Array.from({ length: trend.length }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (trend.length - 1 - i))
      return `${date.getMonth() + 1}/${date.getDate()}`
    })

    return {
      backgroundColor: 'transparent',
      grid: {
        left: 0,
        right: 0,
        top: 5,
        bottom: 0,
        containLabel: false,
      },
      xAxis: {
        type: 'category',
        data: dates,
        show: false,
      },
      yAxis: {
        type: 'value',
        show: false,
      },
      series: [
        {
          type: 'line',
          data: trend,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            color: color || '#1890ff',
            width: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: color ? `${color}40` : '#1890ff40',
                },
                {
                  offset: 1,
                  color: color ? `${color}00` : '#1890ff00',
                },
              ],
            },
          },
        },
      ],
    }
  }, [trend, color])

  return (
    <Card
      size="small"
      loading={loading}
      onClick={onClick}
      hoverable={!!onClick}
      style={{
        height: '100%',
        minHeight: isMobile ? '100px' : '120px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      bodyStyle={{
        padding: isMobile ? '12px' : '16px',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
      className="enhanced-kpi-card"
    >
      <div>
        <div style={{ 
          fontSize: '12px', 
          color: 'var(--color-fg)', 
          opacity: 0.7,
          marginBottom: '4px'
        }}>
          {title}
        </div>
        <Statistic
          value={value}
          precision={precision}
          suffix={suffix}
          valueStyle={{
            fontSize: isMobile ? '20px' : '24px',
            fontWeight: 'bold',
            lineHeight: '1.2',
            ...valueStyle,
            color: color || valueStyle?.color,
          }}
        />
      </div>

      {/* 今日新增和周对比 */}
      {(todayChange !== undefined || weekChange !== undefined) && (
        <div style={{ 
          marginTop: '8px',
          fontSize: '11px',
          display: 'flex',
          gap: '12px',
        }}>
          {todayChange !== undefined && (
            <span style={{ color: 'var(--color-fg)', opacity: 0.6 }}>
              今日: {todayChange > 0 ? '+' : ''}{todayChange}
            </span>
          )}
          {weekChange !== undefined && (
            <span style={{ 
              color: weekChange >= 0 ? '#52c41a' : '#ff4d4f',
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
            }}>
              {weekChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              {Math.abs(weekChange).toFixed(1)}%
            </span>
          )}
        </div>
      )}

      {/* Mini趋势图 */}
      {trend && trend.length > 0 && (
        <div style={{ 
          marginTop: '8px',
          height: '40px',
          width: '100%',
        }}>
          <ReactECharts 
            option={miniChartOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      )}
    </Card>
  )
}

