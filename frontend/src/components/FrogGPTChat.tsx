/**
 * FrogGPT ChatKit 组件 - 高级AI中枢聊天界面
 * 基于 ChatGPT 风格的现代化聊天体验
 */
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Input,
  Button,
  Avatar,
  Spin,
  message,
  Space,
  Typography,
  Tooltip,
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  CopyOutlined,
  ReloadOutlined,
  StopOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chatkitApi } from '@/services/chatkitApi'
import { useDashboardStore } from '@/stores/dashboardStore'
import { ChatMessage, DashboardCommand } from '@/types/chatkit'

const { TextArea } = Input
const { Text } = Typography

interface FrogGPTChatProps {
  shopId?: number
  shopIds?: number[]
  onCommand?: (command: DashboardCommand) => void
}

export const FrogGPTChat: React.FC<FrogGPTChatProps> = ({
  shopId,
  shopIds,
  onCommand,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const dispatchCommand = useDashboardStore((state) => state.dispatchCommand)

  // 创建会话
  const { data: session, isLoading: sessionLoading, error: sessionError, refetch: refetchSession } = useQuery({
    queryKey: ['chatkit-session', shopId, shopIds],
    queryFn: async () => {
      try {
        console.log('正在创建 ChatKit 会话...', { shopId, shopIds })
        const result = await chatkitApi.createSession(shopId, shopIds)
        console.log('ChatKit 会话创建成功:', result)
        return result
      } catch (error: any) {
        console.error('ChatKit 会话创建失败:', error)
        const errorMessage = error?.response?.data?.detail || error?.message || '未知错误'
        throw new Error(errorMessage)
      }
    },
    enabled: !sessionId,
    retry: 2,
    retryDelay: 1000,
    staleTime: Infinity, // 会话数据不会过期
  })

  // 处理会话创建成功
  useEffect(() => {
    if (session && !sessionId) {
      console.log('设置会话 ID:', session.session_id)
      setSessionId(session.session_id)
      // 添加欢迎消息（新版本 ChatKit 组件）
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: `👋 你好！我是 **FrogGPT**，你的智能AI运营助手。

我可以帮你：

📊 **数据分析**
- 查看今日销售总结
- 分析最近 7 天 GMV 变化趋势
- 对比多个店铺的销售表现

💰 **盈利分析**
- 找出最赚钱的 SKU
- 分析商品利润结构
- 识别亏损商品

🔍 **异常监控**
- 查看退款异常的商品
- 分析发货延迟情况
- 监控库存预警

当前店铺：**${session.metadata.shopId ? `店铺 ${session.metadata.shopId}` : '所有店铺'}**

💡 **试试问我：**
- "展示最近 14 天 GMV 趋势"
- "分析今日销售情况"
- "找出最赚钱的 10 个 SKU"
- "对比店铺 1 和店铺 2 的销售表现"`,
        timestamp: Date.now(),
      }
      setMessages([welcomeMessage])
    }
  }, [session, sessionId])

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, scrollToBottom])

  // 发送消息
  const handleSend = useCallback(async () => {
    if (!input.trim() || loading || !sessionId) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setStreaming(true)
    setStreamingContent('')

    // 创建 AbortController
    const controller = new AbortController()
    setAbortController(controller)

    try {
      const selectedShops = useDashboardStore.getState().selectedShops

      const response = await fetch('/api/chatkit/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        signal: controller.signal,
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          shop_ids: shopIds || selectedShops.length > 0 ? selectedShops : undefined,
          history: messages.map((msg) => ({
            role: msg.role,
            content: msg.content,
          })),
        }),
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let fullContent = ''
      let currentThinking = ''

      while (true) {
        if (controller.signal.aborted) {
          reader.cancel()
          break
        }

        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'thinking') {
                currentThinking += data.content || ''
              } else if (data.type === 'content') {
                fullContent += data.data || ''
                setStreamingContent(fullContent)
              } else if (data.type === 'dashboard_command') {
                // 处理 Dashboard 指令
                const command: DashboardCommand = data.data
                dispatchCommand(command)
                if (onCommand) {
                  onCommand(command)
                }
                // 在消息中显示指令提示
                fullContent += `\n\n[已执行 Dashboard 指令: ${command.type}]\n`
                setStreamingContent(fullContent)
              } else if (data.type === 'done') {
                // 完成
                setStreaming(false)
                setStreamingContent('')
                const assistantMessage: ChatMessage = {
                  id: `assistant-${Date.now()}`,
                  role: 'assistant',
                  content: fullContent,
                  timestamp: Date.now(),
                }
                setMessages((prev) => [...prev, assistantMessage])
                setLoading(false)
                return
              } else if (data.type === 'error') {
                throw new Error(data.data || '未知错误')
              }
            } catch (e) {
              // 忽略 JSON 解析错误
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        message.info('已取消请求')
      } else {
        message.error(`发送失败: ${error.message}`)
        console.error('发送消息失败:', error)
      }
    } finally {
      setLoading(false)
      setStreaming(false)
      setStreamingContent('')
      setAbortController(null)
    }
  }, [input, loading, sessionId, shopIds, messages, dispatchCommand, onCommand])

  // 停止生成
  const handleStop = useCallback(() => {
    if (abortController) {
      abortController.abort()
      setAbortController(null)
      setStreaming(false)
      setLoading(false)
    }
  }, [abortController])

  // 复制消息
  const handleCopy = useCallback((content: string) => {
    navigator.clipboard.writeText(content)
    message.success('已复制到剪贴板')
  }, [])

  // 重新生成
  const handleRegenerate = useCallback(() => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages].reverse().find((msg) => msg.role === 'user')
      if (lastUserMessage) {
        setMessages((prev) => prev.filter((msg) => msg.id !== lastUserMessage.id))
        setInput(lastUserMessage.content)
        setTimeout(() => handleSend(), 100)
      }
    }
  }, [messages, handleSend])

  // 快捷键
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (sessionLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '12px',
          gap: '16px',
        }}
      >
        <Spin size="large" />
        <Text style={{ color: '#94a3b8', fontSize: '14px' }}>正在初始化 AI 会话...</Text>
      </div>
    )
  }

  if (sessionError) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '12px',
          padding: '24px',
          gap: '16px',
        }}
      >
        <Text type="danger" style={{ fontSize: '16px', fontWeight: 600 }}>
          加载失败
        </Text>
        <Text style={{ color: '#94a3b8', fontSize: '14px', textAlign: 'center' }}>
          {sessionError instanceof Error 
            ? sessionError.message 
            : '无法连接到 AI 服务，请检查网络连接或联系管理员'}
        </Text>
        <Button
          type="primary"
          onClick={() => {
            setSessionId(null)
            refetchSession()
          }}
        >
          重试
        </Button>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'rgba(15, 23, 42, 0.6)',
        borderRadius: '12px',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        overflow: 'hidden',
      }}
    >
      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onCopy={handleCopy}
            onRegenerate={msg.role === 'assistant' ? handleRegenerate : undefined}
          />
        ))}

        {/* 流式内容 */}
        {streaming && streamingContent && (
          <MessageBubble
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              timestamp: Date.now(),
            }}
            isStreaming
            onCopy={handleCopy}
          />
        )}

        {/* 加载状态 */}
        {loading && !streaming && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px' }}>
            <Avatar
              size={32}
              style={{
                background: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
              }}
              icon={<RobotOutlined />}
            />
            <Spin size="small" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div
        style={{
          padding: '12px',
          borderTop: '1px solid rgba(99, 102, 241, 0.2)',
          background: 'rgba(2, 6, 23, 0.4)',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading || !sessionId}
            style={{
              flex: 1,
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              color: '#e5e7eb',
              borderRadius: '12px',
            }}
          />
          <Space direction="vertical" size={4}>
            {streaming && (
              <Button
                size="small"
                icon={<StopOutlined />}
                onClick={handleStop}
                danger
              >
                停止
              </Button>
            )}
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!input.trim() || loading || !sessionId}
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                border: 'none',
              }}
            >
              发送
            </Button>
          </Space>
        </div>
        <Text
          style={{
            fontSize: '10px',
            color: '#64748b',
            marginTop: '4px',
            display: 'block',
          }}
        >
          Enter 发送 · Shift+Enter 换行
        </Text>
      </div>
    </div>
  )
}

