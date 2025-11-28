import React, { useState, useRef, useEffect } from 'react'
import { Card, Typography, Button, Spin, message, Input, Space, Avatar } from 'antd'
import { ClearOutlined, RobotOutlined, UserOutlined, SendOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'
import type { ChatMessage, DecisionData } from './types'

const { Text } = Typography
const { TextArea } = Input

interface AiChatPanelProps {
  shopId?: string
  shopName?: string
  onDecisionParsed?: (data: DecisionData | null) => void
}

/**
 * 模拟 AI 回复（临时使用，后续替换为真实 API 调用）
 */
const mockAiReply = (userMessage: string): string => {
  // 返回一个包含 markdown 和 JSON 代码块的示例回复
  return `根据您的问题"${userMessage}"，我为您分析了最近7天的数据：

## 分析结果

1. **GMV 趋势**：最近7天GMV为 ¥1789.4k，较上期增长 12.3%
2. **订单量**：总订单数 7,488 单，平均每日 1,069 单
3. **利润率**：当前利润率 13.10%，处于健康水平

## 决策建议

\`\`\`json
{
  "decisionSummary": "整体运营状况良好，建议继续保持当前策略，同时关注高退货率SKU的优化。",
  "riskLevel": "low",
  "actions": [
    {
      "type": "优化SKU",
      "target": "SKU-12345",
      "delta": "退货率降低 5%",
      "reason": "该SKU退货率较高，建议检查商品描述和图片准确性"
    },
    {
      "type": "提升转化",
      "target": "标题优化",
      "delta": "点击率提升 10%",
      "reason": "建议使用更具吸引力的标题，突出产品卖点"
    }
  ]
}
\`\`\`

希望这些建议对您有帮助！`
}

/**
 * 从 markdown 内容中提取 JSON 决策数据
 */
const extractDecisionFromMarkdown = (content: string): DecisionData | null => {
  try {
    // 使用正则表达式提取 ```json ... ``` 代码块
    const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/)
    if (jsonMatch && jsonMatch[1]) {
      const jsonStr = jsonMatch[1].trim()
      const decisionData = JSON.parse(jsonStr) as DecisionData
      return decisionData
    }
  } catch (error) {
    console.error('解析决策 JSON 失败:', error)
  }
  return null
}

const AiChatPanel: React.FC<AiChatPanelProps> = ({ shopId, shopName, onDecisionParsed }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      key: 'welcome',
      role: 'assistant',
      content: '👋 欢迎使用 FrogGPT！我是您的 AI 运营助手。\n\n我可以帮您：\n- 分析销售数据和趋势\n- 提供运营决策建议\n- 回答关于店铺和商品的问题\n\n请随时向我提问！',
      timestamp: new Date(),
    },
  ])
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /**
   * 处理发送消息
   */
  const handleSend = async () => {
    const value = inputValue.trim()
    if (!value) {
      message.warning('请输入消息')
      return
    }

    // 添加用户消息
    const userMessage: ChatMessage = {
      key: `user-${Date.now()}`,
      role: 'user',
      content: value,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      // 模拟 AI 回复（后续替换为真实 API 调用）
      await new Promise((resolve) => setTimeout(resolve, 1000)) // 模拟网络延迟
      const aiResponse = mockAiReply(value)

      // 添加助手消息
      const assistantMessage: ChatMessage = {
        key: `assistant-${Date.now()}`,
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // 解析 JSON 决策片段
      const decisionData = extractDecisionFromMarkdown(aiResponse)
      // 回传决策数据给左侧卡片
      if (onDecisionParsed) {
        onDecisionParsed(decisionData)
      }
    } catch (error) {
      message.error('发送消息失败')
      console.error('发送消息错误:', error)
    } finally {
      setLoading(false)
    }
  }

  /**
   * 处理键盘事件
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  /**
   * 清空对话
   */
  const handleClear = () => {
    setMessages([
      {
        key: 'welcome',
        role: 'assistant',
        content: '对话已清空，请继续提问。',
        timestamp: new Date(),
      },
    ])
    if (onDecisionParsed) {
      onDecisionParsed(null)
    }
  }

  return (
    <Card
      style={{
        background: '#020617',
        borderColor: '#1E293B',
        borderRadius: '16px',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      styles={{
        body: {
          padding: 0,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
        flexDirection: 'column',
      }}
    >
      {/* 顶部标题栏 */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #1E293B',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <Text strong style={{ color: '#fff', fontSize: '16px', display: 'block' }}>
            FrogGPT 对话
          </Text>
          <Text type="secondary" style={{ color: '#64748b', fontSize: '12px' }}>
            右侧智能对话，左侧展示分析和决策结果
          </Text>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {shopName && (
            <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px' }}>
              {shopName}
            </Text>
          )}
          <Button
            type="text"
            icon={<ClearOutlined />}
            onClick={handleClear}
            style={{ color: '#94a3b8' }}
          >
            清空对话
          </Button>
        </div>
      </div>

      {/* 消息列表区域 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          background: '#020617',
        }}
      >
        {messages.map((item) => {
          if (item.role === 'user') {
            return (
              <div
                key={item.key}
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  marginBottom: '16px',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    background: '#1e40af',
                    color: '#fff',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    maxWidth: '70%',
                    wordBreak: 'break-word',
                  }}
                >
                  {item.content}
                </div>
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1e40af', flexShrink: 0 }} />
              </div>
            )
          } else {
            return (
              <div
                key={item.key}
                style={{
                  display: 'flex',
                  justifyContent: 'flex-start',
                  marginBottom: '16px',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1e293b', flexShrink: 0 }} />
                <div
                  style={{
                    background: '#1e293b',
                    color: '#e2e8f0',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    maxWidth: '70%',
                    wordBreak: 'break-word',
                  }}
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw, rehypeSanitize]}
                  >
                    {item.content}
                  </ReactMarkdown>
                </div>
              </div>
            )
          }
        })}
        {loading && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: '#94a3b8',
              marginTop: '16px',
            }}
          >
            <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1e293b', flexShrink: 0 }} />
            <div
              style={{
                background: '#1e293b',
                color: '#e2e8f0',
                padding: '12px 16px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Spin size="small" />
              <Text type="secondary" style={{ color: '#94a3b8' }}>
                FrogGPT 正在思考...
              </Text>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 底部输入区 */}
      <div
        style={{
          padding: '16px 20px',
          borderTop: '1px solid #1E293B',
          background: '#020617',
        }}
      >
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="向 FrogGPT 提问，例如：分析最近 7 天 GMV 变化原因"
            autoSize={{ minRows: 1, maxRows: 6 }}
            disabled={loading}
            style={{
              flex: 1,
              background: '#0f172a',
              borderColor: '#1E293B',
              color: '#fff',
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            disabled={!inputValue.trim()}
            style={{
              background: '#1e40af',
              borderColor: '#1e40af',
            }}
          >
            发送
          </Button>
        </Space.Compact>
      </div>
    </Card>
  )
}

export default AiChatPanel
