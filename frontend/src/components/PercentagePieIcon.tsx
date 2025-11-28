import { useMemo } from 'react'

interface PercentagePieIconProps {
  percentage: number // 百分比值 (0-100)
  size?: number // 图标大小，默认 40px
  color?: string // 主颜色
  backgroundColor?: string // 背景颜色
}

/**
 * 百分比饼状图图标组件 - 重新设计版本
 * 使用填充饼状图设计，更清晰、更现代
 */
export default function PercentagePieIcon({ 
  percentage, 
  size = 40,
  color = '#52c41a',
  backgroundColor = 'rgba(255, 255, 255, 0.1)'
}: PercentagePieIconProps) {
  // 限制百分比范围 0-100
  const normalizedPercentage = Math.max(0, Math.min(100, percentage))
  
  // SVG 参数
  const radius = (size / 2) - 3
  const center = size / 2
  const viewBox = `0 0 ${size} ${size}`
  
  // 计算饼状图的路径
  // 从顶部（12点）开始，顺时针填充
  const startAngle = -90 // 从顶部开始（-90度）
  const endAngle = startAngle + (normalizedPercentage / 100) * 360
  
  // 转换为弧度
  const startAngleRad = (startAngle * Math.PI) / 180
  const endAngleRad = (endAngle * Math.PI) / 180
  
  // 计算起始点和终点坐标
  const startX = center + radius * Math.cos(startAngleRad)
  const startY = center + radius * Math.sin(startAngleRad)
  const endX = center + radius * Math.cos(endAngleRad)
  const endY = center + radius * Math.sin(endAngleRad)
  
  // 判断是否需要大弧（超过180度）
  const largeArcFlag = normalizedPercentage > 50 ? 1 : 0
  
  // 构建 SVG 路径
  const pathData = useMemo(() => {
    if (normalizedPercentage === 0) {
      return ''
    } else if (normalizedPercentage >= 100) {
      return '' // 100% 时使用 circle
    }
    
    // 绘制饼状扇形：从中心到顶部 -> 圆弧到终点 -> 回到中心
    return `M ${center},${center} L ${startX},${startY} A ${radius},${radius} 0 ${largeArcFlag},1 ${endX},${endY} Z`
  }, [normalizedPercentage, center, radius, startX, startY, endX, endY, largeArcFlag])
  
  return (
    <div style={{
      width: size,
      height: size,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
    }}>
      <svg
        width={size}
        height={size}
        viewBox={viewBox}
        style={{ display: 'block' }}
      >
        <defs>
          {/* 渐变定义 - 增强视觉深度 */}
          <linearGradient id={`pie-fill-gradient-${size}-${color.replace('#', '')}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="1" />
            <stop offset="50%" stopColor={color} stopOpacity="0.95" />
            <stop offset="100%" stopColor={color} stopOpacity="0.85" />
          </linearGradient>
          
          {/* 发光滤镜 */}
          <filter id={`pie-glow-filter-${size}-${color.replace('#', '')}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {/* 背景圆 - 使用深色背景增强对比 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill={backgroundColor}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="1"
        />
        
        {/* 百分比饼状扇形 - 使用渐变填充 */}
        {normalizedPercentage > 0 && normalizedPercentage < 100 && (
          <path
            d={pathData}
            fill={`url(#pie-fill-gradient-${size}-${color.replace('#', '')})`}
            stroke={color}
            strokeWidth="2"
            style={{
              transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: `url(#pie-glow-filter-${size}-${color.replace('#', '')})`,
              opacity: 1,
            }}
          />
        )}
        
        {/* 100% 时显示完整圆 */}
        {normalizedPercentage >= 100 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill={`url(#pie-fill-gradient-${size}-${color.replace('#', '')})`}
            stroke={color}
            strokeWidth="2"
            style={{
              transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: `url(#pie-glow-filter-${size}-${color.replace('#', '')})`,
              opacity: 1,
            }}
          />
        )}
        
        {/* 外边框 - 增强视觉层次 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={`${color}50`}
          strokeWidth="1.5"
          opacity="0.5"
        />
      </svg>
      
      {/* 百分比符号，居中显示 */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        fontSize: size * 0.3,
        fontWeight: 900,
        color: color,
        fontFamily: 'JetBrains Mono, monospace',
        lineHeight: 1,
        textShadow: `0 0 8px ${color}cc, 0 0 16px ${color}80`,
        transition: 'all 0.3s ease',
        pointerEvents: 'none',
        opacity: 1,
        letterSpacing: '-1px',
      }}>
        %
      </div>
    </div>
  )
}
