/**
 * AI 聊天面板组件 V2.0
 * 使用 Ant Design X 组件：Bubble, Sender, XMarkdown
 */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Card, Select, Button, Space, Typography, Avatar, Spin, Input } from 'antd'
import { ClearOutlined, RobotOutlined, UserOutlined, SendOutlined } from '@ant-design/icons'
import { Bubble } from '@ant-design/x'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'
import { frogGptApi } from '@/services/api'
import type { ChatMessage, DecisionData } from '../types'
import { v4 as uuidv4 } from 'uuid'

const { Text } = Typography

interface AiChatPanelV2Props {
  shopId?: string
  shopName?: string
  model?: string
  temperature?: number
  includeSystemData?: boolean
  dataSummaryDays?: number
  onDecisionParsed?: (data: DecisionData | null) => void
  onMessageUpdate?: (messages: ChatMessage[]) => void
  // 外部触发发送消息（用于快捷问题）
  externalMessage?: string | null
  onExternalMessageSent?: () => void
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

const AiChatPanelV2: React.FC<AiChatPanelV2Props> = ({
  shopId,
  shopName,
  model = 'auto',
  temperature = 0.7,
  includeSystemData = true,
  dataSummaryDays = 7,
  onDecisionParsed,
  onMessageUpdate,
  externalMessage,
  onExternalMessageSent,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '👋 欢迎使用 FrogGPT 2.0！我是您的 AI 运营助手。\n\n我可以帮您：\n- 📊 分析销售数据和趋势\n- 🚀 提供运营决策建议\n- 💡 回答关于店铺和商品的问题\n\n请随时向我提问！',
      timestamp: Date.now(),
    },
  ])
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 通知父组件消息更新
  useEffect(() => {
    onMessageUpdate?.(messages)
  }, [messages, onMessageUpdate])

  // 处理外部消息（快捷问题）
  useEffect(() => {
    if (externalMessage && externalMessage.trim()) {
      const sendMessage = async () => {
        const userMessage: ChatMessage = {
          id: uuidv4(),
          role: 'user',
          content: externalMessage.trim(),
          timestamp: Date.now(),
        }

        setMessages(prev => [...prev, userMessage])
        setLoading(true)

        try {
          const response = await frogGptApi.chat({
            messages: [
              ...messages.map(msg => ({
                role: msg.role,
                content: msg.content,
              })),
              {
                role: 'user',
                content: externalMessage.trim(),
              },
            ],
            model,
            temperature,
            include_system_data: includeSystemData,
            data_summary_days: dataSummaryDays,
            shop_id: shopId ? parseInt(shopId) : undefined,
          })

          const assistantMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant',
            content: response.content || response.message || '抱歉，我无法处理您的请求。',
            timestamp: Date.now(),
            thinking: response.thinking,
            sources: response.sources,
          }

          setMessages(prev => [...prev, assistantMessage])

          const decisionData = extractDecisionFromMarkdown(assistantMessage.content)
          if (decisionData) {
            onDecisionParsed?.(decisionData)
          }
        } catch (error: any) {
          console.error('发送消息失败:', error)
          const errorMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant',
            content: `❌ 抱歉，发生了错误：${error.response?.data?.detail || error.message || '未知错误'}`,
            timestamp: Date.now(),
          }
          setMessages(prev => [...prev, errorMessage])
        } finally {
          setLoading(false)
          onExternalMessageSent?.()
        }
      }
      
      sendMessage()
    }
  }, [externalMessage])

  /**
   * 处理发送消息
   */
  const handleSend = useCallback(async (value: string) => {
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: value.trim(),
      timestamp: Date.now(),
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      // 调用 API
      const response = await frogGptApi.chat({
        messages: [
          ...messages.map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          {
            role: 'user',
            content: value.trim(),
          },
        ],
        model,
        temperature,
        include_system_data: includeSystemData,
        data_summary_days: dataSummaryDays,
        shop_id: shopId ? parseInt(shopId) : undefined,
      })

      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: response.content || response.message || '抱歉，我无法处理您的请求。',
        timestamp: Date.now(),
        thinking: response.thinking,
        sources: response.sources,
      }

      setMessages(prev => [...prev, assistantMessage])

      // 提取决策数据
      const decisionData = extractDecisionFromMarkdown(assistantMessage.content)
      if (decisionData) {
        onDecisionParsed?.(decisionData)
      }
    } catch (error: any) {
      console.error('发送消息失败:', error)
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: `❌ 抱歉，发生了错误：${error.response?.data?.detail || error.message || '未知错误'}`,
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }, [messages, model, temperature, includeSystemData, dataSummaryDays, shopId, onDecisionParsed])

  /**
   * 清空对话
   */
  const handleClear = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: '👋 欢迎使用 FrogGPT 2.0！我是您的 AI 运营助手。\n\n我可以帮您：\n- 📊 分析销售数据和趋势\n- 🚀 提供运营决策建议\n- 💡 回答关于店铺和商品的问题\n\n请随时向我提问！',
        timestamp: Date.now(),
      },
    ])
    onDecisionParsed?.(null)
  }

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Text strong style={{ color: '#e2e8f0', fontSize: '16px' }}>
              FrogGPT 对话
            </Text>
            <Text style={{ color: '#64748b', fontSize: '12px', marginLeft: '12px' }}>
              右侧智能对话，左侧展示分析和决策结果
            </Text>
          </div>
          <Space>
            {shopName && (
              <Select
                value={shopName}
                style={{ width: 120 }}
                size="small"
                disabled
                options={[{ label: shopName, value: shopName }]}
              />
            )}
            <Button
              type="text"
              icon={<ClearOutlined />}
              onClick={handleClear}
              style={{ color: '#94a3b8' }}
            >
              清空对话
            </Button>
          </Space>
        </div>
      }
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: '#020617',
        borderColor: '#1E293B',
        borderRadius: '12px',
      }}
      styles={{
        header: {
          background: 'transparent',
          borderBottom: '1px solid #1E293B',
          padding: '12px 16px',
        },
        body: {
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden',
        },
      }}
    >
      {/* 消息列表区域 */}
      <div
        ref={scrollContainerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          background: '#0f172a',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {messages.map((message) => (
            <div key={message.id} style={{ display: 'flex', gap: '12px' }}>
              {message.role === 'user' ? (
                <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'flex-end' }}>
                  <Bubble
                    placement="right"
                    style={{
                      maxWidth: '70%',
                    }}
                  >
                    <div style={{ color: '#e2e8f0', whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </div>
                  </Bubble>
                  <Avatar
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#60a5fa', flexShrink: 0 }}
                  />
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '12px', width: '100%' }}>
                  <Avatar
                    icon={<RobotOutlined />}
                    style={{ backgroundColor: '#00d1b2', flexShrink: 0 }}
                  />
                  <Bubble
                    placement="left"
                    style={{
                      maxWidth: '70%',
                    }}
                  >
                    {/* 使用 react-markdown 渲染 markdown 内容 */}
                    <div style={{ color: '#e2e8f0' }}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw, rehypeSanitize]}
                        components={{
                          code: ({ node, inline, className, children, ...props }: any) => {
                            const match = /language-(\w+)/.exec(className || '')
                            const isJson = match && match[1] === 'json'
                            return !inline && isJson ? (
                              <div style={{ 
                                background: '#0f172a', 
                                padding: '12px', 
                                borderRadius: '6px',
                                marginTop: '8px',
                                overflow: 'auto',
                              }}>
                                <pre style={{ margin: 0, color: '#e2e8f0' }}>
                                  <code {...props} className={className}>
                                    {children}
                                  </code>
                                </pre>
                              </div>
                            ) : (
                              <code className={className} {...props} style={{ 
                                background: '#1e293b', 
                                padding: '2px 6px', 
                                borderRadius: '3px',
                                color: '#60a5fa',
                              }}>
                                {children}
                              </code>
                            )
                          },
                          p: ({ children }: any) => <p style={{ margin: '4px 0' }}>{children}</p>,
                          h1: ({ children }: any) => <h1 style={{ color: '#e2e8f0', fontSize: '18px', margin: '8px 0' }}>{children}</h1>,
                          h2: ({ children }: any) => <h2 style={{ color: '#e2e8f0', fontSize: '16px', margin: '6px 0' }}>{children}</h2>,
                          h3: ({ children }: any) => <h3 style={{ color: '#e2e8f0', fontSize: '14px', margin: '4px 0' }}>{children}</h3>,
                          ul: ({ children }: any) => <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>{children}</ul>,
                          li: ({ children }: any) => <li style={{ margin: '2px 0', color: '#e2e8f0' }}>{children}</li>,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    {message.thinking && (
                      <div style={{ marginTop: '8px', padding: '8px', background: '#1e293b', borderRadius: '4px' }}>
                        <Text style={{ color: '#94a3b8', fontSize: '12px' }}>
                          💭 思考过程: {message.thinking}
                        </Text>
                      </div>
                    )}
                    {message.sources && message.sources.length > 0 && (
                      <div style={{ marginTop: '8px' }}>
                        <Text style={{ color: '#94a3b8', fontSize: '12px' }}>来源:</Text>
                        {message.sources.map((source, idx) => (
                          <div key={idx} style={{ marginTop: '4px' }}>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: '#60a5fa', fontSize: '12px' }}
                            >
                              {source.title}
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </Bubble>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Avatar
                icon={<RobotOutlined />}
                style={{ backgroundColor: '#00d1b2', flexShrink: 0 }}
              />
              <Bubble placement="left">
                <Spin size="small" />
                <Text style={{ color: '#94a3b8', marginLeft: '8px' }}>正在思考...</Text>
              </Bubble>
            </div>
          )}
          <div ref={messagesEndRef} />
        </Space>
      </div>

      {/* 输入区域 */}
      <div style={{ padding: '16px', borderTop: '1px solid #1E293B', background: '#020617' }}>
        {/* 使用 Sender 组件，如果不可用则使用 Input + Button */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <Input.TextArea
            placeholder="向 FrogGPT 提问，例如：分析最近7天 GMV 变化原因"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey && !loading && inputValue.trim()) {
                handleSend(inputValue)
                setInputValue('')
              }
            }}
            disabled={loading}
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{
              background: '#0f172a',
              borderColor: '#1E293B',
              color: '#e2e8f0',
              flex: 1,
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => {
              if (inputValue.trim() && !loading) {
                handleSend(inputValue)
                setInputValue('')
              }
            }}
            loading={loading}
            disabled={loading || !inputValue.trim()}
            style={{
              background: '#60a5fa',
              borderColor: '#60a5fa',
            }}
          >
            发送
          </Button>
        </div>
      </div>
    </Card>
  )
}

export default AiChatPanelV2

