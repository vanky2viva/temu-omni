/**
 * AI 聊天面板组件 V2.0
 * 使用 Ant Design X 组件：Bubble, Sender, XMarkdown
 */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Card, Space, Typography, Avatar, Spin } from 'antd'
import { RobotOutlined, UserOutlined } from '@ant-design/icons'
import { Bubble, Sender, ThoughtChain, type SenderProps } from '@ant-design/x'
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
  const messagesRef = useRef<ChatMessage[]>(messages)
  const lastUserMessage = useMemo(
    () => [...messages].reverse().find(msg => msg.role === 'user'),
    [messages],
  )

  const promptItems = useMemo(() => {
    const baseItems = [
      { key: 'summary', label: '生成今日运营总结', description: 'GMV、订单量、利润率要点', icon: <RobotOutlined /> },
      { key: 'gmv', label: '分析最近7天 GMV 异动', description: '洞察变化原因并给优化建议', icon: <RobotOutlined /> },
      { key: 'refund', label: '高退货 SKU 排查', description: '找出Top5并分析原因', icon: <RobotOutlined /> },
      { key: 'title', label: '写3个高转化标题', description: '基于热销商品', icon: <RobotOutlined /> },
      { key: 'profit', label: '利润率提升动作', description: '给出3个可执行动作与预期', icon: <RobotOutlined /> },
    ]

    const text = (lastUserMessage?.content || '').toLowerCase()
    const contextItems = []
    if (text.includes('gmv') || text.includes('销售') || text.includes('营业额')) {
      contextItems.push({ key: 'ctx-gmv', label: '细分 GMV 变化原因', description: '按渠道/类目拆解并给方案', icon: <RobotOutlined /> })
    }
    if (text.includes('退款') || text.includes('退货')) {
      contextItems.push({ key: 'ctx-refund', label: '定位退款率暴涨原因', description: '聚焦近7天、SKU与地区', icon: <RobotOutlined /> })
    }
    if (text.includes('转化') || text.includes('标题')) {
      contextItems.push({ key: 'ctx-title', label: '生成高转化标题+卖点', description: '输出3条并附理由', icon: <RobotOutlined /> })
    }
    if (contextItems.length === 0 && lastUserMessage) {
      contextItems.push({ key: 'ctx-follow', label: '继续深挖上条问题', description: '补充数据或给下一步行动', icon: <RobotOutlined /> })
    }

    const merged = [...contextItems, ...baseItems]
    const dedup = merged.filter((item, idx, arr) => arr.findIndex(it => it.key === item.key) === idx)
    return dedup.slice(0, 6).map(item => ({ ...item, value: item.key }))
  }, [lastUserMessage])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 通知父组件消息更新
  useEffect(() => {
    onMessageUpdate?.(messages)
  }, [messages, onMessageUpdate])

  useEffect(() => {
    messagesRef.current = messages
    console.log('messages状态更新:', {
      count: messages.length,
      lastMessage: messages[messages.length - 1],
      allMessages: messages,
    })
  }, [messages])

  /**
   * 处理发送消息（使用流式响应）
   */
  const handleSend = useCallback(async (value: string) => {
    const content = value.trim()
    if (!content || loading) return

    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }

    // 使用函数式更新确保状态正确更新
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      console.log('添加用户消息:', {
        previousCount: prev.length,
        newCount: newMessages.length,
        message: userMessage,
      })
      return newMessages
    })
    setLoading(true)

    // 创建助手消息 ID（用于流式更新）
    const assistantMessageId = uuidv4()
    let assistantMessageContent = ''
    let messageModel: string | undefined = undefined

    try {
      // 记录请求信息（用于调试）
      console.log('发送流式聊天请求:', {
        model,
        temperature,
        includeSystemData,
        messagesCount: messagesRef.current.length + 1,
        shopId: shopId ? parseInt(shopId) : undefined,
      })
      
      // 创建初始助手消息
      const initialAssistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }
      
      setMessages(prev => [...prev, initialAssistantMessage])
      
      // 调用流式 API
      const stream = frogGptApi.chatStream({
        messages: [
          ...messagesRef.current.map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          {
            role: 'user',
            content,
          },
        ],
        model,
        temperature,
        include_system_data: includeSystemData,
        data_summary_days: dataSummaryDays ?? undefined,
        shop_id: shopId ? parseInt(shopId) : undefined,
      })

      // 处理流式响应
      for await (const chunk of stream) {
        if (chunk.type === 'error') {
          throw new Error(chunk.error || '未知错误')
        } else if (chunk.type === 'content') {
          // 累积内容
          assistantMessageContent += chunk.content
          messageModel = chunk.model || messageModel
          
          // 实时更新消息内容
          setMessages(prev => {
            return prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  content: assistantMessageContent,
                }
              }
              return msg
            })
          })
        } else if (chunk.type === 'done') {
          // 流式响应完成
          console.log('流式响应完成:', {
            contentLength: assistantMessageContent.length,
            finishReason: chunk.finish_reason,
          })
          
          // 提取决策数据
          const decisionData = extractDecisionFromMarkdown(assistantMessageContent)
          if (decisionData) {
            onDecisionParsed?.(decisionData)
          }
        } else if (chunk.type === 'usage') {
          // 使用统计（可选）
          console.log('Token 使用统计:', chunk.usage)
        }
      }
    } catch (error: any) {
      console.error('发送消息失败:', error)
      console.error('错误详情:', {
        message: error.message,
        stack: error.stack,
      })
      
      // 提取错误信息
      let errorMessage = '未知错误'
      if (error.message) {
        errorMessage = error.message
      }
      
      // 更新助手消息为错误消息
      setMessages(prev => {
        return prev.map(msg => {
          if (msg.id === assistantMessageId) {
            return {
              ...msg,
              content: `❌ 抱歉，发生了错误：${errorMessage}`,
            }
          }
          return msg
        })
      })
    } finally {
      setLoading(false)
    }
  }, [model, temperature, includeSystemData, dataSummaryDays, shopId, onDecisionParsed, loading])

  // 处理外部消息（快捷问题）
  useEffect(() => {
    if (externalMessage && externalMessage.trim()) {
      const sendMessage = async () => {
        await handleSend(externalMessage.trim())
        onExternalMessageSent?.()
      }

      sendMessage()
    }
  }, [externalMessage, handleSend, onExternalMessageSent])

  const renderSenderSuffix: NonNullable<SenderProps['suffix']> = (ori, { components }) => {
    const { ClearButton } = components
    return (
      <Space size="small">
        <ClearButton />
        {ori}
      </Space>
    )
  }

  return (
    <Card
      className="frog-gpt-chat-card frog-gpt-section-card"
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      styles={{
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
        className="frog-gpt-chat-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          borderRadius: 12,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', minHeight: '100%' }}>
          {loading && (
            <ThoughtChain
              className="frog-gpt-thought"
              items={[
                { key: 'sync', title: '收集数据', description: '同步运营指标与店铺画像', status: 'success' },
                { key: 'analyze', title: '分析趋势', description: '识别 GMV/利润/退款率波动', status: 'loading' },
                { key: 'compose', title: '生成答案', description: '编排决策卡片与建议', status: 'loading' },
              ]}
            />
          )}
          {(() => {
            console.log('准备渲染消息列表，消息数量:', messages.length, '消息:', messages)
            return null
          })()}
          {messages.length > 0 ? messages.map((message) => {
            console.log('渲染消息:', {
              id: message.id,
              role: message.role,
              contentLength: message.content.length,
              contentPreview: message.content.substring(0, 50),
              hasContent: !!message.content,
              fullContent: message.content,
            })
            
            // 如果是助手消息，添加额外的调试信息
            if (message.role === 'assistant') {
              console.log('助手消息详情:', {
                id: message.id,
                content: message.content,
                contentLength: message.content.length,
                willRender: true,
              })
            }
            
            return (
            <div 
              key={message.id} 
              style={{ 
                display: 'flex', 
                gap: '12px', 
                width: '100%',
                minHeight: '40px',
                marginBottom: '16px',
              }}
            >
              {message.role === 'user' ? (
                <div 
                  className="frog-gpt-user-message"
                  data-message-id={message.id}
                  data-role="user"
                  style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'flex-end', alignItems: 'flex-start' }}
                >
                  <div
                    className="frog-gpt-user-message-content"
                    data-content-length={message.content.length}
                    style={{
                      maxWidth: '70%',
                      flex: '0 1 auto',
                      background: 'rgba(96, 165, 250, 0.2)',
                      borderRadius: '12px',
                      padding: '12px 16px',
                      color: '#e2e8f0',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      lineHeight: '1.6',
                      fontSize: '14px',
                      minHeight: '20px',
                    }}
                  >
                    {message.content}
                  </div>
                  <Avatar
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#60a5fa', flexShrink: 0 }}
                  />
                </div>
              ) : (
                <div 
                  className="frog-gpt-assistant-message"
                  data-message-id={message.id}
                  data-role="assistant"
                  style={{ display: 'flex', gap: '12px', width: '100%', alignItems: 'flex-start' }}
                >
                  <Avatar
                    icon={<RobotOutlined />}
                    style={{ backgroundColor: '#00d1b2', flexShrink: 0 }}
                  />
                  <div
                    className="frog-gpt-message-content"
                    data-content-length={message.content.length}
                    style={{
                      maxWidth: '70%',
                      flex: '0 1 auto',
                      background: 'rgba(255, 255, 255, 0.12)',
                      borderRadius: '12px',
                      padding: '12px 16px',
                      color: '#e2e8f0',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      lineHeight: '1.6',
                      fontSize: '14px',
                      minHeight: '20px',
                    }}
                  >
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
                        p: ({ children }: any) => <p style={{ margin: '4px 0', color: '#e2e8f0' }}>{children}</p>,
                        h1: ({ children }: any) => <h1 style={{ color: '#e2e8f0', fontSize: '18px', margin: '8px 0' }}>{children}</h1>,
                        h2: ({ children }: any) => <h2 style={{ color: '#e2e8f0', fontSize: '16px', margin: '6px 0' }}>{children}</h2>,
                        h3: ({ children }: any) => <h3 style={{ color: '#e2e8f0', fontSize: '14px', margin: '4px 0' }}>{children}</h3>,
                        ul: ({ children }: any) => <ul style={{ margin: '4px 0', paddingLeft: '20px', color: '#e2e8f0' }}>{children}</ul>,
                        li: ({ children }: any) => <li style={{ margin: '2px 0', color: '#e2e8f0' }}>{children}</li>,
                        div: ({ children, ...props }: any) => <div style={{ color: '#e2e8f0' }} {...props}>{children}</div>,
                        span: ({ children, ...props }: any) => <span style={{ color: '#e2e8f0' }} {...props}>{children}</span>,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
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
                  </div>
                </div>
              )}
            </div>
            )
          }) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>
              暂无消息
            </div>
          )}
          {loading && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Avatar
                icon={<RobotOutlined />}
                style={{ backgroundColor: '#00d1b2', flexShrink: 0 }}
              />
              <Bubble
                placement="start"
                content={
                  <Space>
                    <Spin size="small" />
                    <Text style={{ color: '#94a3b8' }}>正在思考...</Text>
                  </Space>
                }
              />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 底部提示词 + 输入区域 */}
      <div style={{ padding: '12px 16px 12px', borderTop: '1px solid #1E293B', background: '#0b1120' }}>
        <div className="frog-gpt-suggestion-row">
          {promptItems.map(item => (
            <div
              key={item.key}
              className="frog-gpt-suggestion-chip"
              onClick={() => {
                const promptMap: Record<string, string> = {
                  summary: '请生成今日的运营总结报告，包括GMV、订单量、利润率等关键指标，并给出一句话洞察。',
                  gmv: '分析最近 7 天 GMV 变化的原因，按渠道/类目拆解主要驱动，并提供优化建议。',
                  refund: '请列出退货率最高的 5 个 SKU，分析原因并给出改进措施，包括标题、素材和客服话术。',
                  title: '基于当前热销商品，帮我生成 3 个高转化率的商品标题，并简述理由。',
                  profit: '结合最近 14 天数据，告诉我可以提升利润率的三个动作、执行步骤和预期收益。',
                  'ctx-gmv': '围绕我刚才的问题，细分 GMV 变化的原因，按渠道/类目/价格带给出三条改进建议。',
                  'ctx-refund': '根据当前问题，定位退款率/退货率暴涨的原因，列出 Top SKU、品类和地区，并给可执行的缓解方案。',
                  'ctx-title': '基于上条问题，输出 3 条新标题，每条附一句卖点解释和关键词。',
                  'ctx-follow': '请继续深挖我上条问题，补充需要的数据点或给出下一步行动方案。',
                }
                const prompt = promptMap[item.key as string]
                if (prompt && !loading) {
                  handleSend(prompt)
                  setInputValue('')
                }
              }}
              role="button"
              tabIndex={0}
            >
              <div className="frog-gpt-suggestion-chip-title">{item.label}</div>
              {item.description && (
                <div className="frog-gpt-suggestion-chip-desc">{item.description}</div>
              )}
            </div>
          ))}
        </div>

        <div style={{ marginTop: 10 }}>
          <Sender
            value={inputValue}
            onChange={(value) => setInputValue(value || '')}
            onSubmit={(value) => {
              if (value?.trim() && !loading) {
                handleSend(value)
                setInputValue('')
              }
            }}
            submitType="enter"
            loading={loading}
            disabled={loading}
            placeholder="向 FrogGPT 提问，例如：分析最近7天 GMV 变化原因"
            suffix={renderSenderSuffix}
            footer={() => null}
            styles={{
              content: { background: '#0f172a', borderRadius: 12, border: '1px solid #1E293B' },
              suffix: { paddingRight: 4 },
            }}
          />
        </div>
      </div>
    </Card>
  )
}

export default AiChatPanelV2
