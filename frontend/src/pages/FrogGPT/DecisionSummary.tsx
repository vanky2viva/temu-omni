import React from 'react'
import { Card, Tag, Typography, List, Space } from 'antd'
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { DecisionData } from './types'

const { Text, Paragraph } = Typography

interface DecisionSummaryProps {
  decisionData: DecisionData | null
}

const DecisionSummary: React.FC<DecisionSummaryProps> = ({ decisionData }) => {
  if (!decisionData) {
    return (
      <Card
        title="AI 决策结果"
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
        <Text type="secondary" style={{ color: '#64748b' }}>
          暂无决策数据，请在右侧对话中与 FrogGPT 交互
        </Text>
      </Card>
    )
  }

  const getRiskLevelConfig = (level?: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low':
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          text: '低风险',
        }
      case 'medium':
        return {
          color: 'warning',
          icon: <WarningOutlined />,
          text: '中风险',
        }
      case 'high':
        return {
          color: 'error',
          icon: <CloseCircleOutlined />,
          text: '高风险',
        }
      default:
        return {
          color: 'default',
          icon: null,
          text: '未知',
        }
    }
  }

  const riskConfig = getRiskLevelConfig(decisionData.riskLevel)

  return (
    <Card
      title="AI 决策结果"
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
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 风险等级标签 */}
        {decisionData.riskLevel && (
          <Tag
            color={riskConfig.color}
            icon={riskConfig.icon}
            style={{ fontSize: '14px', padding: '4px 12px' }}
          >
            {riskConfig.text}
          </Tag>
        )}

        {/* 决策总结 */}
        {decisionData.decisionSummary && (
          <Paragraph style={{ color: '#e2e8f0', margin: 0 }}>
            {decisionData.decisionSummary}
          </Paragraph>
        )}

        {/* 动作建议列表 */}
        {decisionData.actions && decisionData.actions.length > 0 && (
          <div>
            <Text strong style={{ color: '#fff', display: 'block', marginBottom: '8px' }}>
              建议动作：
            </Text>
            <List
              dataSource={decisionData.actions}
              renderItem={(action, index) => (
                <List.Item style={{ padding: '8px 0', border: 'none' }}>
                  <Card
                    size="small"
                    style={{
                      background: '#0f172a',
                      borderColor: '#1E293B',
                      borderRadius: '8px',
                      width: '100%',
                    }}
                    styles={{ body: { padding: '12px' } }}
                  >
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <div>
                        <Text strong style={{ color: '#60a5fa' }}>
                          {action.type}
                        </Text>
                        {action.target && (
                          <Text style={{ color: '#94a3b8', marginLeft: '8px' }}>
                            → {action.target}
                          </Text>
                        )}
                      </div>
                      {action.delta && (
                        <Text style={{ color: '#52c41a', fontSize: '12px' }}>
                          预期变化: {action.delta}
                        </Text>
                      )}
                      {action.reason && (
                        <Text style={{ color: '#64748b', fontSize: '12px' }}>
                          {action.reason}
                        </Text>
                      )}
                    </Space>
                  </Card>
                </List.Item>
              )}
            />
          </div>
        )}
      </Space>
    </Card>
  )
}

export default DecisionSummary

