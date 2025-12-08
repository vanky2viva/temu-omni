/**
 * AI 结构化决策区组件
 * 显示 RiskLevel 卡片 + Summary 卡片 + Action List 卡片
 */
import React, { useMemo } from 'react'
import { Card, Tag, Typography, List, Space, Badge } from 'antd'
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  RocketOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { ThoughtChain, type ThoughtChainItemType } from '@ant-design/x'
import type { DecisionData } from '../types'

const { Text, Paragraph } = Typography

interface DecisionPanelProps {
  decisionData: DecisionData | null
}

const DecisionPanel: React.FC<DecisionPanelProps> = ({ decisionData }) => {
  const getRiskLevelConfig = (level?: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low':
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          text: '低风险',
          bgColor: 'rgba(72, 199, 116, 0.1)',
          borderColor: '#48c774',
        }
      case 'medium':
        return {
          color: 'warning',
          icon: <WarningOutlined />,
          text: '中风险',
          bgColor: 'rgba(250, 173, 20, 0.1)',
          borderColor: '#faad14',
        }
      case 'high':
        return {
          color: 'error',
          icon: <CloseCircleOutlined />,
          text: '高风险',
          bgColor: 'rgba(241, 70, 104, 0.1)',
          borderColor: '#f14668',
        }
      default:
        return {
          color: 'default',
          icon: null,
          text: '未知',
          bgColor: 'rgba(139, 148, 158, 0.1)',
          borderColor: '#8b949e',
        }
    }
  }

  const getActionPriorityColor = (priority?: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high':
        return '#f14668'
      case 'medium':
        return '#faad14'
      case 'low':
        return '#48c774'
      default:
        return '#8b949e'
    }
  }

  const thoughtChainItems = useMemo<ThoughtChainItemType[]>(() => {
    if (!decisionData) {
      return [
        {
          key: 'pending-data',
          title: '等待 AI 推理',
          description: '在右侧对话中发起问题，FrogGPT 将自动生成决策链路',
          status: 'loading',
        },
      ]
    }

    const items: ThoughtChainItemType[] = []

    if (decisionData.decisionSummary) {
      items.push({
        key: 'summary',
        title: '决策总结',
        description: decisionData.decisionSummary,
        status: 'success',
      })
    }

    decisionData.actions?.forEach((action, index) => {
      items.push({
        key: `action-${index}`,
        title: action.type,
        description: action.reason || action.target,
        footer: action.delta,
        status: 'success',
      })
    })

    if (decisionData.metadata?.analysisDate) {
      items.push({
        key: 'analysis-time',
        title: '分析时间',
        description: decisionData.metadata.analysisDate,
        status: 'success',
      })
    }

    return items
  }, [decisionData])

  if (!decisionData) {
    return (
      <Card
        className="frog-gpt-section-card"
        styles={{
          header: {
            background: 'transparent',
            borderBottom: '1px solid #1E293B',
            color: '#e2e8f0',
          },
          body: { padding: '16px' },
        }}
      >
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px',
          color: '#64748b',
        }}>
          <ThunderboltOutlined style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }} />
          <div>暂无决策数据</div>
          <div style={{ fontSize: '12px', marginTop: '8px' }}>
            请在右侧对话中与 FrogGPT 交互获取 AI 决策建议
          </div>
        </div>
      </Card>
    )
  }

  const riskConfig = getRiskLevelConfig(decisionData.riskLevel)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <Card
        className="frog-gpt-section-card"
        title={
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ThunderboltOutlined style={{ color: '#60a5fa' }} />
            <span>AI 推理链路</span>
          </span>
        }
        styles={{
          header: {
            background: 'transparent',
            borderBottom: '1px solid #1E293B',
            color: '#e2e8f0',
          },
          body: { padding: '12px' },
        }}
      >
        <ThoughtChain
          items={thoughtChainItems}
          className="frog-gpt-thought"
          styles={{
            item: { color: '#e2e8f0' },
          }}
        />
      </Card>

      {/* 风险等级卡片 */}
      {decisionData.riskLevel && (
        <Card
          className="frog-gpt-section-card"
          style={{
            background: riskConfig.bgColor,
            border: `2px solid ${riskConfig.borderColor}`,
            borderRadius: '12px',
          }}
          styles={{
            body: { padding: '16px' },
          }}
        >
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {riskConfig.icon}
              <Text strong style={{ color: '#e2e8f0', fontSize: '14px' }}>
                风险等级
              </Text>
            </div>
            <Tag
              color={riskConfig.color}
              icon={riskConfig.icon}
              style={{
                fontSize: '16px',
                padding: '8px 16px',
                margin: 0,
                border: `1px solid ${riskConfig.borderColor}`,
              }}
            >
              {riskConfig.text}
            </Tag>
            {decisionData.metadata?.confidence && (
              <Text style={{ color: '#94a3b8', fontSize: '12px' }}>
                置信度: {(decisionData.metadata.confidence * 100).toFixed(1)}%
              </Text>
            )}
          </Space>
        </Card>
      )}

      {/* 决策总结卡片 */}
      {decisionData.decisionSummary && (
        <Card
          className="frog-gpt-section-card"
          title={
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <RocketOutlined style={{ color: '#60a5fa' }} />
              <span>决策总结</span>
            </span>
          }
          style={{
            background: '#020617',
            borderColor: '#1E293B',
            borderRadius: '12px',
          }}
          styles={{
            header: {
              background: 'transparent',
              borderBottom: '1px solid #1E293B',
              color: '#e2e8f0',
            },
            body: { padding: '16px' },
          }}
        >
          <Paragraph style={{ color: '#e2e8f0', margin: 0, fontSize: '14px', lineHeight: '1.6' }}>
            {decisionData.decisionSummary}
          </Paragraph>
          {decisionData.metadata?.analysisDate && (
            <Text style={{ color: '#64748b', fontSize: '11px', marginTop: '8px', display: 'block' }}>
              分析时间: {decisionData.metadata.analysisDate}
            </Text>
          )}
        </Card>
      )}

      {/* 动作建议列表卡片 */}
      {decisionData.actions && decisionData.actions.length > 0 && (
        <Card
          className="frog-gpt-section-card"
          title={
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ThunderboltOutlined style={{ color: '#60a5fa' }} />
              <span>建议动作</span>
              <Badge count={decisionData.actions.length} style={{ backgroundColor: '#60a5fa' }} />
            </span>
          }
          style={{
            background: '#020617',
            borderColor: '#1E293B',
            borderRadius: '12px',
          }}
          styles={{
            header: {
              background: 'transparent',
              borderBottom: '1px solid #1E293B',
              color: '#e2e8f0',
            },
            body: { padding: '16px' },
          }}
        >
          <List
            dataSource={decisionData.actions}
            renderItem={(action) => (
              <List.Item style={{ padding: '12px 0', border: 'none' }}>
                <Card
                  size="small"
                  style={{
                    background: '#0f172a',
                    border: '1px solid #1E293B',
                    borderRadius: '8px',
                    width: '100%',
                  }}
                  styles={{ body: { padding: '12px' } }}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {action.priority && (
                          <Badge
                            color={getActionPriorityColor(action.priority)}
                            text={action.priority === 'high' ? '高优先级' : action.priority === 'medium' ? '中优先级' : '低优先级'}
                            style={{ fontSize: '10px' }}
                          />
                        )}
                        <Text strong style={{ color: '#60a5fa', fontSize: '14px' }}>
                          {action.type}
                        </Text>
                      </div>
                    </div>
                    {action.target && (
                      <div>
                        <Text style={{ color: '#94a3b8', fontSize: '12px' }}>目标: </Text>
                        <Text style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 500 }}>
                          {action.target}
                        </Text>
                      </div>
                    )}
                    {action.delta && (
                      <div>
                        <Text style={{ color: '#52c41a', fontSize: '12px', fontWeight: 500 }}>
                          📈 预期变化: {action.delta}
                        </Text>
                      </div>
                    )}
                    {action.estimatedImpact && (
                      <div>
                        <Text style={{ color: '#ffdd57', fontSize: '12px' }}>
                          💡 预估影响: {action.estimatedImpact}
                        </Text>
                      </div>
                    )}
                    {action.reason && (
                      <div>
                        <Text style={{ color: '#64748b', fontSize: '12px', lineHeight: '1.5' }}>
                          {action.reason}
                        </Text>
                      </div>
                    )}
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  )
}

export default DecisionPanel









