/**
 * AI 聊天面板组件 V2.0
 * 使用 Ant Design X 组件：Bubble, Sender, Attachments, FileCard
 */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Card, Space, Typography, Avatar, Spin, message } from 'antd'
import { RobotOutlined, UserOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { Sender, ThoughtChain, FileCard, type SenderProps } from '@ant-design/x'
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
    // 支持多种格式：```json、```JSON、``` json等
    const jsonMatch = content.match(/```(?:json|JSON)\s*([\s\S]*?)\s*```/i)
    if (jsonMatch && jsonMatch[1]) {
      const jsonStr = jsonMatch[1].trim()
      const decisionData = JSON.parse(jsonStr) as DecisionData
      
      // 验证必需字段
      if (!decisionData.decisionSummary || !decisionData.riskLevel || !decisionData.actions || !Array.isArray(decisionData.actions) || decisionData.actions.length === 0) {
        console.warn('决策卡片数据缺少必需字段:', decisionData)
        return null
      }
      
      // 验证 actions 格式
      const validActions = decisionData.actions.filter((action: any) => 
        action.type && action.target
      )
      
      if (validActions.length === 0) {
        console.warn('决策卡片 actions 格式无效')
        return null
      }
      
      // 返回验证后的数据
      return {
        ...decisionData,
        actions: validActions,
      }
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
  const [attachments, setAttachments] = useState<File[]>([])
  const [attachmentFiles, setAttachmentFiles] = useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const messagesRef = useRef<ChatMessage[]>(messages)
  const decisionDraftRef = useRef<DecisionData | null>(null)
  const lastUserMessage = useMemo(
    () => [...messages].reverse().find(msg => msg.role === 'user'),
    [messages],
  )

  const promptItems = useMemo(() => {
    const baseItems = [
      { key: 'stock-plan', label: '制定备货计划', description: '根据回款和销量制定未来一周/月备货计划', icon: <RobotOutlined /> },
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
    if (text.includes('备货') || text.includes('库存') || text.includes('采购')) {
      contextItems.push({ key: 'stock-plan-month', label: '制定一个月备货计划', description: '基于回款和销量数据', icon: <RobotOutlined /> })
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
   * 处理发送消息（使用流式响应，支持文件上传）
   */
  const handleSend = useCallback(async (value: string, files?: File[]) => {
    const content = value.trim()
    const filesToSend = files || attachments
    
    // 如果没有内容且没有文件，则不发送
    if ((!content && filesToSend.length === 0) || loading) return
    decisionDraftRef.current = null
    onDecisionParsed?.(null)

    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: content || (filesToSend.length > 0 ? `上传了 ${filesToSend.length} 个文件` : ''),
      timestamp: Date.now(),
    }

    // 使用函数式更新确保状态正确更新
    setMessages(prev => {
      const newMessages = [...prev, userMessage]
      console.log('添加用户消息:', {
        previousCount: prev.length,
        newCount: newMessages.length,
        message: userMessage,
        filesCount: filesToSend.length,
      })
      return newMessages
    })
    setLoading(true)

    // 创建助手消息 ID（用于流式更新）
    const assistantMessageId = uuidv4()
    let assistantMessageContent = ''
    let messageModel: string | undefined = undefined

    try {
      // 如果有文件，使用带文件的 API
      if (filesToSend.length > 0) {
        const formData = new FormData()
        formData.append('messages', JSON.stringify([
          ...messagesRef.current.map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          {
            role: 'user',
            content: content || '',
          },
        ]))
        formData.append('model', model || 'auto')
        formData.append('temperature', String(temperature))
        formData.append('include_system_data', String(includeSystemData))
        if (dataSummaryDays) {
          formData.append('data_summary_days', String(dataSummaryDays))
        }
        if (shopId) {
          formData.append('shop_id', String(shopId))
        }
        
        // 添加文件
        filesToSend.forEach((file) => {
          formData.append('files', file)
        })

        // 调用带文件的 API（非流式）
        try {
          const response = await frogGptApi.chatWithFiles(formData)
          
          // 处理响应（根据后端返回格式调整）
          const responseData = response.data || response
          if (responseData && (responseData.content || responseData.message)) {
            assistantMessageContent = responseData.content || responseData.message || ''
            messageModel = responseData.model
            
            setMessages(prev => {
              return prev.map(msg => {
                if (msg.id === assistantMessageId) {
                  return {
                    ...msg,
                    content: assistantMessageContent,
                    isLoading: false,
                  }
                }
                return msg
              })
            })
            
            // 提取决策数据
            const decisionData = extractDecisionFromMarkdown(assistantMessageContent)
            if (decisionData) {
              decisionDraftRef.current = decisionData
              onDecisionParsed?.(decisionData)
            }
          } else {
            throw new Error('响应中没有内容')
          }
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || '文件上传失败'
          setMessages(prev => {
            return prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  content: `❌ 抱歉，文件处理失败：${errorMessage}`,
                  isLoading: false,
                }
              }
              return msg
            })
          })
        } finally {
          // 清空附件
          setAttachments([])
          setAttachmentFiles([])
        }
        return
      }

      // 记录请求信息（用于调试）
      console.log('发送流式聊天请求:', {
        model,
        temperature,
        includeSystemData,
        messagesCount: messagesRef.current.length + 1,
        shopId: shopId ? parseInt(shopId) : undefined,
      })
      
      // 创建初始助手消息（带加载状态）
      const initialAssistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isLoading: true, // 标记为加载中
      } as ChatMessage
      
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
                  isLoading: false, // 有内容后取消加载状态
                }
              }
              return msg
            })
          })
          const parsedDraft = extractDecisionFromMarkdown(assistantMessageContent)
          if (parsedDraft && JSON.stringify(parsedDraft) !== JSON.stringify(decisionDraftRef.current)) {
            decisionDraftRef.current = parsedDraft
            onDecisionParsed?.(parsedDraft)
          }
        } else if (chunk.type === 'done') {
          // 流式响应完成
          console.log('流式响应完成:', {
            contentLength: assistantMessageContent.length,
            finishReason: chunk.finish_reason,
          })
          
          // 确保取消加载状态
          setMessages(prev => {
            return prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  isLoading: false,
                }
              }
              return msg
            })
          })
          
          // 提取决策数据
          const decisionData = extractDecisionFromMarkdown(assistantMessageContent)
          if (decisionData) {
            decisionDraftRef.current = decisionData
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
              isLoading: false, // 取消加载状态
            }
          }
          return msg
        })
      })
    } finally {
      setLoading(false)
      // 清空附件
      if (attachments.length > 0) {
        setAttachments([])
        setAttachmentFiles([])
      }
    }
  }, [model, temperature, includeSystemData, dataSummaryDays, shopId, onDecisionParsed, loading, attachments])

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

  // 处理文件粘贴和拖拽
  const handlePasteFile = useCallback((files: FileList) => {
    const fileArray = Array.from(files)
    const validFiles = fileArray.filter(file => {
      // 限制文件大小（10MB）
      if (file.size > 10 * 1024 * 1024) {
        message.warning(`文件 ${file.name} 超过 10MB 限制`)
        return false
      }
      return true
    })
    
    if (validFiles.length > 0) {
      setAttachments(prev => [...prev, ...validFiles])
      
      // 创建 UploadFile 对象用于显示
      const uploadFiles: UploadFile[] = validFiles.map((file, index) => ({
        uid: `${file.name}-${Date.now()}-${index}`,
        name: file.name,
        status: 'done' as const,
        url: URL.createObjectURL(file),
        originFileObj: file,
      } as UploadFile))
      
      setAttachmentFiles(prev => [...prev, ...uploadFiles])
      message.success(`已添加 ${validFiles.length} 个文件`)
    }
  }, [])

  // 处理文件删除
  const handleRemoveFile = useCallback((uid: string) => {
    const uploadFile = attachmentFiles.find(f => f.uid === uid)
    if (uploadFile?.originFileObj) {
      setAttachments(prev => prev.filter(f => f !== uploadFile.originFileObj))
    }
    setAttachmentFiles(prev => prev.filter(f => f.uid !== uid))
  }, [attachmentFiles])

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
      <div className="frog-gpt-chat-meta" style={{ flexShrink: 0 }}>
        <div className="frog-gpt-chat-led" />
      </div>
      {/* 消息列表区域 */}
      <div
        ref={scrollContainerRef}
        className="frog-gpt-chat-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '6px',
          borderRadius: 12,
          minHeight: 0,
          maxHeight: '100%',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%', minHeight: '100%' }}>
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
                gap: '6px', 
                width: '100%',
                minHeight: '32px',
                marginBottom: '4px',
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
                      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
                      borderRadius: '12px',
                      padding: '12px 16px',
                      color: '#e2e8f0',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      lineHeight: '1.6',
                      fontSize: '14px',
                      minHeight: '20px',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      boxShadow: '0 4px 12px rgba(59, 130, 246, 0.2), 0 0 10px rgba(59, 130, 246, 0.1)',
                      textShadow: '0 0 8px rgba(59, 130, 246, 0.3)',
                    }}
                  >
                    {(!message.content || message.content.trim() === '') && message.isLoading ? (
                      <Space>
                        <Spin size="small" />
                        <Text style={{ color: '#94a3b8' }}>正在思考...</Text>
                      </Space>
                    ) : (
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
                    )}
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
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 底部提示词 + 输入区域 */}
      <div style={{ 
        padding: '4px 8px 4px', 
        borderTop: '1px solid #1E293B', 
        background: '#0b1120', 
        flexShrink: 0,
        position: 'relative',
        zIndex: 2,
      }}>
        <div className="frog-gpt-suggestion-row">
          {promptItems.map(item => (
            <div
              key={item.key}
              className="frog-gpt-suggestion-chip"
              onClick={() => {
                const promptMap: Record<string, string> = {
                  'stock-plan': '根据过去一周的回款数据和销量，制定未来一周的按SKU货号的备货计划。请分析每个SKU的销量趋势和回款情况，预测未来需求，并给出详细的备货建议。',
                  'stock-plan-month': '根据过去一周的回款数据和销量，制定未来一个月的按SKU货号的备货计划。请分析每个SKU的销量趋势和回款情况，预测未来需求，并给出详细的备货建议。',
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

        {/* 显示已上传的文件 */}
        {attachmentFiles.length > 0 && (
          <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {attachmentFiles.map((file) => (
              <div key={file.uid} style={{ position: 'relative' }}>
                <FileCard
                  name={file.name}
                  style={{
                    background: 'rgba(10, 10, 26, 0.8)',
                    border: '1px solid rgba(139, 92, 246, 0.4)',
                    borderRadius: 8,
                    padding: '8px 12px',
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 8px rgba(139, 92, 246, 0.2), 0 0 10px rgba(139, 92, 246, 0.1)',
                  }}
                />
                <button
                  onClick={() => handleRemoveFile(file.uid)}
                  style={{
                    position: 'absolute',
                    top: 4,
                    right: 4,
                    background: 'rgba(239, 68, 68, 0.9)',
                    border: 'none',
                    borderRadius: '50%',
                    width: 20,
                    height: 20,
                    cursor: 'pointer',
                    color: '#fff',
                    fontSize: 14,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    lineHeight: 1,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 1)'
                    e.currentTarget.style.transform = 'scale(1.1)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.9)'
                    e.currentTarget.style.transform = 'scale(1)'
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <div 
          className={`frog-gpt-drag-area ${isDragging ? 'drag-over' : ''}`}
          style={{ marginTop: attachments.length > 0 ? 0 : 10 }}
          onDrop={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setIsDragging(false)
            const files = e.dataTransfer.files
            if (files.length > 0) {
              handlePasteFile(files)
            }
          }}
          onDragOver={(e) => {
            e.preventDefault()
            e.stopPropagation()
            if (!isDragging) {
              setIsDragging(true)
            }
          }}
          onDragLeave={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setIsDragging(false)
          }}
        >
          <Sender
            value={inputValue}
            onChange={(value) => setInputValue(value || '')}
            onSubmit={(value) => {
              if ((value?.trim() || attachments.length > 0) && !loading) {
                handleSend(value || '', attachments)
                setInputValue('')
              }
            }}
            onPasteFile={handlePasteFile}
            submitType="enter"
            loading={loading}
            disabled={loading}
            placeholder="向 FrogGPT 提问，例如：分析最近7天 GMV 变化原因（支持拖拽/粘贴文件）"
            suffix={renderSenderSuffix}
            header={
              attachmentFiles.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '8px 0' }}>
                  {attachmentFiles.map((file) => (
                    <div key={file.uid} style={{ position: 'relative' }}>
                      <FileCard
                        name={file.name}
                      style={{
                        background: 'rgba(10, 10, 26, 0.8)',
                        border: '1px solid rgba(139, 92, 246, 0.4)',
                        borderRadius: 8,
                        padding: '8px 12px',
                        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.2), 0 0 10px rgba(139, 92, 246, 0.1)',
                      }}
                      />
                      <button
                        onClick={() => handleRemoveFile(file.uid)}
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          background: 'rgba(239, 68, 68, 0.9)',
                          border: 'none',
                          borderRadius: '50%',
                          width: 20,
                          height: 20,
                          cursor: 'pointer',
                          color: '#fff',
                          fontSize: 14,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          lineHeight: 1,
                          transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(239, 68, 68, 1)'
                          e.currentTarget.style.transform = 'scale(1.1)'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(239, 68, 68, 0.9)'
                          e.currentTarget.style.transform = 'scale(1)'
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              ) : false
            }
            footer={() => null}
            styles={{
              root: { 
                border: '1px solid rgba(139, 92, 246, 0.4)', 
                borderRadius: 16, 
                boxShadow: 
                  '0 12px 36px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(139, 92, 246, 0.2), 0 0 20px rgba(139, 92, 246, 0.3)',
                background: 'linear-gradient(135deg, rgba(10, 10, 26, 0.95), rgba(26, 10, 46, 0.95))',
                backdropFilter: 'blur(20px)',
                transition: 'all 0.3s',
              },
              content: { 
                background: 'rgba(10, 10, 26, 0.8)', 
                borderRadius: 16, 
                border: '1px solid rgba(139, 92, 246, 0.3)',
                color: '#e2e8f0',
              },
              input: {
                color: '#e2e8f0',
                textShadow: '0 0 10px rgba(139, 92, 246, 0.3)',
              },
              suffix: { paddingRight: 8 },
            }}
          />
        </div>
      </div>
    </Card>
  )
}

export default AiChatPanelV2
