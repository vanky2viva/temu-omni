import React from 'react'
import { Card, Row, Col, Spin, Statistic } from 'antd'
import { DollarOutlined, RiseOutlined } from '@ant-design/icons'

interface FinanceOverviewProps {
  stats: any
  loading: boolean
  isMobile: boolean
}

const FinanceOverview: React.FC<FinanceOverviewProps> = ({ stats, loading, isMobile }) => {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={8}>
        <Card loading={loading} style={{ background: 'linear-gradient(135deg, rgba(88, 166, 255, 0.15) 0%, rgba(88, 166, 255, 0.05) 100%)' }}>
          <Statistic
            title="GMV"
            value={stats?.total_gmv || 0}
            prefix={<DollarOutlined />}
            precision={2}
            valueStyle={{ color: '#58a6ff' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <Card loading={loading} style={{ background: 'linear-gradient(135deg, rgba(82, 196, 26, 0.15) 0%, rgba(82, 196, 26, 0.05) 100%)' }}>
          <Statistic
            title="利润"
            value={stats?.total_profit || 0}
            prefix={<RiseOutlined />}
            precision={2}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <Card loading={loading} style={{ background: 'linear-gradient(135deg, rgba(114, 46, 209, 0.15) 0%, rgba(114, 46, 209, 0.05) 100%)' }}>
          <Statistic
            title="利润率"
            value={stats?.total_gmv ? (stats.total_profit / stats.total_gmv * 100) : 0}
            suffix="%"
            precision={2}
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
    </Row>
  )
}

export default FinanceOverview

