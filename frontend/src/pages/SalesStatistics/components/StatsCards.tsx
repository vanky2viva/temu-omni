import React from 'react'
import { ShoppingOutlined, BarChartOutlined, DollarOutlined, TrophyOutlined } from '@ant-design/icons'

interface StatsCardsProps {
  data: any
  isMobile: boolean
}

const StatsCards: React.FC<StatsCardsProps> = ({ data, isMobile }) => {
  const gmv = data?.total_gmv || 0
  const orders = data?.total_orders || 0
  const profit = data?.total_profit ?? 0

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
      <div className="bulma-card" style={{ padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#8b949e' }}>
          <ShoppingOutlined style={{ color: '#00d1b2' }} />
          <span>总销量</span>
        </div>
        <div style={{ fontSize: 24, fontWeight: 'bold', color: '#fff' }}>{(data?.total_quantity || 0).toLocaleString()}</div>
      </div>
      <div className="bulma-card" style={{ padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#8b949e' }}>
          <BarChartOutlined style={{ color: '#3273dc' }} />
          <span>总订单数</span>
        </div>
        <div style={{ fontSize: 24, fontWeight: 'bold', color: '#3273dc' }}>{orders.toLocaleString()}</div>
      </div>
      <div className="bulma-card" style={{ padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#8b949e' }}>
          <DollarOutlined style={{ color: '#ffdd57' }} />
          <span>GMV</span>
        </div>
        <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ffdd57' }}>¥{(gmv/1000).toFixed(1)}k</div>
      </div>
      <div className="bulma-card" style={{ padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#8b949e' }}>
          <TrophyOutlined style={{ color: profit >= 0 ? '#48c774' : '#f14668' }} />
          <span>利润</span>
        </div>
        <div style={{ fontSize: 24, fontWeight: 'bold', color: profit >= 0 ? '#48c774' : '#f14668' }}>¥{(profit/1000).toFixed(1)}k</div>
      </div>
    </div>
  )
}

export default StatsCards

