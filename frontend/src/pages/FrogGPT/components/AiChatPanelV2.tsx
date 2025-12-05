/**
 * AI 聊天面板组件 V2.0
 * 使用 Ant Design X 组件：Bubble, Sender, Attachments, FileCard
 */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Card, Space, Typography, Avatar, Spin, App, Button } from 'antd'
import { RobotOutlined, UserOutlined, ThunderboltOutlined, SettingOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { Sender, ThoughtChain, Think, Attachments, Bubble, type SenderProps } from '@ant-design/x'
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
  const { message: messageApi } = App.useApp()
  const abortControllerRef = useRef<AbortController | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  
  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      // 使用更严格的移动端判断，确保在移动设备上始终使用上下布局
      const isMobileDevice = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
      const isMobileWidth = window.innerWidth < 1024 // 提高断点到1024px
      setIsMobile(isMobileDevice || isMobileWidth)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '👋 欢迎使用 FrogGPT 2.0！我是您的 AI 运营助手。\n\n我可以帮您：\n- 📊 分析销售数据和趋势\n- 🚀 提供运营决策建议\n- 💡 回答关于店铺和商品的问题\n\n请随时向我提问！',
      timestamp: Date.now(),
    },
  ])
  const [loading, setLoading] = useState(false)
  // 使用 ref 跟踪 loading 状态，避免在 handleSend 依赖数组中包含 loading 造成循环依赖
  const loadingRef = useRef(false)
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
  // 管理每个消息的思考过程展开状态
  const [thinkingExpanded, setThinkingExpanded] = useState<Record<string, boolean>>({})

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

  // 检测用户是否手动滚动（距离底部超过阈值）
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const lastScrollTopRef = useRef(0)
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // 检查是否在底部附近
  const checkIfNearBottom = useCallback(() => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight
      return distanceFromBottom < 150 // 距离底部150px内认为在底部
    }
    return true
  }, [])
  
  // 处理滚动事件
  const handleScroll = useCallback(() => {
    if (scrollContainerRef.current) {
      const { scrollTop } = scrollContainerRef.current
      const isScrollingUp = scrollTop < lastScrollTopRef.current
      lastScrollTopRef.current = scrollTop
      
      const isNearBottom = checkIfNearBottom()
      
      if (isScrollingUp || !isNearBottom) {
        // 用户向上滚动或不在底部，禁用自动滚动
        setShouldAutoScroll(false)
        // 清除之前的定时器
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current)
        }
        // 5秒后如果用户回到底部，重新启用自动滚动
        scrollTimeoutRef.current = setTimeout(() => {
          if (checkIfNearBottom()) {
            setShouldAutoScroll(true)
          }
        }, 5000)
      } else if (isNearBottom) {
        // 用户在底部，启用自动滚动
        setShouldAutoScroll(true)
      }
    }
  }, [checkIfNearBottom])
  
  // 监听滚动事件
  useEffect(() => {
    const container = scrollContainerRef.current
    if (container) {
      lastScrollTopRef.current = container.scrollTop
      container.addEventListener('scroll', handleScroll, { passive: true })
      return () => {
        container.removeEventListener('scroll', handleScroll)
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current)
        }
      }
    }
  }, [handleScroll])
  
  // 自动滚动到底部（仅在应该自动滚动时）
  useEffect(() => {
    if (shouldAutoScroll && messagesEndRef.current) {
      // 使用 requestAnimationFrame 确保 DOM 更新后再滚动
      requestAnimationFrame(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      })
    }
  }, [messages, shouldAutoScroll])

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
    // 使用 loadingRef 而不是 loading，避免循环依赖
    if ((!content && filesToSend.length === 0) || loadingRef.current) return
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
    loadingRef.current = true

    // 创建助手消息 ID（用于流式更新）
    const assistantMessageId = uuidv4()
    let assistantMessageContent = ''
    let messageModel: string | undefined = undefined

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

        // 创建初始助手消息（带加载状态和思考过程）
        const initialAssistantMessage: ChatMessage = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isLoading: true,
          thinking: '正在处理文件并分析内容...',
        } as ChatMessage
        
        setMessages(prev => [...prev, initialAssistantMessage])

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
                    thinking: undefined, // 完成后移除思考过程
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
      
      // 创建初始助手消息（带加载状态和思考过程）
      let assistantThinkingContent = '' // 累积思考过程内容
      const initialAssistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isLoading: true, // 标记为加载中
        thinking: '正在分析您的问题，准备生成回答...', // 初始思考过程
      } as ChatMessage
      
      setMessages(prev => [...prev, initialAssistantMessage])
      
      // 创建 AbortController 用于取消请求
      abortControllerRef.current = new AbortController()
      const signal = abortControllerRef.current.signal
      
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
      }, signal)

      // 处理流式响应
      try {
        for await (const chunk of stream) {
          if (chunk.type === 'error') {
            throw new Error(chunk.error || '未知错误')
          } else if (chunk.type === 'reasoning') {
            // 处理思考过程（DeepSeek 的 reasoning_content）
            assistantThinkingContent += chunk.content || ''
            
            // 实时更新思考过程
            setMessages(prev => {
              return prev.map(msg => {
                if (msg.id === assistantMessageId) {
                  return {
                    ...msg,
                    thinking: assistantThinkingContent || '正在思考...',
                    isLoading: true, // 思考过程中保持加载状态
                  }
                }
                return msg
              })
            })
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
                    // 保留思考过程（如果有）
                    thinking: assistantThinkingContent || undefined,
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
              thinkingLength: assistantThinkingContent.length,
              finishReason: chunk.finish_reason,
            })
            
            // 确保取消加载状态，保留思考过程（如果有）
            setMessages(prev => {
              return prev.map(msg => {
                if (msg.id === assistantMessageId) {
                  return {
                    ...msg,
                    isLoading: false,
                    // 保留思考过程（DeepSeek 的 reasoning_content）
                    thinking: assistantThinkingContent || undefined,
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
        // 如果是取消请求，不显示错误消息
        if (error.name === 'AbortError' || signal?.aborted) {
          console.log('请求已取消')
          setMessages(prev => {
            return prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  content: msg.content || '请求已取消',
                  isLoading: false,
                }
              }
              return msg
            })
          })
          return
        }
        
        console.error('发送消息失败:', error)
        console.error('错误详情:', {
          message: error.message,
          stack: error.stack,
        })
        
        // 提取错误信息
        let errorMessage = '未知错误'
        if (error.message) {
          errorMessage = error.message
          // 如果是TLS/SSL连接错误，提供更友好的错误信息
          if (errorMessage.includes('TLS/SSL') || errorMessage.includes('connection has been closed')) {
            errorMessage = '连接中断，请重试。如果问题持续，可能是网络问题或服务器响应超时。'
          }
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
        // 清理 AbortController
        abortControllerRef.current = null
        setLoading(false)
        loadingRef.current = false
        // 清空附件并释放对象 URL
        if (attachmentFiles.length > 0) {
          attachmentFiles.forEach(file => {
            if (file.url && file.url.startsWith('blob:')) {
              URL.revokeObjectURL(file.url)
            }
          })
          setAttachments([])
          setAttachmentFiles([])
        }
      }
    }, [model, temperature, includeSystemData, dataSummaryDays, shopId, onDecisionParsed, attachments, attachmentFiles])

  // 处理外部消息（快捷问题）
  useEffect(() => {
    if (externalMessage && externalMessage.trim()) {
      const sendMessage = async () => {
        await handleSend(externalMessage.trim(), [])
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
        messageApi.warning(`文件 ${file.name} 超过 10MB 限制`)
        return false
      }
      // 限制文件类型（可选：根据需求添加）
      const allowedTypes = [
        'image/', 'text/', 'application/pdf', 
        'application/vnd.openxmlformats-officedocument',
        'application/vnd.ms-excel',
        'application/vnd.ms-office'
      ]
      const isValidType = allowedTypes.some(type => file.type.startsWith(type)) || !file.type
      if (!isValidType) {
        messageApi.warning(`文件 ${file.name} 类型不支持`)
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
        size: file.size,
        type: file.type,
      } as UploadFile))
      
      setAttachmentFiles(prev => [...prev, ...uploadFiles])
      messageApi.success(`已添加 ${validFiles.length} 个文件`)
    }
  }, [messageApi])

  // 处理停止流式输出
  const handleStop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setLoading(false)
      loadingRef.current = false
      messageApi.info('已停止生成')
    }
  }, [messageApi])

  // 处理文件删除
  const handleRemoveFile = useCallback((id: string) => {
    console.log('移除文件:', id)
    setAttachmentFiles(prev => {
      const uploadFile = prev.find(f => f.uid === id)
      console.log('找到文件:', uploadFile)
      
      if (uploadFile) {
        // 从 attachments 中移除对应的 File 对象
        if (uploadFile.originFileObj) {
          setAttachments(attachments => {
            const filtered = attachments.filter(f => f !== uploadFile.originFileObj)
            console.log('attachments 更新:', filtered.length, '个文件')
            return filtered
          })
        }
        
        // 释放对象 URL
        if (uploadFile.url && uploadFile.url.startsWith('blob:')) {
          URL.revokeObjectURL(uploadFile.url)
        }
      }
      
      // 从 attachmentFiles 中移除
      const filtered = prev.filter(f => f.uid !== id)
      console.log('attachmentFiles 更新:', filtered.length, '个文件')
      
      if (filtered.length !== prev.length) {
        messageApi.success('文件已移除')
      }
      
      return filtered
    })
  }, [messageApi])

  const renderSenderSuffix: NonNullable<SenderProps['suffix']> = (ori, { components }) => {
    const { ClearButton } = components
    return (
      <Space size="small" style={{ marginRight: 4 }}>
        {loading ? (
          <button
            onClick={handleStop}
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '4px 12px',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.5)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)'
            }}
          >
            停止
          </button>
        ) : (
          <>
            {inputValue && (
              <ClearButton 
                onClick={() => {
                  setInputValue('')
                }}
              />
            )}
            {ori}
          </>
        )}
      </Space>
    )
  }
  
  const renderSenderPrefix = useCallback(() => {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const bgColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)'
    const hoverBgColor = isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.1)'
    const textColor = isDark ? '#d1d5db' : '#666'
    
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        width: 32,
        height: 32,
        marginLeft: 8,
        marginRight: 4,
        borderRadius: 8,
        background: bgColor,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = hoverBgColor
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = bgColor
      }}
      onClick={() => {
        // 触发文件选择
        const input = document.createElement('input')
        input.type = 'file'
        input.multiple = true
        input.onchange = (e) => {
          const files = (e.target as HTMLInputElement).files
          if (files && files.length > 0) {
            handlePasteFile(files)
          }
        }
        input.click()
      }}
      >
        <span style={{ fontSize: 20, color: textColor, lineHeight: 1 }}>+</span>
      </div>
    )
  }, [handlePasteFile])

  return (
    <Card
      className="frog-gpt-chat-card frog-gpt-section-card"
      style={{
        height: '100%',
        maxHeight: '100%',
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        maxWidth: '100%',
        overflow: 'hidden',
        visibility: 'visible',
        opacity: 1,
        border: isMobile ? 'none' : undefined, // 移动端无边框
        borderRadius: isMobile ? 0 : undefined, // 移动端无圆角
        boxShadow: isMobile ? 'none' : undefined, // 移动端无阴影
      }}
      styles={{
        root: {
          height: '100%',
          maxHeight: '100%',
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          visibility: 'visible',
          opacity: 1,
          border: isMobile ? 'none' : undefined,
          borderRadius: isMobile ? 0 : undefined,
          boxShadow: isMobile ? 'none' : undefined,
        },
        body: {
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden',
          minHeight: 0,
          maxHeight: '100%',
        },
      }}
    >
      {/* 移动端顶部栏 */}
      {isMobile && (
        <div style={{
          padding: '8px 16px',
          background: 'linear-gradient(135deg, rgba(10, 10, 26, 0.98) 0%, rgba(26, 10, 46, 0.98) 100%)',
          borderBottom: '1px solid rgba(139, 92, 246, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          flexShrink: 0,
          minHeight: '48px',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}>
          <Text style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 600 }}>
            FrogGPT
          </Text>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => {
              // 触发设置弹窗 - 通过自定义事件通知父组件
              window.dispatchEvent(new CustomEvent('openFrogGPTConfig'))
            }}
            size="small"
            style={{ color: '#e2e8f0', padding: '4px 8px' }}
          />
        </div>
      )}
      {!isMobile && (
        <div className="frog-gpt-chat-meta" style={{ flexShrink: 0 }}>
          <div className="frog-gpt-chat-led" />
        </div>
      )}
      <div
        ref={scrollContainerRef}
        className="frog-gpt-chat-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: isMobile ? '12px 8px' : '6px',
          paddingBottom: isMobile ? '100px' : '6px',
          borderRadius: isMobile ? 0 : 12,
          minHeight: 0,
          height: isMobile ? '100%' : 'auto',
          maxHeight: '100%',
          position: 'relative',
          zIndex: 1,
          WebkitOverflowScrolling: 'touch',
          touchAction: 'pan-y',
          overscrollBehaviorY: 'contain',
          display: 'flex',
          flexDirection: 'column',
          visibility: 'visible',
          opacity: 1,
        }}
      >
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: isMobile ? '12px' : '6px', 
          width: '100%', 
          minHeight: isMobile ? 'auto' : '100%', // 移动端不强制最小高度
          paddingBottom: isMobile ? '20px' : '0',
        }}>
          {loading && (
            <ThoughtChain
              className="frog-gpt-thought"
              items={[
                { 
                  key: 'sync', 
                  title: '收集数据', 
                  description: '同步运营指标与店铺画像', 
                  status: 'success',
                  collapsible: false,
                },
                { 
                  key: 'analyze', 
                  title: '分析趋势', 
                  description: '识别 GMV/利润/退款率波动', 
                  status: 'loading',
                  blink: true,
                  collapsible: false,
                },
                { 
                  key: 'compose', 
                  title: '生成答案', 
                  description: '编排决策卡片与建议', 
                  status: 'loading',
                  blink: true,
                  collapsible: false,
                },
              ]}
              line="solid"
              styles={{
                root: {
                  marginBottom: '12px',
                },
                item: {
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                },
                itemIcon: {
                  color: '#60a5fa',
                },
                itemHeader: {
                  color: '#e2e8f0',
                  fontSize: 13,
                  fontWeight: 600,
                },
                itemContent: {
                  color: '#94a3b8',
                  fontSize: 12,
                },
              }}
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
                className={message.role === 'user' ? 'frog-gpt-user-message' : 'frog-gpt-assistant-message'}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  width: '100%',
                  alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '8px',
                }}
              >
                <div style={{
                  display: 'flex',
                  flexDirection: message.role === 'assistant' ? 'column' : 'row',
                  alignItems: message.role === 'assistant' ? 'flex-start' : 'flex-end',
                  width: '100%',
                  maxWidth: message.role === 'user' ? '75%' : '100%',
                  marginLeft: message.role === 'user' ? 'auto' : '0',
                }}>
                  {/* 对于助手消息，先显示头像和思考过程 */}
                  {message.role === 'assistant' && (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      width: '100%',
                    }}>
                      {/* AI 头像 */}
                      <div style={{ marginBottom: '8px' }}>
                        <Avatar 
                          icon={<ThunderboltOutlined />} 
                          style={{ 
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: '2px solid rgba(139, 92, 246, 0.5)',
                            boxShadow: '0 0 12px rgba(139, 92, 246, 0.4)',
                          }} 
                        />
                      </div>
                      {/* 思考过程显示在头像下方 */}
                      {message.thinking && (
                        <div style={{ 
                          width: '100%',
                          marginBottom: '8px',
                        }}>
                          <Think
                            key={`think-${message.id}-${thinkingExpanded[message.id] ? 'expanded' : 'collapsed'}`}
                            title="思考过程"
                            defaultExpanded={message.isLoading ? true : (thinkingExpanded[message.id] ?? false)}
                            blink={message.isLoading}
                            styles={{
                              root: {
                                background: 'rgba(59, 130, 246, 0.1)',
                                border: '1px solid rgba(59, 130, 246, 0.3)',
                                borderRadius: '6px',
                                padding: '8px 12px',
                                width: '100%',
                                cursor: message.isLoading ? 'default' : 'pointer',
                              },
                              content: {
                                color: '#94a3b8',
                                fontSize: 12,
                                lineHeight: 1.5,
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                              },
                            }}
                          >
                            {message.thinking}
                          </Think>
                        </div>
                      )}
                    </div>
                  )}
                  <Bubble
                    placement={message.role === 'user' ? 'end' : 'start'}
                    loading={message.isLoading && (!message.content || message.content.trim() === '')}
                    streaming={message.isLoading && !!message.content}
                    content={message.role === 'user' ? message.content : (message.content || '')}
                    contentRender={message.role === 'user' ? undefined : ((content) => {
                    if (!content || content.trim() === '') {
                      return (
                        <Space>
                          <Spin size="small" />
                          <Text style={{ color: '#94a3b8', fontSize: 13 }}>正在思考...</Text>
                        </Space>
                      )
                    }
                    return (
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
                                padding: '8px 12px', 
                                borderRadius: '6px',
                                marginTop: '6px',
                                marginBottom: '6px',
                                overflow: 'auto',
                              }}>
                                <pre style={{ margin: 0, color: '#e2e8f0', fontSize: 12, lineHeight: 1.5 }}>
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
                                fontSize: 12,
                              }}>
                                {children}
                              </code>
                            )
                          },
                          p: ({ children }: any) => <p style={{ margin: '2px 0', color: '#e2e8f0', fontSize: 13, lineHeight: 1.6 }}>{children}</p>,
                          h1: ({ children }: any) => <h1 style={{ color: '#e2e8f0', fontSize: 16, margin: '6px 0', fontWeight: 600 }}>{children}</h1>,
                          h2: ({ children }: any) => <h2 style={{ color: '#e2e8f0', fontSize: 15, margin: '5px 0', fontWeight: 600 }}>{children}</h2>,
                          h3: ({ children }: any) => <h3 style={{ color: '#e2e8f0', fontSize: 14, margin: '4px 0', fontWeight: 600 }}>{children}</h3>,
                          ul: ({ children }: any) => <ul style={{ margin: '2px 0', paddingLeft: '18px', color: '#e2e8f0', fontSize: 13 }}>{children}</ul>,
                          ol: ({ children }: any) => <ol style={{ margin: '2px 0', paddingLeft: '18px', color: '#e2e8f0', fontSize: 13 }}>{children}</ol>,
                          li: ({ children }: any) => <li style={{ margin: '1px 0', color: '#e2e8f0', fontSize: 13, lineHeight: 1.6 }}>{children}</li>,
                          table: ({ children }: any) => (
                            <div style={{ overflowX: 'auto', margin: '6px 0' }}>
                              <table style={{ 
                                width: '100%', 
                                borderCollapse: 'collapse',
                                fontSize: 12,
                              }}>
                                {children}
                              </table>
                            </div>
                          ),
                          thead: ({ children }: any) => <thead style={{ background: 'rgba(59, 130, 246, 0.1)' }}>{children}</thead>,
                          tbody: ({ children }: any) => <tbody>{children}</tbody>,
                          tr: ({ children }: any) => <tr style={{ borderBottom: '1px solid rgba(59, 130, 246, 0.2)' }}>{children}</tr>,
                          th: ({ children }: any) => (
                            <th style={{ 
                              padding: '6px 8px', 
                              textAlign: 'left', 
                              color: '#e2e8f0',
                              fontWeight: 600,
                              fontSize: 12,
                            }}>
                              {children}
                            </th>
                          ),
                          td: ({ children }: any) => (
                            <td style={{ 
                              padding: '6px 8px', 
                              color: '#cbd5e1',
                              fontSize: 12,
                            }}>
                              {children}
                            </td>
                          ),
                          blockquote: ({ children }: any) => (
                            <blockquote style={{ 
                              margin: '4px 0',
                              padding: '6px 12px',
                              borderLeft: '3px solid rgba(59, 130, 246, 0.5)',
                              background: 'rgba(59, 130, 246, 0.05)',
                              color: '#cbd5e1',
                              fontSize: 13,
                            }}>
                              {children}
                            </blockquote>
                          ),
                          hr: () => <hr style={{ border: 'none', borderTop: '1px solid rgba(59, 130, 246, 0.2)', margin: '8px 0' }} />,
                          div: ({ children, ...props }: any) => <div style={{ color: '#e2e8f0', fontSize: 13 }} {...props}>{children}</div>,
                          span: ({ children, ...props }: any) => <span style={{ color: '#e2e8f0', fontSize: 13 }} {...props}>{children}</span>,
                        }}
                      >
                        {content}
                      </ReactMarkdown>
                    )
                  })}
                    avatar={message.role === 'user' ? (
                      <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#60a5fa' }} />
                    ) : (
                      // 助手消息的头像已经在上面单独显示了，这里不显示
                      null
                    )}
                    styles={{
                      root: {
                        marginBottom: 0,
                        width: message.role === 'assistant' ? '100%' : 'auto',
                        marginLeft: message.role === 'user' ? 'auto' : '0',
                      },
                      body: {
                        maxWidth: message.role === 'assistant' ? '100%' : '75%',
                      },
                      content: {
                        padding: '8px 12px',
                        fontSize: 13,
                        lineHeight: 1.6,
                      },
                    }}
                    variant={message.role === 'user' ? 'filled' : 'shadow'}
                    shape="round"
                  />
                </div>
              </div>
            )
          }) : (
            <div style={{ 
              textAlign: 'center', 
              padding: isMobile ? '20px 0' : '40px 0', 
              color: '#94a3b8',
              minHeight: isMobile ? 'auto' : 'auto',
            }}>
              暂无消息
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 底部提示词 + 输入区域 */}
      <div style={{ 
        padding: isMobile ? '12px 16px' : '4px 8px 4px', 
        borderTop: isMobile ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid #1E293B', 
        background: isMobile ? 'linear-gradient(180deg, rgba(10, 10, 26, 0.98) 0%, rgba(10, 10, 26, 1) 100%)' : '#0b1120', 
        backdropFilter: isMobile ? 'blur(20px)' : 'none',
        flexShrink: 0,
        position: isMobile ? 'sticky' : 'relative',
        bottom: isMobile ? 0 : 'auto',
        zIndex: isMobile ? 100 : 2,
        boxShadow: isMobile ? '0 -4px 16px rgba(0, 0, 0, 0.3)' : undefined,
        display: 'flex',
        flexDirection: 'column',
        visibility: 'visible',
        opacity: 1,
      }}>
        {!isMobile && (
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
                  handleSend(prompt, [])
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
        )}

        <div 
          className={`frog-gpt-drag-area ${isDragging ? 'drag-over' : ''}`}
          style={{ 
            marginTop: isMobile ? (attachmentFiles.length > 0 ? 0 : 4) : (attachmentFiles.length > 0 ? 0 : 10),
            position: 'relative',
          }}
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
            // 只有当离开整个区域时才取消拖拽状态
            const rect = e.currentTarget.getBoundingClientRect()
            const x = e.clientX
            const y = e.clientY
            if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
            setIsDragging(false)
            }
          }}
        >
          {isDragging && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(59, 130, 246, 0.08)',
                border: '2px dashed rgba(59, 130, 246, 0.4)',
                borderRadius: 24,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 10,
                pointerEvents: 'none',
                backdropFilter: 'blur(4px)',
          }}
        >
              <Text style={{ color: '#3b82f6', fontSize: 15, fontWeight: 500 }}>
                释放文件以上传
              </Text>
            </div>
          )}
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
            placeholder={isMobile ? "向 FrogGPT 提问..." : "向 FrogGPT 提问，例如：分析最近7天 GMV 变化原因（支持拖拽/粘贴文件）"}
            prefix={renderSenderPrefix}
            suffix={renderSenderSuffix}
            header={
              attachmentFiles.length > 0 ? (
                <Attachments
                  items={attachmentFiles.map(file => ({
                    id: file.uid,
                    uid: file.uid,
                    name: file.name || '未知文件',
                    url: file.url,
                    size: file.size,
                    type: file.type,
                  }))}
                  onRemove={(file) => {
                    console.log('Attachments onRemove 被调用:', file)
                    const fileId = typeof file === 'string' ? file : (file as any)?.id || (file as any)?.uid
                    if (fileId) {
                      handleRemoveFile(String(fileId))
                    }
                  }}
                  onChange={(items) => {
                    // 当文件列表变化时同步更新状态
                    console.log('Attachments onChange 被调用:', items)
                    // 确保 items 是数组
                    if (!Array.isArray(items)) {
                      console.warn('Attachments onChange 接收到的 items 不是数组:', items)
                      return
                    }
                    const remainingIds = items.map(item => item.id)
                    setAttachmentFiles(prev => {
                      const filtered = prev.filter(f => remainingIds.includes(f.uid))
                      // 移除不在列表中的文件
                      const removed = prev.filter(f => !remainingIds.includes(f.uid))
                      removed.forEach(file => {
                        if (file.originFileObj) {
                          setAttachments(prevAttachments => prevAttachments.filter(f => f !== file.originFileObj))
                        }
                        if (file.url && file.url.startsWith('blob:')) {
                          URL.revokeObjectURL(file.url)
                        }
                      })
                      return filtered
                    })
                  }}
                  styles={{
                    root: {
                      background: 'transparent',
                          border: 'none',
                      borderRadius: 8,
                      padding: '8px 4px',
                    },
                    file: {
                      background: 'rgba(0, 0, 0, 0.04)',
                      border: '1px solid rgba(0, 0, 0, 0.08)',
                      borderRadius: 8,
                      transition: 'all 0.2s',
                      padding: '6px 12px',
                    },
                  }}
                />
              ) : false
            }
            footer={() => null}
            styles={{
              root: { 
                border: isMobile ? '1px solid rgba(139, 92, 246, 0.4)' : '1px solid rgba(139, 92, 246, 0.3)', 
                borderRadius: isMobile ? 24 : 20, 
                boxShadow: isMobile 
                  ? '0 4px 20px rgba(139, 92, 246, 0.3), 0 0 0 1px rgba(139, 92, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                  : '0 4px 16px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(139, 92, 246, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
                background: isMobile 
                  ? 'linear-gradient(135deg, rgba(10, 10, 26, 0.98), rgba(26, 10, 46, 0.98))'
                  : 'linear-gradient(135deg, rgba(10, 10, 26, 0.95), rgba(26, 10, 46, 0.95))',
                backdropFilter: 'blur(20px)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                padding: isMobile ? '8px 6px' : '4px 2px',
                minHeight: isMobile ? 56 : 48,
                margin: 0,
                position: 'relative',
                zIndex: 'auto',
              },
              content: { 
                background: 'transparent', 
                borderRadius: isMobile ? 24 : 20, 
                border: 'none',
                color: '#e2e8f0',
                padding: isMobile ? '10px 14px' : '8px 12px',
                fontSize: isMobile ? 16 : 14,
                lineHeight: 1.5,
                margin: 0,
                minHeight: isMobile ? 48 : 'auto',
              },
              input: {
                color: '#e2e8f0',
                fontSize: 14,
                height: '34px',
                lineHeight: '34px',
                maxHeight: '272px',
                outline: 'none',
                background: 'transparent !important',
                border: 'none !important',
                padding: 0,
                margin: 0,
              } as React.CSSProperties,
              prefix: {
                marginLeft: 2,
                marginRight: 2,
              },
              suffix: { 
                paddingRight: 6,
                marginRight: 2,
              },
            }}
            classNames={{
              root: 'frog-gpt-sender-root',
              content: 'frog-gpt-sender-content',
            }}
          />
        </div>
      </div>
    </Card>
  )
}

export default AiChatPanelV2
