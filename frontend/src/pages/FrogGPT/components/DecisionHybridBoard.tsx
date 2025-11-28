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
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{action.target}</div>
        {action.delta && <Text style={{ color: '#60a5fa' }}>{action.delta}</Text>}
        {action.reason && <Text type="secondary" style={{ color: '#94a3b8' }}>{action.reason}</Text>}
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
        body: { padding: '6px' },
        root: { width: '100%', maxWidth: '100%', position: 'relative', zIndex: 1 },
        header: { 
          background: 'transparent',
          borderBottom: '1px solid rgba(96, 165, 250, 0.2)',
          padding: '6px 10px'
        }
      }}
      title={
        <Space>
          <ThunderboltOutlined style={{ color: '#60a5fa', fontSize: '14px' }} />
          <span style={{ fontSize: '13px', fontWeight: 600 }}>AI 决策链路</span>
          {riskTag}
        </Space>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, position: 'relative', zIndex: 1 }}>
        <ThoughtChain
          items={thoughtItems}
          className="frog-gpt-thought"
          styles={{ 
            item: { color: '#e2e8f0' },
            root: { position: 'relative', zIndex: 1 }
          }}
        />

        {actions.length > 0 && (
          <Card
            size="small"
            style={{ 
              background: 'linear-gradient(135deg, rgba(11, 18, 32, 0.9), rgba(15, 23, 42, 0.7))',
              borderColor: 'rgba(96, 165, 250, 0.2)',
              position: 'relative', 
              zIndex: 1,
              backdropFilter: 'blur(10px)'
            }}
            styles={{ 
              body: { padding: '4px' },
              root: { position: 'relative', zIndex: 1 },
              header: {
                background: 'transparent',
                borderBottom: '1px solid rgba(96, 165, 250, 0.15)',
                padding: '4px 8px'
              }
            }}
            title={
              <Space>
                <LineChartOutlined style={{ color: '#60a5fa' }} />
                <span style={{ fontSize: '12px', fontWeight: 500 }}>执行动作</span>
              </Space>
            }
          >
            <Actions
              items={actions}
              variant="outlined"
              styles={{
                root: { gap: 8, position: 'relative', zIndex: 1 },
                item: { background: '#0f172a', color: '#e2e8f0' },
              }}
            />
          </Card>
        )}

        <Divider style={{ borderColor: '#1f2937', margin: '8px 0' }} />

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {decisionData.metadata?.confidence !== undefined && (
            <Tag color="blue" style={{ margin: 0, padding: '6px 10px' }}>
              <ClockCircleOutlined /> 置信度 {Math.round(decisionData.metadata.confidence * 100)}%
            </Tag>
          )}
          {decisionData.metadata?.analysisDate && (
            <Tag color="geekblue" style={{ margin: 0, padding: '6px 10px' }}>
              <ClockCircleOutlined /> {decisionData.metadata.analysisDate}
            </Tag>
          )}
          {decisionData.metadata?.dataRange && (
            <Tag color="purple" style={{ margin: 0, padding: '6px 10px' }}>
              数据范围 {decisionData.metadata.dataRange}
            </Tag>
          )}
        </div>
      </div>
    </Card>
  )
}