// 消息气泡组件
interface MessageBubbleProps {
  message: ChatMessage
  isStreaming?: boolean
  onCopy?: (content: string) => void
  onRegenerate?: () => void
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isStreaming,
  onCopy,
  onRegenerate,
}) => {
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        animation: 'fadeInUp 0.3s ease-out',
      }}
    >
      {!isUser && (
        <Avatar
          size={32}
          style={{
            background: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
            flexShrink: 0,
          }}
          icon={<RobotOutlined />}
        />
      )}

      <div
        style={{
          maxWidth: '75%',
          background: isUser
            ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
            : 'rgba(30, 41, 59, 0.95)',
          color: isUser ? '#f9fafb' : '#e5e7eb',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          padding: '12px 16px',
          fontSize: '14px',
          lineHeight: '1.7',
          border: isUser
            ? '1px solid rgba(255, 255, 255, 0.15)'
            : '1px solid rgba(99, 102, 241, 0.25)',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          position: 'relative',
        }}
      >
        {isUser ? (
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {message.content}
          </div>
        ) : (
          <div>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: ({ node, inline, className, children, ...props }: any) => {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <pre
                      style={{
                        background: 'rgba(0, 0, 0, 0.3)',
                        padding: '12px',
                        borderRadius: '8px',
                        overflow: 'auto',
                        fontSize: '12px',
                      }}
                    >
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  ) : (
                    <code
                      style={{
                        background: 'rgba(99, 102, 241, 0.2)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                      {...props}
                    >
                      {children}
                    </code>
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
            {isStreaming && (
              <span
                style={{
                  display: 'inline-block',
                  width: '8px',
                  height: '16px',
                  background: '#6366f1',
                  marginLeft: '4px',
                  animation: 'blink 1s infinite',
                }}
              />
            )}
          </div>
        )}

        {/* 操作按钮 */}
        {!isUser && !isStreaming && (
          <div
            style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              display: 'flex',
              gap: '4px',
              opacity: 0,
              transition: 'opacity 0.2s',
            }}
            className="message-actions"
          >
            {onCopy && (
              <Tooltip title="复制">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => onCopy(message.content)}
                  style={{ color: '#cbd5e1' }}
                />
              </Tooltip>
            )}
            {onRegenerate && (
              <Tooltip title="重新生成">
                <Button
                  type="text"
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={onRegenerate}
                  style={{ color: '#cbd5e1' }}
                />
              </Tooltip>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <Avatar
          size={32}
          style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            flexShrink: 0,
          }}
          icon={<UserOutlined />}
        />
      )}

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
        .message-actions {
          opacity: 0;
        }
        div:hover .message-actions {
          opacity: 1;
        }
      `}</style>
    </div>
  )
}

