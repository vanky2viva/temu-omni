import { Card, Space, Typography, Tag, Divider } from 'antd'
import { Actions, ThoughtChain, type ThoughtChainItemType } from '@ant-design/x'
import { ThunderboltOutlined, ClockCircleOutlined, LineChartOutlined, AlertOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { DecisionData } from '../types'

const { Text } = Typography

interface DecisionHybridBoardProps {
  decisionData: DecisionData | null
}

const priorityIcon: Record<string, React.ReactNode> = {
  high: <AlertOutlined style={{ color: '#f97316' }} />,
  medium: <LineChartOutlined style={{ color: '#0ea5e9' }} />,
  low: <CheckCircleOutlined style={{ color: '#22c55e' }} />,
}

export default function DecisionHybridBoard({ decisionData }: DecisionHybridBoardProps) {
  if (!decisionData) {
    return (
      <Card
        className="frog-gpt-section-card"
        styles={{ 
          body: { padding: '6px' },
          header: { padding: '4px 8px' }
        }}
        title={
          <Space>
            <ThunderboltOutlined style={{ color: '#60a5fa' }} />
            <span>AI 决策链路</span>
          </Space>
        }
      >
        <Text type="secondary" style={{ color: '#94a3b8' }}>
          发送问题后，FrogGPT 将实时解析 Markdown 中的决策 JSON，生成可操作的决策卡片。
        </Text>
      </Card>
    )
  }

  const thoughtItems: ThoughtChainItemType[] = [
    {
      key: 'summary',
      title: '决策总结',
      description: decisionData.decisionSummary || '正在生成…',
      status: decisionData.decisionSummary ? 'success' : 'loading',
    },
  ]

  if (decisionData.metadata?.analysisDate) {
    thoughtItems.push({
      key: 'analysis-date',
      title: '分析时间',
      description: decisionData.metadata.analysisDate,
      status: 'success',
    })
  }

  if (decisionData.metadata?.dataRange) {
    thoughtItems.push({
      key: 'data-range',
      title: '数据范围',
      description: decisionData.metadata.dataRange,
      status: 'success',
    })
  }

  const actions = decisionData.actions?.map((action, index) => ({
    key: `${action.type}-${index}`,
    label: action.type,
    icon: priorityIcon[action.priority || ''] || <LineChartOutlined />,
    danger: action.priority === 'high',
    actionRender: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
        <div style={{ 
          color: '#e2e8f0', 
          fontWeight: 600, 
          fontSize: '12px',
          lineHeight: 1.4,
          marginBottom: '2px'
        }}>
          {action.target}
        </div>
        {action.delta && (
          <Text style={{ 
            color: '#60a5fa', 
            fontSize: '11px',
            fontWeight: 500,
            display: 'block'
          }}>
            {action.delta}
          </Text>
        )}
        {action.reason && (
          <Text type="secondary" style={{ 
            color: '#94a3b8', 
            fontSize: '11px',
            lineHeight: 1.4,
            display: 'block',
            marginTop: '2px'
          }}>
            {action.reason}
          </Text>
        )}
      </div>
    ),
  })) || []

  const riskTag = (() => {
    switch (decisionData.riskLevel) {
      case 'high':
        return <Tag color="error">高风险</Tag>
      case 'medium':
        return <Tag color="warning">中风险</Tag>
      case 'low':
        return <Tag color="success">低风险</Tag>
      default:
        return <Tag>未知</Tag>
    }
  })()

  return (
    <Card
      className="frog-gpt-section-card"
      styles={{ 
        body: { padding: '4px 6px' },
        root: { width: '100%', maxWidth: '100%', position: 'relative', zIndex: 1 },
        header: { 
          background: 'transparent',
          borderBottom: '1px solid rgba(96, 165, 250, 0.2)',
          padding: '4px 8px',
          minHeight: '32px'
        }
      }}
      title={
        <Space size="small">
          <ThunderboltOutlined style={{ color: '#60a5fa', fontSize: '13px' }} />
          <span style={{ fontSize: '12px', fontWeight: 600 }}>AI 决策链路</span>
          {riskTag}
        </Space>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, position: 'relative', zIndex: 1 }}>
        <ThoughtChain
          items={thoughtItems}
          className="frog-gpt-thought"
          line="solid"
          styles={{ 
            item: { 
              color: '#e2e8f0',
              padding: '6px 10px',
              fontSize: '12px',
              minHeight: 'auto'
            },
            itemHeader: {
              fontSize: '12px',
              fontWeight: 500,
              marginBottom: '2px'
            },
            itemContent: {
              fontSize: '11px',
              color: '#94a3b8',
              lineHeight: 1.4
            },
            root: { 
              position: 'relative', 
              zIndex: 1,
              marginBottom: '4px'
            }
          }}
        />

        {actions.length > 0 && (
          <Card
            size="small"
            style={{ 
              background: 'linear-gradient(135deg, rgba(11, 18, 32, 0.95), rgba(15, 23, 42, 0.85))',
              borderColor: 'rgba(96, 165, 250, 0.3)',
              position: 'relative', 
              zIndex: 1,
              backdropFilter: 'blur(10px)',
              boxShadow: '0 2px 8px rgba(96, 165, 250, 0.15)',
              marginTop: '4px'
            }}
            styles={{ 
              body: { padding: '6px 8px' },
              root: { position: 'relative', zIndex: 1 },
              header: {
                background: 'transparent',
                borderBottom: '1px solid rgba(96, 165, 250, 0.2)',
                padding: '4px 6px',
                minHeight: '28px'
              }
            }}
            title={
              <Space size="small">
                <LineChartOutlined style={{ color: '#60a5fa', fontSize: '12px' }} />
                <span style={{ fontSize: '11px', fontWeight: 500 }}>执行动作</span>
              </Space>
            }
          >
            <Actions
              items={actions}
              variant="outlined"
              styles={{
                root: { gap: 6, position: 'relative', zIndex: 1 },
                item: { 
                  background: 'rgba(15, 23, 42, 0.8)', 
                  color: '#e2e8f0',
                  borderColor: 'rgba(96, 165, 250, 0.3)',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  transition: 'all 0.2s',
                  fontSize: '12px'
                },
              }}
            />
          </Card>
        )}

        {(decisionData.metadata?.confidence !== undefined || decisionData.metadata?.analysisDate || decisionData.metadata?.dataRange) && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: '4px', paddingTop: '4px', borderTop: '1px solid rgba(31, 41, 55, 0.5)' }}>
            {decisionData.metadata?.confidence !== undefined && (
              <Tag color="blue" style={{ margin: 0, padding: '4px 8px', fontSize: '11px', borderRadius: '4px' }}>
                <ClockCircleOutlined style={{ fontSize: '10px' }} /> 置信度 {Math.round(decisionData.metadata.confidence * 100)}%
              </Tag>
            )}
            {decisionData.metadata?.analysisDate && (
              <Tag color="geekblue" style={{ margin: 0, padding: '4px 8px', fontSize: '11px', borderRadius: '4px' }}>
                <ClockCircleOutlined style={{ fontSize: '10px' }} /> {decisionData.metadata.analysisDate}
              </Tag>
            )}
            {decisionData.metadata?.dataRange && (
              <Tag color="purple" style={{ margin: 0, padding: '4px 8px', fontSize: '11px', borderRadius: '4px' }}>
                数据范围 {decisionData.metadata.dataRange}
              </Tag>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
