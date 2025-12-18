import React from 'react'
import { Row, Col, Card, Statistic } from 'antd'
import { ShoppingOutlined, DollarOutlined, RiseOutlined } from '@ant-design/icons'

const StatsCards: React.FC<any> = ({ overview, isMobile }) => {
  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ background: 'rgba(250, 140, 22, 0.1)' }}>
          <Statistic title="总订单量" value={overview?.total_orders || 0} prefix={<ShoppingOutlined />} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ background: 'rgba(88, 166, 255, 0.1)' }}>
          <Statistic title="总GMV" value={overview?.total_gmv || 0} prefix={<DollarOutlined />} precision={2} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ background: 'rgba(82, 196, 26, 0.1)' }}>
          <Statistic title="总利润" value={overview?.total_profit || 0} prefix={<RiseOutlined />} precision={2} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ background: 'rgba(114, 46, 209, 0.1)' }}>
          <Statistic title="利润率" value={overview?.profit_margin || 0} suffix="%" precision={2} />
        </Card>
      </Col>
    </Row>
  )
}

export default StatsCards

