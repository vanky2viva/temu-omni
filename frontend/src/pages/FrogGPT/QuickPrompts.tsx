import React from 'react'
import { Card, Button, Space, Typography } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import type { QuickPrompt } from './types'

const { Text } = Typography

interface QuickPromptsProps {
  prompts: QuickPrompt[]
  onPromptClick: (prompt: string) => void
}

const QuickPrompts: React.FC<QuickPromptsProps> = ({ prompts, onPromptClick }) => {
  return (
    <Card
      title="快捷问题"
      style={{
        background: '#020617',
        borderColor: '#1E293B',
        borderRadius: '12px',
      }}
      headStyle={{
        color: '#fff',
        borderBottomColor: '#1E293B',
      }}
      styles={{ body: { padding: '16px' } }}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {prompts.map((prompt, index) => (
          <Button
            key={index}
            type="text"
            icon={<ThunderboltOutlined />}
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
              e.currentTarget.style.color = '#fff'
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
    </Card>
  )
}

export default QuickPrompts

