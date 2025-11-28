import React from 'react'
import { Card, Row, Col, Typography, Statistic } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons'
import type { MetricData } from './types'

const { Text } = Typography

interface MetricOverviewProps {
  metrics: MetricData[]
}

const MetricOverview: React.FC<MetricOverviewProps> = ({ metrics }) => {
  const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <ArrowUpOutlined style={{ color: '#52c41a' }} />
      case 'down':
        return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <MinusOutlined style={{ color: '#8c8c8c' }} />
    }
  }

  return (
    <Card
      title="运营指标速览"
      style={{
        background: '#020617',
        borderColor: '#1E293B',
        borderRadius: '12px',
        marginBottom: '16px',
      }}
      headStyle={{
        color: '#fff',
        borderBottomColor: '#1E293B',
      }}
      styles={{ body: { padding: '16px' } }}
    >
      <Row gutter={[12, 12]}>
        {metrics.map((metric, index) => (
          <Col span={12} key={index}>
            <Card
              style={{
                background: '#0f172a',
                borderColor: '#1E293B',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              }}
              styles={{ body: { padding: '12px' } }}
            >
              <Statistic
                title={
                  <Text style={{ color: '#94a3b8', fontSize: '12px' }}>
                    {metric.label}
                  </Text>
                }
                value={metric.value}
                valueStyle={{ color: '#fff', fontSize: '18px', fontWeight: 'bold' }}
                prefix={getTrendIcon(metric.trend)}
                suffix={
                  metric.trendValue ? (
                    <Text
                      style={{
                        color: metric.trend === 'up' ? '#52c41a' : metric.trend === 'down' ? '#ff4d4f' : '#8c8c8c',
                        fontSize: '12px',
                      }}
                    >
                      {metric.trendValue}
                    </Text>
                  ) : null
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  )
}

export default MetricOverview

