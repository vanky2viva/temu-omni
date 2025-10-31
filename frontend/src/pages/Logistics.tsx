import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from 'antd'
import StateHeatmap from '@/components/StateHeatmap'
import { orderApi } from '@/services/api'

function Logistics() {
  // 获取所有订单数据
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders', 'logistics'],
    queryFn: () => orderApi.getOrders({ limit: 10000 }), // 获取足够多的订单数据
  })

  // 从订单数据中提取地址信息并统计各州订单数量
  const stateOrderData = useMemo(() => {
    if (!orders || orders.length === 0) {
      return []
    }

    const stateCountMap: Record<string, number> = {}
    
    orders.forEach((order: any) => {
      // 优先使用直接从数据库获取的地址字段
      let province: string | null = order.shipping_province || null
      
      // 如果没有从数据库字段获取到，尝试从 raw_data JSON 中提取
      if (!province && order.raw_data) {
        try {
          const rawData = typeof order.raw_data === 'string' 
            ? JSON.parse(order.raw_data) 
            : order.raw_data
          
          // 尝试多种可能的字段名
          province = rawData.shipping_province ||
                    rawData.shipping_state || 
                    rawData.state || 
                    rawData.province || 
                    rawData.region ||
                    rawData.address_state ||
                    rawData.STATE ||
                    rawData.State ||
                    null
          
          // 如果没有province，尝试从地址中解析
          if (!province && rawData.shipping_address) {
            const address = rawData.shipping_address
            if (typeof address === 'string') {
              // 尝试从地址字符串中提取州代码（如 "CA", "NY"）
              const stateMatch = address.match(/\b([A-Z]{2})\b/)
              if (stateMatch) {
                province = stateMatch[1]
              }
            } else if (typeof address === 'object') {
              province = address.state || address.province || address.region || null
            }
          }
        } catch (e) {
          // JSON解析失败，忽略
          console.warn('Failed to parse raw_data:', e)
        }
      }
      
      // 如果找到了州/省份信息，进行统计
      if (province) {
        const stateCode = province.trim().toUpperCase()
        // 验证是否是有效的美国州代码（2个字母）
        if (/^[A-Z]{2}$/.test(stateCode)) {
          stateCountMap[stateCode] = (stateCountMap[stateCode] || 0) + 1
        }
      }
    })
    
    return Object.entries(stateCountMap).map(([state, count]) => ({
      state,
      count,
    }))
  }, [orders])

  return (
    <div>
      <h2 style={{ 
        marginBottom: 24, 
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        🚚 物流管理
      </h2>

      <Card className="chart-card">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0', color: '#8b949e' }}>
            正在加载订单数据...
          </div>
        ) : stateOrderData.length > 0 ? (
          <StateHeatmap data={stateOrderData} height={600} />
        ) : (
          <div style={{ textAlign: 'center', padding: '50px 0', color: '#8b949e' }}>
            暂无包含地址信息的订单数据，无法显示地图热力图
            <br />
            <span style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px', display: 'block' }}>
              请确保导入的订单数据包含州/省份信息（如 CA, NY 等州代码）
            </span>
          </div>
        )}
      </Card>
    </div>
  )
}

export default Logistics

