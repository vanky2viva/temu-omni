import React, { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Row,
  Col,
  Space,
  Button,
  Avatar,
  Input,
  message,
  Spin,
  Select,
  Popover,
  Form,
  Switch,
  InputNumber,
  Typography,
} from 'antd'
import {
  ThunderboltOutlined,
  UploadOutlined,
  DeleteOutlined,
  RobotOutlined,
  SendOutlined,
  SettingOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import ReactECharts from 'echarts-for-react'
import { forggptApi, shopApi, statisticsApi, aiConfigApi } from '@/services/api'
import dayjs from 'dayjs'

// 生成唯一ID的辅助函数
const generateId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const { TextArea } = Input
const { Text } = Typography

type MessageRole = 'user' | 'assistant'

interface Message {
  id: string
  role: MessageRole
  title?: string
  content: string
  createdAt: string
}

// 快捷提示词（用于空状态显示）
const quickPrompts = [
  '生成今日销售总结',
  '分析最近 7 天 GMV 变化',
  '找出最近 30 天最赚钱的 SKU',
  '查看退款异常的商品',
]

export default function ForgGPT() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>(() => {
    const saved = localStorage.getItem('forggpt_session_id')
    return saved || generateId()
  })
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [thinkingContent, setThinkingContent] = useState('')
  const [showThinking, setShowThinking] = useState(false)
  const [thinkingCompleted, setThinkingCompleted] = useState(false)
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null)
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false)
  const [settingsForm] = Form.useForm()
  // 文件上传相关状态
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ id: string; name: string; type: string; size: number; url?: string; desc?: string }>>([])
  const [isDragging, setIsDragging] = useState(false)
  const dragCounterRef = useRef(0)
  const dateRange = {
    start: dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    end: dayjs().format('YYYY-MM-DD'),
  }
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const thinkingContentRef = useRef<HTMLDivElement>(null)

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取最近7天统计数据
  const { data: stats7d } = useQuery({
    queryKey: ['forggpt_stats_7d', selectedShopId],
    queryFn: () =>
      statisticsApi.getDaily({
        shop_ids: selectedShopId ? [selectedShopId] : undefined,
        days: 7,
      }),
    staleTime: 5 * 60 * 1000,
  })

  // 获取AI配置
  const { data: aiConfigData, refetch: refetchAiConfig } = useQuery({
    queryKey: ['ai-config'],
    queryFn: () => aiConfigApi.getConfig(),
    enabled: isSettingsModalOpen,
  })

  // 当配置数据加载完成时，填充表单（预填常见默认值）
  useEffect(() => {
    if (isSettingsModalOpen && aiConfigData?.data) {
      const config = aiConfigData.data
      settingsForm.setFieldsValue({
        provider: config.provider || 'deepseek',
        // DeepSeek 默认值
        deepseek_api_key: config.deepseek_api_key || '',
        deepseek_base_url: config.deepseek_base_url || 'https://api.deepseek.com',
        deepseek_model: config.deepseek_model || 'deepseek-chat',
        // OpenAI 默认值
        openai_api_key: config.openai_api_key || '',
        openai_base_url: config.openai_base_url || 'https://api.openai.com/v1',
        openai_model: config.openai_model || 'gpt-4o',
        // 通用配置默认值
        timeout_seconds: config.timeout_seconds || 60,
        cache_enabled: config.cache_enabled !== undefined ? config.cache_enabled : true,
        cache_ttl_days: config.cache_ttl_days || 30,
        daily_limit: config.daily_limit || 1000,
      })
    } else if (isSettingsModalOpen && !aiConfigData) {
      // 如果还没有加载配置，先设置默认值
      settingsForm.setFieldsValue({
        provider: 'deepseek',
        deepseek_base_url: 'https://api.deepseek.com',
        deepseek_model: 'deepseek-chat',
        openai_base_url: 'https://api.openai.com/v1',
        openai_model: 'gpt-4o',
        timeout_seconds: 60,
        cache_enabled: true,
        cache_ttl_days: 30,
        daily_limit: 1000,
      })
    }
  }, [isSettingsModalOpen, aiConfigData, settingsForm])

  // 加载对话历史
  useEffect(() => {
    localStorage.setItem('forggpt_session_id', sessionId)
    const loadHistory = async () => {
      try {
        const response = await forggptApi.getHistory(sessionId)
        if (response && response.data && response.data.history) {
          setMessages(
            response.data.history.map((msg: any, index: number) => ({
              id: msg.timestamp || `${Date.now()}-${index}`,
              role: msg.role,
              content: msg.content,
              createdAt: msg.timestamp ? dayjs(msg.timestamp).format('HH:mm') : dayjs().format('HH:mm'),
            }))
          )
        }
      } catch (error) {
        console.error('加载对话历史失败:', error)
      }
    }
    loadHistory()
  }, [sessionId])

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 滚动思考内容到底部（使用 instant 确保实时更新时快速滚动）
  const scrollThinkingToBottom = () => {
    if (thinkingContentRef.current) {
      // 直接设置 scrollTop，使用 instant 滚动以跟上实时更新
      thinkingContentRef.current.scrollTop = thinkingContentRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // 当思考内容更新时，滚动到思考内容底部和消息容器底部
  useEffect(() => {
    if (showThinking && thinkingContent) {
      // 先滚动消息容器，显示思考内容区域
      scrollToBottom()
      // 使用 requestAnimationFrame 确保 DOM 已更新后再滚动思考内容内部
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          scrollThinkingToBottom()
        })
      })
    }
  }, [thinkingContent, showThinking])

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      createdAt: dayjs().format('HH:mm'),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input.trim()
    setInput('')
    setLoading(true)
    setIsStreaming(false)
    setStreamingContent('')
    setThinkingContent('')
    setShowThinking(false)
    setThinkingCompleted(false)

    try {
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }))

      const response = await fetch('/api/forggpt/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: currentInput,
          session_id: sessionId,
          shop_ids: selectedShopId ? [selectedShopId] : undefined,
          date_range: dateRange,
          stream: true,
          history: history,
        }),
      })

      if (!response.ok) {
        // 尝试读取错误信息
        let errorMessage = '请求失败'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch (e) {
          errorMessage = `请求失败: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      setIsStreaming(true)
      let currentSessionId = sessionId
      let assistantMessageId = (Date.now() + 1).toString()
      let fullContent = ''
      let currentThinking = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'session_id') {
                currentSessionId = data.data
                setSessionId(currentSessionId)
              } else if (data.type === 'thinking') {
                // 思考过程 - 始终显示最新内容
                currentThinking += data.content || ''
                setThinkingContent(currentThinking)
                setShowThinking(true)
                setThinkingCompleted(false)
              } else if (data.type === 'thinking_end') {
                // 思考结束，自动折叠但保留内容
                setThinkingCompleted(true)
                // 延迟一下再折叠，让用户看到思考完成
                setTimeout(() => {
                  setShowThinking(false)
                }, 500)
              } else if (data.type === 'content') {
                // 正常内容
                fullContent += data.data || data.content || ''
                setStreamingContent(fullContent)
              } else if (data.type === 'done') {
                const assistantMessage: Message = {
                  id: assistantMessageId,
                  role: 'assistant',
                  content: fullContent,
                  createdAt: dayjs().format('HH:mm'),
                }
                setMessages((prev) => [...prev, assistantMessage])
                setStreamingContent('')
                // 保留思考内容，但自动折叠
                setThinkingCompleted(true)
                setShowThinking(false)
                setIsStreaming(false)
                // 保存历史
                await forggptApi.chat({
                  message: currentInput,
                  session_id: currentSessionId,
                  history: [
                    ...history,
                    { role: 'user', content: currentInput },
                    { role: 'assistant', content: fullContent },
                  ],
                  stream: false,
                })
              } else if (data.type === 'error') {
                const errorMsg = data.data || 'AI服务调用失败'
                throw new Error(errorMsg)
              }
            } catch (e) {
              console.warn('解析流式响应失败:', e)
            }
          }
        }
      }
    } catch (error: any) {
      message.error(error.message || '发送消息失败')
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `抱歉，发生了错误：${error.message || '未知错误'}`,
        createdAt: dayjs().format('HH:mm'),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setIsStreaming(false)
      // 如果思考过程还在显示且未完成，确保标记为完成并折叠
      if (showThinking && !thinkingCompleted) {
        setThinkingCompleted(true)
        setTimeout(() => {
          setShowThinking(false)
        }, 500)
      }
    }
  }

  const handleQuickClick = (prompt: string) => {
    setInput(prompt)
    // 自动发送
    setTimeout(() => {
      handleSend()
    }, 100)
  }

  const handleClear = () => {
    setMessages([])
    setInput('')
    setStreamingContent('')
    setThinkingContent('')
    setShowThinking(false)
    setThinkingCompleted(false)
    setUploadedFiles([]) // 清空已上传的文件列表
    message.success('对话已清空')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // 处理文件上传（支持多种文件类型）
  const handleFileUpload = async (file: File | Blob, fileName?: string) => {
    try {
      // 如果是 Blob，需要转换为 File
      const fileToUpload = file instanceof File ? file : new File([file], fileName || `file_${Date.now()}`)
      
      // 检查文件类型和大小
      const maxSize = 50 * 1024 * 1024 // 50MB
      if (fileToUpload.size > maxSize) {
        message.error('文件大小不能超过 50MB')
        return false
      }

      // 添加文件到上传列表（先显示，后上传）
      const fileId = generateId()
      const fileInfo = {
        id: fileId,
        name: fileToUpload.name || fileName || '未命名文件',
        type: fileToUpload.type || 'unknown',
        size: fileToUpload.size,
      }
      setUploadedFiles(prev => [...prev, fileInfo])

      // 上传文件
      try {
        const response = await forggptApi.uploadFile(fileToUpload)
        // 更新文件信息（使用服务器返回的信息）
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, ...response.data, desc: response.data?.message || `${formatFileSize(fileToUpload.size)}` }
            : f
        ))
        message.success('文件上传成功')
      } catch (error: any) {
        // 上传失败，从列表中移除
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
        message.error(`文件上传失败: ${error.message || '未知错误'}`)
      }
      
      return false
    } catch (error: any) {
      message.error(`文件处理失败: ${error.message}`)
      return false
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  // 处理拖拽上传
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current++
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current--
    if (dragCounterRef.current === 0) {
      setIsDragging(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    dragCounterRef.current = 0

    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) {
      // 可能是拖拽的链接
      const url = e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/plain')
      if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
        handleLinkUpload(url)
        return
      }
      return
    }

    // 处理文件
    for (const file of files) {
      await handleFileUpload(file)
    }
  }

  // 处理链接上传
  const handleLinkUpload = async (url: string) => {
    try {
      // 验证URL格式
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        message.error('请输入有效的URL链接')
        return
      }

      // 添加到文件列表
      const fileId = generateId()
      const fileInfo = {
        id: fileId,
        name: url,
        type: 'url',
        size: 0,
        url: url,
        desc: '在线链接',
      }
      setUploadedFiles(prev => [...prev, fileInfo])
      message.success('链接已添加')

      // 可选：发送到后端处理
      // await forggptApi.uploadFile(url)
    } catch (error: any) {
      message.error(`链接添加失败: ${error.message}`)
    }
  }

  // 处理粘贴事件（支持图片、链接、文本）
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items || items.length === 0) return

      // 检查是否在输入框中
      const target = e.target as HTMLElement
      const isInInput = target.tagName === 'TEXTAREA' || target.tagName === 'INPUT'

      for (const item of Array.from(items)) {
        // 处理粘贴的图片
        if (item.type.indexOf('image') !== -1) {
          e.preventDefault()
          const blob = item.getAsFile()
          if (blob) {
            const timestamp = Date.now()
            const extension = item.type.split('/')[1] || 'png'
            const file = new File([blob], `粘贴图片_${timestamp}.${extension}`, { type: item.type })
            await handleFileUpload(file)
            message.success('图片已粘贴上传')
          }
        }
        // 处理粘贴的链接或文本（仅当在输入框外粘贴时）
        else if (item.type === 'text/plain' && !isInInput) {
          item.getAsString((text) => {
            const trimmedText = text.trim()
            // 检查是否是链接
            if (trimmedText.match(/^https?:\/\/.+/)) {
              e.preventDefault()
              handleLinkUpload(trimmedText)
            }
          })
        }
      }
    }

    // 监听全局粘贴事件
    document.addEventListener('paste', handlePaste)
    return () => {
      document.removeEventListener('paste', handlePaste)
    }
  }, [])

  // 检测输入框中的链接并自动提取
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInput(value)
    
    // 检测是否输入了链接（简单的URL检测）
    const urlMatch = value.match(/https?:\/\/[^\s]+/g)
    if (urlMatch && urlMatch.length > 0) {
      // 可选：提示用户是否要将链接添加为文件
      // 这里先不做自动处理，让用户手动操作
    }
  }

  // 从输入框中提取链接并上传
  const handleExtractLinkFromInput = () => {
    const urlMatch = input.match(/https?:\/\/[^\s]+/g)
    if (urlMatch && urlMatch.length > 0) {
      urlMatch.forEach(url => {
        handleLinkUpload(url)
      })
      // 从输入框中移除链接
      const newInput = input.replace(/https?:\/\/[^\s]+/g, '').trim()
      setInput(newInput)
      message.success(`已添加 ${urlMatch.length} 个链接`)
    } else {
      message.info('输入框中未检测到链接')
    }
  }


  const handleSaveSettings = async () => {
    try {
      const values = await settingsForm.validateFields()
      await aiConfigApi.updateConfig(values)
      message.success('AI配置更新成功')
      setIsSettingsModalOpen(false)
      refetchAiConfig()
    } catch (error: any) {
      message.error(`保存失败: ${error.message}`)
    }
  }

  // 统计数据
  const totalGmv7d = stats7d?.data?.total_gmv || 0
  const totalOrders7d = stats7d?.data?.total_orders || 0
  const totalProfit7d = stats7d?.data?.total_profit || 0
  const totalCost7d = stats7d?.data?.total_cost || 0
  const avgOrderValue7d = stats7d?.data?.avg_order_value || 0
  const refundRate7d = stats7d?.data?.refund_rate || 0

  const formatCurrency = (value: number) => {
    if (value >= 10000) {
      return `¥${(value / 10000).toFixed(1)}万`
    }
    return `¥${value.toFixed(0)}`
  }

  const formatNumber = (value: number) => {
    return value.toLocaleString('zh-CN')
  }

  const profitMargin = totalGmv7d > 0 ? ((totalProfit7d / totalGmv7d) * 100).toFixed(1) : '0'

  // 使用 useEffect 动态计算高度，确保完全适应视口
  const [containerHeight, setContainerHeight] = useState<number>(0)
  
  useEffect(() => {
    const calculateHeight = () => {
      // 获取 MainLayout Header 的实际高度
      const header = document.querySelector('.site-header') as HTMLElement
      const headerHeight = header?.offsetHeight || 64
      
      // 获取 Content 的实际 margin
      const content = document.querySelector('.site-content')?.parentElement as HTMLElement
      const contentMarginTop = parseInt(getComputedStyle(content || document.body).marginTop) || 24
      const contentMarginBottom = parseInt(getComputedStyle(content || document.body).marginBottom) || 16
      
      // 计算可用高度
      const availableHeight = window.innerHeight - headerHeight - contentMarginTop - contentMarginBottom
      setContainerHeight(availableHeight)
    }
    
    calculateHeight()
    window.addEventListener('resize', calculateHeight)
    return () => window.removeEventListener('resize', calculateHeight)
  }, [])

  return (
    <div
      style={{
        height: containerHeight > 0 ? `${containerHeight}px` : 'calc(100vh - 64px - 24px - 16px - 4px)',
        background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%)',
        color: '#e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
        margin: '-24px', // 抵消 MainLayout Content 的 padding: 24px
        boxSizing: 'border-box',
      }}
    >
      {/* 赛博科技感背景效果 */}
      <style>{`
        @keyframes cyberGlow {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.6; }
        }
        @keyframes scanLine {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.5); }
          50% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.8), 0 0 30px rgba(99, 102, 241, 0.4); }
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      `}</style>

      {/* 顶部工具栏 - 紧凑设计，集成到页面内 */}
      <div
        style={{
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(2, 6, 23, 0.95) 100%)',
          borderBottom: '1px solid rgba(99, 102, 241, 0.3)',
          padding: '6px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '44px',
          flexShrink: 0,
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.3)',
          position: 'relative',
        }}
      >
        {/* 顶部发光效果 */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.8), transparent)',
            animation: 'cyberGlow 2s ease-in-out infinite',
          }}
        />
        
        <Space align="center" size={12}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #22c55e 0%, #10b981 50%, #059669 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '18px',
              boxShadow: '0 0 15px rgba(34, 197, 94, 0.4)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
            }}
          >
            🐸
          </div>
          <div>
            <div style={{ fontSize: '15px', color: '#e5e7eb', fontWeight: 600, letterSpacing: '0.5px' }}>
              FrogGPT
            </div>
            <div style={{ fontSize: '10px', color: '#6366f1', fontFamily: 'monospace', marginTop: '1px' }}>
              AI ANALYSIS SYSTEM
            </div>
          </div>
        </Space>

        <Space size={8}>
          <Select
            value={selectedShopId || undefined}
            onChange={(value) => setSelectedShopId(value || null)}
            placeholder="所有店铺"
            style={{ width: 100 }}
            dropdownStyle={{ background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.3)' }}
            allowClear
            size="small"
          >
            {shops?.data?.map((shop: any) => (
              <Select.Option key={shop.id} value={shop.id}>
                {shop.shop_name}
              </Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            size="small"
            onClick={() => {
              setInput('生成今日销售总结')
              handleSend()
            }}
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              border: 'none',
              height: '30px',
              boxShadow: '0 2px 8px rgba(99, 102, 241, 0.4)',
            }}
          >
            今日报告
          </Button>
          <Popover
            title={
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#e5e7eb' }}>AI模型配置</div>
            }
            open={isSettingsModalOpen}
            onOpenChange={setIsSettingsModalOpen}
            trigger="click"
            placement="bottomRight"
            content={
              <div style={{ width: '480px', maxHeight: '70vh', overflowY: 'auto' }}>
                <Spin spinning={!aiConfigData}>
                  <Form form={settingsForm} layout="vertical" initialValues={{ provider: 'deepseek' }}>
                    <Form.Item 
                      label="* AI 服务提供商" 
                      name="provider" 
                      rules={[{ required: true, message: '请选择AI服务提供商' }]}
                      tooltip="选择使用的AI服务提供商"
                      style={{ marginBottom: '16px' }}
                    >
                      <Select style={{ width: '100%' }}>
                        <Select.Option value="deepseek">DeepSeek</Select.Option>
                        <Select.Option value="openai">OpenAI</Select.Option>
                      </Select>
                    </Form.Item>

                    {/* 根据选择的provider动态显示配置 */}
                    <Form.Item shouldUpdate={(prevValues, currentValues) => prevValues.provider !== currentValues.provider} noStyle>
                      {({ getFieldValue }) => {
                        const provider = getFieldValue('provider') || 'deepseek'
                        return provider === 'deepseek' ? (
                          <>
                            <Form.Item label="API Key" name="deepseek_api_key" tooltip="DeepSeek API 密钥，必填项">
                              <Input.Password 
                                placeholder={aiConfigData?.data?.has_deepseek_api_key ? '已配置，可留空不修改' : '请输入 DeepSeek API Key'}
                                autoComplete="off"
                                size="small"
                              />
                            </Form.Item>
                            <Form.Item label="Base URL" name="deepseek_base_url" tooltip="DeepSeek API 基础 URL">
                              <Input placeholder="https://api.deepseek.com" size="small" />
                            </Form.Item>
                            <Form.Item label="模型名称" name="deepseek_model" tooltip="DeepSeek 模型名称，推荐: deepseek-chat, deepseek-coder, deepseek-reasoner">
                              <Input placeholder="deepseek-chat" size="small" />
                            </Form.Item>
                          </>
                        ) : (
                          <>
                            <Form.Item label="API Key" name="openai_api_key" tooltip="OpenAI API 密钥，必填项">
                              <Input.Password 
                                placeholder={aiConfigData?.data?.has_openai_api_key ? '已配置，可留空不修改' : '请输入 OpenAI API Key'}
                                autoComplete="off"
                                size="small"
                              />
                            </Form.Item>
                            <Form.Item label="Base URL" name="openai_base_url" tooltip="OpenAI API 基础 URL">
                              <Input placeholder="https://api.openai.com/v1" size="small" />
                            </Form.Item>
                            <Form.Item label="模型名称" name="openai_model" tooltip="OpenAI 模型名称，推荐: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo">
                              <Input placeholder="gpt-4o" size="small" />
                            </Form.Item>
                          </>
                        )
                      }}
                    </Form.Item>

                    <Form.Item label="AI 调用超时时间 (秒)" name="timeout_seconds" tooltip="API 请求超时时间，推荐 60-120 秒">
                      <InputNumber min={1} max={300} style={{ width: '100%' }} placeholder="60" size="small" />
                    </Form.Item>
                    <Form.Item label="启用 AI 结果缓存" name="cache_enabled" valuePropName="checked" tooltip="开启后相同问题的回答会被缓存，减少 API 调用">
                      <Switch size="small" />
                    </Form.Item>
                    <Form.Item label="AI 缓存过期天数" name="cache_ttl_days" tooltip="缓存结果保留天数，过期后自动清理">
                      <InputNumber min={1} max={365} style={{ width: '100%' }} placeholder="30" size="small" />
                    </Form.Item>
                    <Form.Item label="每日 AI 调用次数限制" name="daily_limit" tooltip="每日最多调用 AI API 的次数，防止超量使用">
                      <InputNumber min={1} max={100000} style={{ width: '100%' }} placeholder="1000" size="small" />
                    </Form.Item>
                    
                    <Form.Item style={{ marginBottom: 0, marginTop: '16px' }}>
                      <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                        <Button size="small" onClick={() => setIsSettingsModalOpen(false)}>
                          取消
                        </Button>
                        <Button type="primary" size="small" onClick={handleSaveSettings}>
                          保存
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </Spin>
              </div>
            }
            overlayStyle={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '8px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
            }}
            overlayInnerStyle={{
              background: 'rgba(15, 23, 42, 0.95)',
              padding: '16px',
            }}
          >
            <Button
              icon={<SettingOutlined />}
              size="small"
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#cbd5e1',
                height: '30px',
              }}
            />
          </Popover>
        </Space>
      </div>

      {/* 主体内容 - 精确计算高度 */}
      <div
        style={{
          padding: '8px 12px',
          display: 'flex',
          gap: '12px',
          overflow: 'hidden',
          flex: 1,
          minHeight: 0,
        }}
      >
        {/* 左侧：数据展示区域 */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            minHeight: 0,
            overflowY: 'auto',
            paddingRight: '4px',
          }}
        >
        {/* 数据概览 */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            borderRadius: '12px',
            padding: '16px',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div
            style={{
              fontSize: '16px',
              color: '#e5e7eb',
              fontWeight: 700,
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: '2px solid rgba(99, 102, 241, 0.3)',
              letterSpacing: '0.5px',
            }}
          >
            数据概览
          </div>
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <MetricBlock label="7天GMV" value={formatCurrency(totalGmv7d)} hint="+12.3%" />
            </Col>
            <Col span={8}>
              <MetricBlock label="7天订单" value={`${formatNumber(totalOrders7d)}`} hint="+6.2%" />
            </Col>
            <Col span={8}>
              <MetricBlock label="7天利润" value={formatCurrency(totalProfit7d)} hint={`${profitMargin}%`} />
            </Col>
            <Col span={8}>
              <MetricBlock label="7天成本" value={formatCurrency(totalCost7d)} />
            </Col>
            <Col span={8}>
              <MetricBlock label="客单价" value={formatCurrency(avgOrderValue7d)} />
            </Col>
            <Col span={8}>
              <MetricBlock label="退款率" value={`${(refundRate7d * 100).toFixed(1)}%`} hint="健康" />
            </Col>
          </Row>
        </div>

          {/* 快捷分析 */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              borderRadius: '12px',
              padding: '12px',
              flex: 1,
              overflowY: 'auto',
              minHeight: 0,
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
            }}
          >
            <div
              style={{
                fontSize: '13px',
                color: '#e5e7eb',
                fontWeight: 600,
                marginBottom: '10px',
                paddingBottom: '8px',
                borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
                letterSpacing: '0.5px',
              }}
            >
              快捷分析
            </div>
            <Space direction="vertical" size={6} style={{ width: '100%' }}>
              {[
                { label: '今日销售总结', prompt: '请为我生成今日销售总结，包括 GMV、订单数、客单价、利润、退款情况，并给出主要原因分析。' },
                { label: '7天GMV变化分析', prompt: '请分析最近7天GMV的趋势，以及增长或下降的主要驱动因素，从订单量、客单价、畅销SKU、退款率等维度解释。' },
                { label: 'SKU盈利分析', prompt: '请帮我分析这个SKU的利润结构，包括成本、售价、毛利额、毛利率，并结合最近的销量趋势判断是否值得加大投入。' },
                { label: '商品对比选品', prompt: '请对比销量前10的SKU在最近30天的销量、GMV、利润、退款率，找出最值得重点推广的商品。' },
                { label: '退款异常分析', prompt: '请分析最近30天退款率较高的SKU列表，并找出异常原因（如破损率、发货延迟、材质问题等）。' },
                { label: '店铺对比分析', prompt: '请对比所有店铺的销售表现，包括GMV、订单量、利润、退款率等指标。' },
                { label: '库存预警分析', prompt: '请分析哪些商品需要补货，基于最近7天的销量趋势和当前库存情况。' },
                { label: '价格策略建议', prompt: '请分析当前商品定价是否合理，基于成本、市场表现和利润情况给出价格优化建议。' },
              ].map((item) => (
                <Button
                  key={item.label}
                  block
                  size="small"
                  onClick={() => {
                    setInput(item.prompt)
                    handleSend()
                  }}
                  style={{
                    background: 'rgba(99, 102, 241, 0.1)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    color: '#cbd5e1',
                    fontSize: '12px',
                    height: '32px',
                    textAlign: 'left',
                    borderRadius: '6px',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'
                    e.currentTarget.style.boxShadow = '0 0 10px rgba(99, 102, 241, 0.3)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Space>
          </div>

          {/* 文件列表 */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              borderRadius: '12px',
              padding: '12px',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
            }}
          >
            <div
              style={{
                fontSize: '13px',
                color: '#e5e7eb',
                fontWeight: 600,
                marginBottom: '10px',
                paddingBottom: '8px',
                borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
                letterSpacing: '0.5px',
              }}
            >
              文件
            </div>
            <Space direction="vertical" size={6} style={{ width: '100%' }}>
              {uploadedFiles.length === 0 ? (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '20px',
                    color: '#64748b',
                    fontSize: '12px',
                  }}
                >
                  <div style={{ marginBottom: '8px' }}>📎</div>
                  <div>支持拖拽、粘贴到对话框上传</div>
                  <div style={{ fontSize: '10px', marginTop: '4px' }}>文档、表格、图片、链接</div>
                </div>
              ) : (
                uploadedFiles.map((file) => (
                  <FileItem
                    key={file.id}
                    name={file.name}
                    desc={file.desc || (file.size > 0 ? formatFileSize(file.size) : '')}
                    type={file.type}
                    onRemove={() => setUploadedFiles(prev => prev.filter(f => f.id !== file.id))}
                  />
                ))
              )}
            </Space>
          </div>
        </div>

        {/* 右侧：对话区域 - 缩小宽度 */}
        <div
          style={{
            width: '480px',
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            border: isDragging ? '2px dashed rgba(99, 102, 241, 0.8)' : '1px solid rgba(99, 102, 241, 0.2)',
            borderRadius: '12px',
            overflow: 'hidden',
            backdropFilter: 'blur(10px)',
            boxShadow: isDragging ? '0 0 30px rgba(99, 102, 241, 0.5)' : '0 4px 20px rgba(0, 0, 0, 0.3)',
            transition: 'all 0.3s',
            position: 'relative',
          }}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {/* 拖拽提示遮罩 */}
          {isDragging && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(99, 102, 241, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                borderRadius: '12px',
                backdropFilter: 'blur(5px)',
              }}
            >
              <div
                style={{
                  textAlign: 'center',
                  color: '#818cf8',
                  fontSize: '16px',
                  fontWeight: 600,
                  textShadow: '0 0 10px rgba(99, 102, 241, 0.5)',
                }}
              >
                📎 松开鼠标上传文件
              </div>
            </div>
          )}
          {/* 快捷问题 - 仅在空状态显示 */}
          {messages.length === 0 && !loading && !isStreaming && (
            <div
              style={{
                padding: '8px 12px',
                borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
                background: 'rgba(99, 102, 241, 0.05)',
                flexShrink: 0,
              }}
            >
              <Space wrap size={6}>
                {quickPrompts.map((q) => (
                  <Button
                    key={q}
                    size="small"
                    onClick={() => handleQuickClick(q)}
                    style={{
                      borderRadius: '6px',
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      color: '#cbd5e1',
                      fontSize: '12px',
                      height: '26px',
                      padding: '0 10px',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'
                      e.currentTarget.style.boxShadow = '0 0 10px rgba(99, 102, 241, 0.4)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'
                      e.currentTarget.style.boxShadow = 'none'
                    }}
                  >
                    {q}
                  </Button>
                ))}
              </Space>
            </div>
          )}

          {/* 消息列表 - 可滚动区域 */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              overflowX: 'hidden',
              padding: '12px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              minHeight: 0,
            }}
          >
            {messages.length === 0 && !loading && !isStreaming ? (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  padding: '20px 16px',
                }}
              >
                <div
                  style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '32px',
                    marginBottom: '16px',
                    border: '2px solid rgba(34, 197, 94, 0.3)',
                    boxShadow: '0 0 30px rgba(34, 197, 94, 0.2)',
                  }}
                >
                  🐸
                </div>
                <div
                  style={{
                    fontSize: '18px',
                    fontWeight: 600,
                    color: '#e5e7eb',
                    marginBottom: '6px',
                    letterSpacing: '0.5px',
                  }}
                >
                  你好，我是 FrogGPT
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#94a3b8',
                    lineHeight: '1.5',
                    maxWidth: '450px',
                    marginBottom: '16px',
                  }}
                >
                  我可以帮你分析运营数据，提供经营建议，也可以处理你上传的表格和文档。
                </div>
                <Space wrap size={6}>
                  {quickPrompts.map((q) => (
                    <Button
                      key={q}
                      size="small"
                      onClick={() => handleQuickClick(q)}
                      style={{
                        borderRadius: '6px',
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: '#cbd5e1',
                        fontSize: '12px',
                        height: '28px',
                        padding: '0 12px',
                      }}
                    >
                      {q}
                    </Button>
                  ))}
                </Space>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatBubble key={msg.id} message={msg} />
                ))}
                {/* 思考过程 - 如果已完成但被折叠，显示展开按钮 */}
                {thinkingCompleted && !showThinking && thinkingContent && (
                  <div style={{ marginBottom: '12px' }}>
                    <Button
                      type="text"
                      size="small"
                      onClick={() => setShowThinking(true)}
                      style={{
                        color: '#818cf8',
                        fontSize: '12px',
                        padding: '4px 8px',
                        height: 'auto',
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        borderRadius: '6px',
                      }}
                    >
                      💭 查看思考过程
                    </Button>
                  </div>
                )}
                {/* 思考过程 - 展开状态 */}
                {showThinking && thinkingContent && (
                  <div
                    style={{
                      marginBottom: '12px',
                      padding: '12px 16px',
                      background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      borderRadius: '10px',
                      fontSize: '12px',
                      color: '#cbd5e1',
                      lineHeight: '1.6',
                      boxShadow: '0 0 15px rgba(99, 102, 241, 0.2)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '8px',
                        paddingBottom: '8px',
                        borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
                      }}
                    >
                      <span
                        style={{
                          color: '#818cf8',
                          fontWeight: 600,
                          fontSize: '13px',
                          fontFamily: 'monospace',
                        }}
                      >
                        {thinkingCompleted ? '💭 思考过程' : '💭 AI 正在思考...'}
                      </span>
                      <Button
                        type="text"
                        size="small"
                        style={{
                          color: '#94a3b8',
                          fontSize: '11px',
                          padding: '0 4px',
                          height: 'auto',
                        }}
                        onClick={() => setShowThinking(false)}
                      >
                        收起
                      </Button>
                    </div>
                    <div
                      ref={thinkingContentRef}
                      style={{
                        maxHeight: '200px',
                        overflowY: 'auto',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
                        color: '#a5b4fc',
                        fontSize: '11px',
                      }}
                    >
                      {thinkingContent}
                    </div>
                  </div>
                )}
                {/* 流式内容 */}
                {isStreaming && streamingContent && (
                  <ChatBubble
                    message={{
                      id: 'streaming',
                      role: 'assistant',
                      content: streamingContent,
                      createdAt: dayjs().format('HH:mm'),
                    }}
                    isStreaming={true}
                  />
                )}
                {loading && !isStreaming && (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <Avatar
                      size={32}
                      style={{
                        background: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
                        color: '#022c22',
                        boxShadow: '0 0 10px rgba(34, 197, 94, 0.3)',
                      }}
                      icon={<RobotOutlined />}
                    />
                    <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '10px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                      <Spin size="small" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* 输入框 - 移到对话框内部 */}
          <div
            style={{
              padding: '12px',
              borderTop: '1px solid rgba(99, 102, 241, 0.2)',
              background: 'rgba(2, 6, 23, 0.4)',
              flexShrink: 0,
            }}
          >
            <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <div style={{ marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'space-between' }}>
                  <Button
                    size="small"
                    icon={<DeleteOutlined />}
                    style={{
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      color: '#cbd5e1',
                      fontSize: '11px',
                      height: '24px',
                      padding: '0 8px',
                    }}
                    onClick={handleClear}
                  >
                    清空
                  </Button>
                  <Text
                    style={{
                      fontSize: '10px',
                      color: '#64748b',
                      fontFamily: 'monospace',
                    }}
                  >
                    Enter发送 · Shift+Enter换行 · 拖拽文件/粘贴图片上传
                  </Text>
                </div>
                <TextArea
                  rows={5}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="输入你的问题，或拖拽文件/粘贴图片/链接到此处..."
                  disabled={loading}
                  style={{
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    color: '#e5e7eb',
                    borderRadius: '8px',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    resize: 'none',
                  }}
                />
                {/* 链接提取提示 */}
                {input.match(/https?:\/\/[^\s]+/g) && (
                  <div style={{ marginTop: '4px', fontSize: '11px', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>🔗</span>
                    <span>检测到链接，点击右侧"提取链接"按钮添加到文件列表</span>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {/* 如果输入框中有链接，显示链接提取按钮 */}
                {input.match(/https?:\/\/[^\s]+/g) && (
                  <Button
                    size="small"
                    icon={<UploadOutlined />}
                    onClick={handleExtractLinkFromInput}
                    style={{
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      color: '#818cf8',
                      fontSize: '11px',
                      height: '26px',
                    }}
                  >
                    提取链接
                  </Button>
                )}
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    border: 'none',
                    height: input.match(/https?:\/\/[^\s]+/g) ? '110px' : '120px',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(99, 102, 241, 0.4)',
                    fontSize: '13px',
                  }}
                >
                  发送
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}

// 组件和样式定义
const MetricBlock: React.FC<{
  label: string
  value: string
  hint?: string
}> = ({ label, value, hint }) => (
  <div
    style={{
      background: 'linear-gradient(135deg, rgba(2, 6, 23, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%)',
      borderRadius: '12px',
      padding: '20px 16px',
      border: '2px solid rgba(99, 102, 241, 0.3)',
      transition: 'all 0.3s',
      height: '100%',
      minHeight: '120px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.6)'
      e.currentTarget.style.boxShadow = '0 4px 20px rgba(99, 102, 241, 0.4), 0 0 30px rgba(99, 102, 241, 0.2)'
      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2, 6, 23, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)'
      e.currentTarget.style.transform = 'translateY(-2px)'
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.3)'
      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)'
      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2, 6, 23, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%)'
      e.currentTarget.style.transform = 'translateY(0)'
    }}
  >
    <div style={{ fontSize: '15px', color: '#94a3b8', marginBottom: '12px', fontWeight: 600, letterSpacing: '0.3px' }}>{label}</div>
    <div style={{ fontSize: '28px', color: '#e5e7eb', fontWeight: 800, lineHeight: '1.2', letterSpacing: '1px', textShadow: '0 0 10px rgba(99, 102, 241, 0.3)' }}>{value}</div>
    {hint && (
      <div style={{ fontSize: '14px', color: '#4ade80', marginTop: '10px', fontFamily: 'monospace', fontWeight: 600, textShadow: '0 0 8px rgba(74, 222, 128, 0.3)' }}>{hint}</div>
    )}
  </div>
)

const FileItem: React.FC<{ 
  name: string
  desc: string
  type?: string
  onRemove?: () => void
}> = ({ name, desc, type, onRemove }) => {
  // 根据文件类型显示图标
  const getFileIcon = () => {
    if (type === 'url' || name.startsWith('http://') || name.startsWith('https://')) {
      return '🔗'
    }
    if (type?.startsWith('image/') || /\.(png|jpg|jpeg|gif|webp)$/i.test(name)) {
      return '🖼️'
    }
    if (/\.(xlsx|xls|csv)$/i.test(name)) {
      return '📊'
    }
    if (/\.(doc|docx)$/i.test(name)) {
      return '📄'
    }
    if (/\.(pdf)$/i.test(name)) {
      return '📕'
    }
    if (/\.(txt|md)$/i.test(name)) {
      return '📝'
    }
    return '📎'
  }

  return (
    <div
      style={{
        background: 'rgba(2, 6, 23, 0.6)',
        borderRadius: '8px',
        padding: '8px 10px',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.5)'
        e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.2)'
        e.currentTarget.style.background = 'rgba(2, 6, 23, 0.6)'
      }}
    >
      <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ fontSize: '14px', flexShrink: 0 }}>{getFileIcon()}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: '12px',
              color: '#e5e7eb',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              marginBottom: '2px',
            }}
            title={name}
          >
            {name.length > 20 ? `${name.substring(0, 20)}...` : name}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>{desc}</div>
        </div>
      </div>
      <Space size={4}>
        <Button
          type="link"
          size="small"
          onClick={() => {
            // TODO: 分析文件
            message.info('文件分析功能开发中')
          }}
          style={{
            fontSize: '11px',
            paddingInline: '6px',
            height: '24px',
            color: '#6366f1',
          }}
        >
          分析
        </Button>
        {onRemove && (
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            onClick={onRemove}
            style={{
              fontSize: '10px',
              paddingInline: '4px',
              height: '24px',
              color: '#ef4444',
            }}
          />
        )}
      </Space>
    </div>
  )
}

const ChatBubble: React.FC<{ message: Message; isStreaming?: boolean }> = ({
  message: messageData,
  isStreaming,
}) => {
  const isUser = messageData.role === 'user'

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
        <div
          style={{
            maxWidth: '75%',
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            color: '#f9fafb',
            borderRadius: '12px',
            padding: '10px 14px',
            fontSize: '13px',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6',
            boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          {messageData.content}
          <div
            style={{
              textAlign: 'right',
              fontSize: '10px',
              marginTop: '6px',
              opacity: 0.8,
              fontFamily: 'monospace',
            }}
          >
            {messageData.createdAt}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '8px' }}>
      <Avatar
        size={32}
        style={{
          background: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
          color: '#022c22',
          flexShrink: 0,
          boxShadow: '0 0 10px rgba(34, 197, 94, 0.3)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
        }}
        icon={<RobotOutlined />}
      />
      <div
        style={{
          maxWidth: '75%',
          background: 'rgba(30, 41, 59, 0.8)',
          borderRadius: '12px',
          padding: '12px 14px',
          fontSize: '13px',
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
        }}
      >
        {messageData.title && (
          <div
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: '#4ade80',
              marginBottom: '8px',
              fontFamily: 'monospace',
            }}
          >
            {messageData.title}
          </div>
        )}
        <div style={{ color: '#e5e7eb' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
              // 代码块高亮和图表渲染
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '')
                const language = match ? match[1] : ''
                const codeString = String(children).replace(/\n$/, '')
                
                // 检查是否是图表数据（chart或echarts格式）
                if (!inline && (language === 'chart' || language === 'echarts')) {
                  try {
                    const chartConfig = JSON.parse(codeString)
                    // 验证是否是有效的ECharts配置
                    if (chartConfig && (chartConfig.option || chartConfig.series || chartConfig.xAxis || chartConfig.yAxis)) {
                      const option = chartConfig.option || chartConfig
                      // 应用暗色主题
                      const darkOption = {
                        ...option,
                        backgroundColor: 'transparent',
                        textStyle: {
                          color: '#e5e7eb',
                          ...option.textStyle,
                        },
                        title: option.title ? {
                          ...option.title,
                          textStyle: {
                            color: '#e5e7eb',
                            ...option.title.textStyle,
                          },
                        } : undefined,
                        legend: option.legend ? {
                          ...option.legend,
                          textStyle: {
                            color: '#e5e7eb',
                            ...option.legend.textStyle,
                          },
                        } : undefined,
                        grid: option.grid ? {
                          ...option.grid,
                          borderColor: 'rgba(99, 102, 241, 0.3)',
                          ...option.grid,
                        } : undefined,
                        xAxis: option.xAxis ? (Array.isArray(option.xAxis) ? option.xAxis.map((axis: any) => ({
                          ...axis,
                          axisLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.3)' }, ...axis.axisLine },
                          axisLabel: { color: '#94a3b8', ...axis.axisLabel },
                          splitLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.1)' }, ...axis.splitLine },
                        })) : {
                          ...option.xAxis,
                          axisLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.3)' }, ...option.xAxis.axisLine },
                          axisLabel: { color: '#94a3b8', ...option.xAxis.axisLabel },
                          splitLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.1)' }, ...option.xAxis.splitLine },
                        }) : undefined,
                        yAxis: option.yAxis ? (Array.isArray(option.yAxis) ? option.yAxis.map((axis: any) => ({
                          ...axis,
                          axisLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.3)' }, ...axis.axisLine },
                          axisLabel: { color: '#94a3b8', ...axis.axisLabel },
                          splitLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.1)' }, ...axis.splitLine },
                        })) : {
                          ...option.yAxis,
                          axisLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.3)' }, ...option.yAxis.axisLine },
                          axisLabel: { color: '#94a3b8', ...option.yAxis.axisLabel },
                          splitLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.1)' }, ...option.yAxis.splitLine },
                        }) : undefined,
                      }
                      return (
                        <div style={{ margin: '12px 0', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px', padding: '12px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                          <ReactECharts
                            option={darkOption}
                            style={{ height: chartConfig.height || '300px', width: '100%' }}
                            opts={{ renderer: 'canvas' }}
                          />
                        </div>
                      )
                    }
                  } catch (e) {
                    // JSON解析失败，继续显示为代码
                  }
                }
                
                // JSON格式的图表配置（自动检测）
                if (!inline && language === 'json') {
                  try {
                    const jsonData = JSON.parse(codeString)
                    // 检查是否是ECharts配置
                    if (jsonData && (jsonData.option || jsonData.series || (jsonData.xAxis && jsonData.yAxis))) {
                      const option = jsonData.option || jsonData
                      const darkOption = {
                        ...option,
                        backgroundColor: 'transparent',
                        textStyle: { color: '#e5e7eb', ...option.textStyle },
                      }
                      return (
                        <div style={{ margin: '12px 0', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px', padding: '12px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                          <ReactECharts
                            option={darkOption}
                            style={{ height: jsonData.height || '300px', width: '100%' }}
                            opts={{ renderer: 'canvas' }}
                          />
                        </div>
                      )
                    }
                  } catch (e) {
                    // JSON解析失败，继续显示为代码
                  }
                }
                
                // 普通代码块
                if (!inline && language) {
                  return (
                    <div style={{ position: 'relative', margin: '8px 0' }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '4px 8px',
                          background: 'rgba(0, 0, 0, 0.3)',
                          borderTopLeftRadius: '6px',
                          borderTopRightRadius: '6px',
                          fontSize: '11px',
                          color: '#94a3b8',
                          fontFamily: 'monospace',
                        }}
                      >
                        <span>{language}</span>
                        <Button
                          type="text"
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => {
                            navigator.clipboard.writeText(codeString)
                            message.success('代码已复制')
                          }}
                          style={{
                            color: '#94a3b8',
                            fontSize: '10px',
                            height: '20px',
                            padding: '0 4px',
                          }}
                        >
                          复制
                        </Button>
                      </div>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={language}
                        PreTag="div"
                        customStyle={{
                          margin: 0,
                          borderRadius: '0 0 6px 6px',
                          background: '#1e1e1e',
                          fontSize: '12px',
                          lineHeight: '1.5',
                          padding: '12px',
                        }}
                        {...props}
                      >
                        {codeString}
                      </SyntaxHighlighter>
                    </div>
                  )
                }
                // 行内代码
                return (
                  <code
                    className={className}
                    style={{
                      background: 'rgba(99, 102, 241, 0.2)',
                      color: '#818cf8',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                )
              },
              // 表格样式
              table({ children }: any) {
                return (
                  <div style={{ overflowX: 'auto', margin: '12px 0' }}>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        borderRadius: '6px',
                        overflow: 'hidden',
                      }}
                    >
                      {children}
                    </table>
                  </div>
                )
              },
              thead({ children }: any) {
                return (
                  <thead
                    style={{
                      background: 'rgba(99, 102, 241, 0.15)',
                      borderBottom: '2px solid rgba(99, 102, 241, 0.3)',
                    }}
                  >
                    {children}
                  </thead>
                )
              },
              th({ children }: any) {
                return (
                  <th
                    style={{
                      padding: '8px 12px',
                      textAlign: 'left',
                      border: '1px solid rgba(99, 102, 241, 0.2)',
                      color: '#e5e7eb',
                      fontWeight: 600,
                      fontSize: '12px',
                    }}
                  >
                    {children}
                  </th>
                )
              },
              td({ children }: any) {
                return (
                  <td
                    style={{
                      padding: '8px 12px',
                      border: '1px solid rgba(99, 102, 241, 0.2)',
                      color: '#cbd5e1',
                      fontSize: '12px',
                    }}
                  >
                    {children}
                  </td>
                )
              },
              // 列表样式
              ul({ children }: any) {
                return (
                  <ul
                    style={{
                      margin: '8px 0',
                      paddingLeft: '24px',
                      color: '#cbd5e1',
                      lineHeight: '1.8',
                    }}
                  >
                    {children}
                  </ul>
                )
              },
              ol({ children }: any) {
                return (
                  <ol
                    style={{
                      margin: '8px 0',
                      paddingLeft: '24px',
                      color: '#cbd5e1',
                      lineHeight: '1.8',
                    }}
                  >
                    {children}
                  </ol>
                )
              },
              li({ children }: any) {
                return (
                  <li
                    style={{
                      margin: '4px 0',
                      color: '#cbd5e1',
                    }}
                  >
                    {children}
                  </li>
                )
              },
              // 段落样式
              p({ children }: any) {
                return (
                  <p
                    style={{
                      margin: '8px 0',
                      color: '#e5e7eb',
                      lineHeight: '1.7',
                    }}
                  >
                    {children}
                  </p>
                )
              },
              // 标题样式
              h1({ children }: any) {
                return (
                  <h1
                    style={{
                      fontSize: '18px',
                      fontWeight: 700,
                      color: '#e5e7eb',
                      margin: '12px 0 8px 0',
                      borderBottom: '2px solid rgba(99, 102, 241, 0.3)',
                      paddingBottom: '6px',
                    }}
                  >
                    {children}
                  </h1>
                )
              },
              h2({ children }: any) {
                return (
                  <h2
                    style={{
                      fontSize: '16px',
                      fontWeight: 600,
                      color: '#e5e7eb',
                      margin: '10px 0 6px 0',
                      borderBottom: '1px solid rgba(99, 102, 241, 0.2)',
                      paddingBottom: '4px',
                    }}
                  >
                    {children}
                  </h2>
                )
              },
              h3({ children }: any) {
                return (
                  <h3
                    style={{
                      fontSize: '14px',
                      fontWeight: 600,
                      color: '#e5e7eb',
                      margin: '8px 0 4px 0',
                    }}
                  >
                    {children}
                  </h3>
                )
              },
              // 引用样式
              blockquote({ children }: any) {
                return (
                  <blockquote
                    style={{
                      margin: '8px 0',
                      padding: '8px 12px',
                      borderLeft: '3px solid rgba(99, 102, 241, 0.5)',
                      background: 'rgba(99, 102, 241, 0.1)',
                      borderRadius: '4px',
                      color: '#cbd5e1',
                      fontStyle: 'italic',
                    }}
                  >
                    {children}
                  </blockquote>
                )
              },
              // 链接样式
              a({ href, children }: any) {
                return (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: '#818cf8',
                      textDecoration: 'underline',
                      transition: 'color 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = '#a5b4fc'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = '#818cf8'
                    }}
                  >
                    {children}
                  </a>
                )
              },
              // 强调样式
              strong({ children }: any) {
                return (
                  <strong
                    style={{
                      color: '#fbbf24',
                      fontWeight: 600,
                    }}
                  >
                    {children}
                  </strong>
                )
              },
              // 强调样式
              em({ children }: any) {
                return (
                  <em
                    style={{
                      color: '#cbd5e1',
                      fontStyle: 'italic',
                    }}
                  >
                    {children}
                  </em>
                )
              },
              // 分隔线样式
              hr() {
                return (
                  <hr
                    style={{
                      border: 'none',
                      borderTop: '1px solid rgba(99, 102, 241, 0.3)',
                      margin: '12px 0',
                    }}
                  />
                )
              },
            }}
          >
            {messageData.content}
          </ReactMarkdown>
          {isStreaming && (
            <span
              style={{
                display: 'inline-block',
                width: '2px',
                height: '14px',
                background: '#6366f1',
                animation: 'blink 1s infinite',
                marginLeft: '6px',
                verticalAlign: 'middle',
                borderRadius: '1px',
              }}
            />
          )}
        </div>
        <div
          style={{
            fontSize: '10px',
            color: '#64748b',
            marginTop: '8px',
            fontFamily: 'monospace',
          }}
          >
          FrogGPT · {messageData.createdAt}
        </div>
      </div>
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
