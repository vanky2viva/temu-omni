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
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ArrowUpOutlined style={{ color: '#60a5fa' }} />
          <span>运营指标速览</span>
        </span>
      }
      className="frog-gpt-section-card"
      styles={{ body: { padding: '16px' }, header: { background: 'transparent', color: '#e2e8f0' } }}
    >
      <Row gutter={[12, 12]}>
        {metrics.map((metric, index) => (
          <Col span={12} key={index}>
            <Card
              className="frog-gpt-section-card"
              style={{
                background: 'linear-gradient(135deg, rgba(96, 165, 250, 0.08), rgba(15, 23, 42, 0.9))',
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
                        marginLeft: 6,
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
