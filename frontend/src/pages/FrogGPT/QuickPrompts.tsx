/**
 * 快捷问题组件
 * 支持推荐问题、标准模板问题、自定义问题库
 */
import React from 'react'
import { Card, Button, Space, Typography, Divider } from 'antd'
import {
  ThunderboltOutlined,
  BarChartOutlined,
  RocketOutlined,
  FileTextOutlined,
  StarOutlined,
} from '@ant-design/icons'
import type { QuickPrompt } from './types'

const { Text } = Typography

interface QuickPromptsProps {
  prompts: QuickPrompt[]
  onPromptClick: (prompt: string) => void
}

const QuickPrompts: React.FC<QuickPromptsProps> = ({ prompts, onPromptClick }) => {
  // 按分类分组
  const categorizedPrompts = React.useMemo(() => {
    const categories: Record<string, QuickPrompt[]> = {
      analysis: [],
      optimization: [],
      report: [],
      custom: [],
    }
    
    prompts.forEach(prompt => {
      const category = prompt.category || 'custom'
      if (categories[category]) {
        categories[category].push(prompt)
      }
    })
    
    return categories
  }, [prompts])

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'analysis':
        return <BarChartOutlined />
      case 'optimization':
        return <RocketOutlined />
      case 'report':
        return <FileTextOutlined />
      default:
        return <ThunderboltOutlined />
    }
  }

  const getCategoryLabel = (category?: string) => {
    switch (category) {
      case 'analysis':
        return '数据分析'
      case 'optimization':
        return '优化建议'
      case 'report':
        return '报告生成'
      default:
        return '自定义'
    }
  }

  return (
    <Card
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ThunderboltOutlined style={{ color: '#60a5fa' }} />
          <span>快捷问题</span>
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
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 推荐问题 */}
        {categorizedPrompts.analysis.length > 0 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <StarOutlined style={{ color: '#ffdd57', fontSize: '12px' }} />
              <Text style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 500 }}>
                推荐问题
              </Text>
            </div>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {categorizedPrompts.analysis.slice(0, 2).map((prompt) => (
                <Button
                  key={prompt.id || prompt.label}
                  type="text"
                  icon={getCategoryIcon(prompt.category)}
                  onClick={() => onPromptClick(prompt.prompt)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    color: '#94a3b8',
                    borderColor: '#1E293B',
                    background: '#0f172a',
                    height: 'auto',
                    padding: '8px 12px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#1e293b'
                    e.currentTarget.style.color = '#60a5fa'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#0f172a'
                    e.currentTarget.style.color = '#94a3b8'
                  }}
                >
                  <Text style={{ fontSize: '13px' }}>{prompt.label}</Text>
                </Button>
              ))}
            </Space>
          </div>
        )}

        {/* 其他分类 */}
        {Object.entries(categorizedPrompts).map(([category, categoryPrompts]) => {
          if (category === 'analysis' || categoryPrompts.length === 0) return null
          
          return (
            <div key={category}>
              <Divider style={{ margin: '8px 0', borderColor: '#1E293B' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                {getCategoryIcon(category)}
                <Text style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 500 }}>
                  {getCategoryLabel(category)}
                </Text>
              </div>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {categoryPrompts.map((prompt) => (
                  <Button
                    key={prompt.id || prompt.label}
                    type="text"
                    icon={getCategoryIcon(prompt.category)}
                    onClick={() => onPromptClick(prompt.prompt)}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      color: '#94a3b8',
                      borderColor: '#1E293B',
                      background: '#0f172a',
                      height: 'auto',
                      padding: '8px 12px',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#1e293b'
                      e.currentTarget.style.color = '#60a5fa'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#0f172a'
                      e.currentTarget.style.color = '#94a3b8'
                    }}
                  >
                    <Text style={{ fontSize: '13px' }}>{prompt.label}</Text>
                  </Button>
                ))}
              </Space>
            </div>
          )
        })}
      </Space>
    </Card>
  )
}

export default QuickPrompts
