import { Card } from 'antd'
import LazyECharts from './LazyECharts'
import { useMemo } from 'react'
import type { ReactNode } from 'react'

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
  icon?: ReactNode // 图标组件
  description?: string // 描述文字
  showWeekChange?: boolean // 是否显示周变化（默认true）
}

interface EnhancedKPICardProps {
  data: KPICardData
  isMobile?: boolean
}

/**
 * 增强的KPI卡片组件 - Bulma风格
 * 参考 Bulma Card 组件设计：https://bulma.io/documentation/components/card/
 * 包含主数据、趋势图表、图标等功能
 */
export default function EnhancedKPICard({ data, isMobile = false }: EnhancedKPICardProps) {
  const {
    title,
    value,
    trend = [],
    valueStyle,
    color = '#00d1b2',
    precision,
    suffix,
    onClick,
    loading = false,
    icon,
    description,
  } = data

  // 根据颜色生成渐变背景（参考 Bulma 风格）
  const getGradientStyle = useMemo(() => {
    if (!color) return {}
    
    // 将颜色转换为 rgba
    const hexToRgba = (hex: string, alpha: number) => {
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
    
    return {
      background: `linear-gradient(135deg, ${hexToRgba(color, 0.15)} 0%, ${hexToRgba(color, 0.05)} 100%)`,
      border: `1px solid ${hexToRgba(color, 0.3)}`,
      boxShadow: `0 8px 32px ${hexToRgba(color, 0.15)}`,
    }
  }, [color])
  
  // 格式化数字，添加千分位分隔符
  const formatNumber = (val: number | undefined, prec: number = 0): string => {
    if (val === undefined || val === null) return '0'
    return val.toLocaleString('zh-CN', {
      minimumFractionDigits: prec,
      maximumFractionDigits: prec,
    })
  }

  // Mini图表配置
  const miniChartOption = useMemo(() => {
    if (!trend || trend.length === 0) return null
    
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
            color: color,
            width: 2.5,
            shadowBlur: 4,
            shadowColor: color,
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
                  color: color ? `${color}60` : '#00d1b260',
                },
                {
                  offset: 1,
                  color: color ? `${color}00` : '#00d1b200',
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
      className="stat-card bulma-kpi-card"
      bordered={false}
      loading={loading}
      onClick={onClick}
      style={{
        height: '160px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        ...getGradientStyle,
        backdropFilter: 'blur(10px)',
        overflow: 'hidden',
      }}
      styles={{
        body: {
          padding: trend && trend.length > 0 ? '0.875rem' : '1rem', // 有趋势图时减少padding
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: trend && trend.length > 0 ? 'space-between' : 'center', // 有趋势图时两端对齐
          alignItems: 'center',
          textAlign: 'center',
          boxSizing: 'border-box',
          overflow: 'hidden',
        },
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)'
        const hexToRgba = (hex: string, alpha: number) => {
          const r = parseInt(hex.slice(1, 3), 16)
          const g = parseInt(hex.slice(3, 5), 16)
          const b = parseInt(hex.slice(5, 7), 16)
          return `rgba(${r}, ${g}, ${b}, ${alpha})`
        }
        e.currentTarget.style.boxShadow = `0 12px 48px ${hexToRgba(color, 0.25)}`
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = getGradientStyle.boxShadow || ''
      }}
    >
      {/* 图标和标题行 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        marginBottom: trend && trend.length > 0 ? '0.5rem' : '0.75rem',
        width: '100%',
        flexShrink: 0,
      }}>
        {/* 图标 */}
        {icon && (
          <div style={{
            width: trend && trend.length > 0 ? '32px' : '36px',
            height: trend && trend.length > 0 ? '32px' : '36px',
            borderRadius: '0.75rem', // Bulma card-radius
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 4px 12px ${color}66`,
            flexShrink: 0,
          }}>
            {icon}
          </div>
        )}
        
        {/* 标题 - Bulma card-header style */}
        <div style={{ 
          color: 'var(--color-fg)',
          fontSize: '0.8125rem', // 13px
          fontWeight: 700,
          letterSpacing: '0.5px',
          textTransform: 'uppercase',
          width: icon ? 'auto' : '100%',
          lineHeight: 1.4,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          flex: icon ? 1 : 'none',
          minWidth: 0,
          opacity: 1,
        }}>
          {title}
        </div>
      </div>

      {/* 主数值 - Bulma title style */}
      <div style={{ 
        color: color,
        fontSize: trend && trend.length > 0 
          ? (isMobile ? '1.5rem' : '1.75rem')  // 有趋势图时稍小
          : (isMobile ? '1.75rem' : '2rem'),   // 无趋势图时正常大小
        fontWeight: 700,
        fontFamily: 'JetBrains Mono, monospace',
        lineHeight: 1.2,
        marginBottom: description ? (trend && trend.length > 0 ? '0.25rem' : '0.5rem') : '0',
        textShadow: `0 0 20px ${color}80`,
        width: '100%',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
        padding: '0 4px',
        boxSizing: 'border-box',
        ...valueStyle,
      }}>
        {formatNumber(value, precision)}{suffix || ''}
      </div>

      {/* 描述文字 - Bulma subtitle style */}
      {description && (
        <div style={{ 
          color: 'var(--color-fg)', 
          fontSize: trend && trend.length > 0 ? '0.8125rem' : '0.875rem', // 13px / 14px
          lineHeight: 1.5,
          width: '100%',
          marginBottom: trend && trend.length > 0 ? '0.5rem' : '0',
          wordBreak: 'break-word',
          overflowWrap: 'break-word',
          padding: '0 4px',
          boxSizing: 'border-box',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          opacity: 0.9,
          fontWeight: 500,
        }}>
          {description}
        </div>
      )}

      {/* Mini趋势图 */}
      {trend && trend.length > 0 && miniChartOption && (
        <div style={{ 
          marginTop: 'auto',
          height: '32px',
          width: '100%',
          maxWidth: '100%',
          position: 'relative',
          flexShrink: 0,
          overflow: 'hidden',
          paddingTop: '0.25rem',
        }}>
          <LazyECharts 
            option={miniChartOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      )}
    </Card>
  )
}
