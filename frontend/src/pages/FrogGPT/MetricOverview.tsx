import React from 'react'
import { Card, Typography, Statistic } from 'antd'
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
      styles={{ 
        body: { padding: '6px' }, 
        header: { 
          background: 'transparent', 
          color: '#e2e8f0',
          borderBottom: '1px solid rgba(96, 165, 250, 0.2)',
          padding: '4px 8px'
        },
        root: { width: '100%', maxWidth: '100%', position: 'relative', zIndex: 1 }
      }}
    >
      <div style={{ display: 'flex', gap: '6px', width: '100%' }}>
        {metrics.map((metric, index) => (
          <div key={index} style={{ flex: 1, minWidth: 0 }}>
            <Card
              className="frog-gpt-section-card"
              style={{
                background: 'linear-gradient(135deg, rgba(96, 165, 250, 0.12), rgba(15, 23, 42, 0.95))',
                width: '100%',
                maxWidth: '100%',
                border: '1px solid rgba(96, 165, 250, 0.2)',
                backdropFilter: 'blur(10px)',
                height: '100%',
              }}
              styles={{ 
                body: { padding: '4px' },
                root: { 
                  width: '100%', 
                  maxWidth: '100%',
                  position: 'relative',
                  zIndex: 1,
                  height: '100%',
                }
              }}
            >
              <Statistic
                title={
                  <Text style={{ color: '#94a3b8', fontSize: '12px' }}>
                    {metric.label}
                  </Text>
                }
                value={metric.value}
                valueStyle={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}
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
          </div>
        ))}
      </div>
    </Card>
  )
}

export default MetricOverview
