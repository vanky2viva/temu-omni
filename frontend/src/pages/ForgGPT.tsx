import React, { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Layout,
  Typography,
  Card,
  Row,
  Col,
  Space,
  Button,
  Tag,
  Avatar,
  Input,
  List,
  Upload,
  message,
  Spin,
  Select,
  Modal,
  Form,
  Switch,
  InputNumber,
  Tabs,
} from 'antd'
import {
  ThunderboltOutlined,
  UploadOutlined,
  DeleteOutlined,
  RobotOutlined,
  SendOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { forggptApi, shopApi, statisticsApi, aiConfigApi } from '@/services/api'
import dayjs from 'dayjs'

// 生成唯一ID的辅助函数
const generateId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const { Header, Content, Footer } = Layout
const { Title, Text } = Typography
const { TextArea } = Input

type MessageRole = 'user' | 'assistant'

interface Message {
  id: string
  role: MessageRole
  title?: string
  content: string
  createdAt: string
}

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
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null)
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false)
  const [settingsForm] = Form.useForm()
  const dateRange = {
    start: dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    end: dayjs().format('YYYY-MM-DD'),
  }
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  // 当配置数据加载完成时，填充表单
  useEffect(() => {
    if (isSettingsModalOpen && aiConfigData?.data) {
      const config = aiConfigData.data
      settingsForm.setFieldsValue({
        provider: config.provider || 'deepseek',
        deepseek_api_key: config.deepseek_api_key || '',
        deepseek_base_url: config.deepseek_base_url || 'https://api.deepseek.com',
        deepseek_model: config.deepseek_model || 'deepseek-chat',
        openai_api_key: config.openai_api_key || '',
        openai_base_url: config.openai_base_url || 'https://api.openai.com/v1',
        openai_model: config.openai_model || 'gpt-4o',
        timeout_seconds: config.timeout_seconds || 30,
        cache_enabled: config.cache_enabled !== false,
        cache_ttl_days: config.cache_ttl_days || 30,
        daily_limit: config.daily_limit || 1000,
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

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

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
      setShowThinking(false)
      setThinkingContent('')
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
                // 思考过程
                currentThinking += data.content || ''
                setThinkingContent(currentThinking)
                setShowThinking(true)
              } else if (data.type === 'thinking_end') {
                // 思考结束，收起思考过程
                setShowThinking(false)
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
                setThinkingContent('')
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
      // 如果思考过程还在显示，在完成后自动收起
      if (showThinking) {
        setTimeout(() => {
          setShowThinking(false)
        }, 1000)
      }
    }
  }

  const handleQuickClick = (prompt: string) => {
    setInput(prompt)
  }

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    setMessages([])
    setSessionId(generateId())
    setStreamingContent('')
    message.success('对话已清空')
  }

  const handleFileUpload = async (file: File) => {
    message.info(`正在上传文件: ${file.name}`)
    try {
      const response = await forggptApi.uploadFile(file)
      const messageText = response.data?.message || '上传成功'
      message.success(`文件 ${file.name} 上传成功: ${messageText}`)
      setInput(`请分析我刚刚上传的文件：${file.name}`)
    } catch (error: any) {
      message.error(`文件上传失败: ${error.message || '未知错误'}`)
    }
    return false
  }

  // 打开设置模态框
  const handleOpenSettings = () => {
    setIsSettingsModalOpen(true)
    refetchAiConfig()
  }

  // 保存AI配置
  const handleSaveSettings = async () => {
    try {
      const values = await settingsForm.validateFields()
      await aiConfigApi.updateConfig(values)
      message.success('AI配置保存成功')
      setIsSettingsModalOpen(false)
      refetchAiConfig()
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error(`保存配置失败: ${error.message || '未知错误'}`)
    }
  }

  // 计算统计数据
  const statsData = stats7d?.data || []
  const totalGmv7d = Array.isArray(statsData) 
    ? statsData.reduce((sum: number, item: any) => sum + (item.gmv || 0), 0)
    : (statsData?.total_gmv || 0)
  const totalOrders7d = Array.isArray(statsData)
    ? statsData.reduce((sum: number, item: any) => sum + (item.orders || 0), 0)
    : (statsData?.total_orders || 0)
  const totalProfit7d = Array.isArray(statsData)
    ? statsData.reduce((sum: number, item: any) => sum + (item.profit || 0), 0)
    : (statsData?.total_profit || 0)
  const refundRate7d = (stats7d?.data as any)?.refund_rate || 0

  const formatCurrency = (value: number) => {
    if (value >= 10000) {
      return `¥${(value / 10000).toFixed(1)}k`
    }
    return `¥${value.toFixed(0)}`
  }

  const formatNumber = (value: number) => {
    return value.toLocaleString('zh-CN')
  }

  const profitMargin = totalGmv7d > 0 ? ((totalProfit7d / totalGmv7d) * 100).toFixed(1) : '0'

  // 整体深色背景样式 - 单屏布局
  const pageStyle: React.CSSProperties = {
    height: '100vh',
    background: '#020617',
    color: '#e5e7eb',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  }

  return (
    <Layout style={pageStyle}>
      {/* 顶部栏 - 紧凑设计 */}
      <Header
        style={{
          background: '#020617',
          borderBottom: '1px solid #1e293b',
          padding: '8px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '56px',
          flexShrink: 0,
        }}
      >
        <Space align="center" size="small">
          <Avatar
            style={{
              background: 'linear-gradient(135deg, #22c55e 0%, #a3e635 100%)',
              color: '#022c22',
            }}
            size={32}
          >
            🐸
          </Avatar>
          <div>
            <Title level={5} style={{ margin: 0, color: '#e5e7eb', fontSize: 16, fontWeight: 600 }}>
              FrogGPT
            </Title>
            <Text style={{ fontSize: 11, color: '#64748b' }}>
              AI 分析助手
            </Text>
          </div>
        </Space>

        <Space size="small">
          <Select
            value={selectedShopId || undefined}
            onChange={(value) => setSelectedShopId(value || null)}
            placeholder="所有店铺"
            style={{ width: 100, background: '#0f172a' }}
            dropdownStyle={{ background: '#0f172a' }}
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
            style={{
              background: '#6366f1',
              borderColor: '#6366f1',
            }}
            onClick={() => {
              setInput('生成今日销售总结')
              handleSend()
            }}
          >
            今日报告
          </Button>
          <Button
            icon={<SettingOutlined />}
            size="small"
            style={{
              background: '#0f172a',
              borderColor: '#1e293b',
              color: '#cbd5e1',
            }}
            onClick={handleOpenSettings}
          />
        </Space>
      </Header>

      {/* 主体内容 - 单屏布局 */}
      <Content
        style={{
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          flex: 1,
          minHeight: 0,
        }}
      >
        <Row gutter={12} style={{ flex: 1, minHeight: 0, display: 'flex' }}>
          {/* 左侧：对话区域 */}
          <Col span={16} style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Card
              bordered={false}
              style={{
                background: '#0f172a',
                border: '1px solid #1e293b',
                borderRadius: 12,
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0,
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              }}
              bodyStyle={{ padding: 12, display: 'flex', flexDirection: 'column', minHeight: 0, height: '100%' }}
            >
              {/* 快捷问题 - 紧凑设计 */}
              {messages.length === 0 && !loading && !isStreaming && (
                <Space wrap size={8} style={{ marginBottom: 12 }}>
                  {quickPrompts.map((q) => (
                    <Button
                      key={q}
                      size="small"
                      style={{
                        borderRadius: 6,
                        background: '#020617',
                        borderColor: '#334155',
                        color: '#cbd5e1',
                        fontSize: 11,
                        height: 24,
                        padding: '0 10px',
                      }}
                      onClick={() => handleQuickClick(q)}
                    >
                      {q}
                    </Button>
                  ))}
                </Space>
              )}

              {/* 消息列表 - 可滚动区域 */}
              <div
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  overflowX: 'hidden',
                  paddingRight: 8,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
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
                      color: '#94a3b8',
                    }}
                  >
                    <div
                      style={{
                        marginBottom: 16,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 64,
                        height: 64,
                        borderRadius: 16,
                        background: '#0f172a',
                        fontSize: 32,
                      }}
                    >
                      🐸
                    </div>
                    <div style={{ marginBottom: 4, fontSize: 18, fontWeight: 600, color: '#e5e7eb' }}>
                      你好，我是 FrogGPT
                    </div>
                    <div style={{ marginBottom: 16, maxWidth: 448, fontSize: 12, lineHeight: 1.6 }}>
                      我可以帮你分析运营数据，提供经营建议，也可以处理你上传的表格和文档。
                      从一个问题开始，或选择下方的快捷问题试试：
                    </div>
                    <Space wrap>
                      {quickPrompts.map((q) => (
                        <Button
                          key={q}
                          size="small"
                          style={{
                            borderRadius: 999,
                            background: '#0f172a',
                            borderColor: '#1e293b',
                            color: '#cbd5f5',
                            fontSize: 12,
                          }}
                          onClick={() => handleQuickClick(q)}
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
                    {isStreaming && (streamingContent || thinkingContent) && (
                      <div>
                        {/* 思考过程 */}
                        {showThinking && thinkingContent && (
                          <div
                            style={{
                              marginBottom: 12,
                              padding: '12px 16px',
                              background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                              border: '1px solid #334155',
                              borderRadius: 12,
                              fontSize: 12,
                              color: '#cbd5e1',
                              lineHeight: 1.6,
                              boxShadow: '0 2px 8px rgba(99, 102, 241, 0.1)',
                            }}
                          >
                            <div
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                marginBottom: 8,
                                paddingBottom: 8,
                                borderBottom: '1px solid #334155',
                              }}
                            >
                              <span style={{ color: '#818cf8', fontWeight: 600, fontSize: 13 }}>
                                💭 AI 正在思考...
                              </span>
                              <Button
                                type="text"
                                size="small"
                                style={{
                                  color: '#94a3b8',
                                  fontSize: 11,
                                  padding: '0 4px',
                                  height: 'auto',
                                }}
                                onClick={() => setShowThinking(false)}
                              >
                                收起
                              </Button>
                            </div>
                            <div
                              style={{
                                maxHeight: 300,
                                overflowY: 'auto',
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
                                color: '#a5b4fc',
                                fontSize: 11,
                              }}
                            >
                              {thinkingContent}
                            </div>
                          </div>
                        )}
                        {/* 流式内容 */}
                        {streamingContent && (
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
                      </div>
                    )}
                    {loading && !isStreaming && (
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                        <Avatar
                          size={28}
                          style={{
                            background: '#22c55e',
                            color: '#022c22',
                          }}
                          icon={<RobotOutlined />}
                        />
                        <div style={{ padding: '8px 12px' }}>
                          <Spin size="small" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>
            </Card>
          </Col>

          {/* 右侧：上下文 & 模板 & 文件 */}
          <Col span={8} style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                height: '100%',
                overflowY: 'auto',
                overflowX: 'hidden',
                paddingRight: 4,
              }}
            >
              {/* 当前数据概览 */}
              <Card
                size="small"
                title={<Text style={{ fontSize: 11, color: '#e5e7eb', fontWeight: 600 }}>数据概览</Text>}
                style={{
                  background: '#0f172a',
                  border: '1px solid #1e293b',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                }}
                headStyle={{
                  background: '#020617',
                  borderBottom: '1px solid #1e293b',
                  padding: '8px 12px',
                  minHeight: 36,
                }}
                bodyStyle={{ padding: 10 }}
              >
                <Row gutter={8}>
                  <Col span={12}>
                    <MetricBlock
                      label="最近 7 天 GMV"
                      value={formatCurrency(totalGmv7d)}
                      hint="+12.3%"
                    />
                  </Col>
                  <Col span={12}>
                    <MetricBlock
                      label="最近 7 天订单数"
                      value={`${formatNumber(totalOrders7d)} 单`}
                      hint="+6.2%"
                    />
                  </Col>
                  <Col span={12} style={{ marginTop: 8 }}>
                    <MetricBlock
                      label="最近 7 天利润"
                      value={formatCurrency(totalProfit7d)}
                      hint={`毛利率 ${profitMargin}%`}
                    />
                  </Col>
                  <Col span={12} style={{ marginTop: 8 }}>
                    <MetricBlock
                      label="退款率"
                      value={`${(refundRate7d * 100).toFixed(1)}%`}
                      hint="健康"
                    />
                  </Col>
                </Row>
              </Card>

              {/* 快捷分析 */}
              <Card
                size="small"
                title={<Text style={{ fontSize: 11, color: '#e5e7eb', fontWeight: 600 }}>快捷分析</Text>}
                style={{
                  background: '#0f172a',
                  border: '1px solid #1e293b',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                }}
                headStyle={{
                  background: '#020617',
                  borderBottom: '1px solid #1e293b',
                  padding: '8px 12px',
                  minHeight: 36,
                }}
                bodyStyle={{ padding: 8 }}
              >
                <List
                  size="small"
                  dataSource={[
                    '今日销售概览',
                    '近 7 天 GMV 变化原因',
                    '爆款 & 亏损 SKU 分析',
                    '退款异常排查',
                    '库存预警（未来 7 天）',
                  ]}
                  renderItem={(item) => (
                    <List.Item
                      style={{
                        paddingInline: 8,
                        background: '#020617',
                        marginBottom: 4,
                        borderRadius: 8,
                        border: '1px solid #1e293b',
                      }}
                      actions={[
                        <Button
                          key="ask"
                          size="small"
                          type="link"
                          style={{ fontSize: 10, paddingInline: 4 }}
                          onClick={() => {
                            setInput(item)
                            handleSend()
                          }}
                        >
                          一键询问
                        </Button>,
                      ]}
                    >
                      <Text style={{ fontSize: 12, color: '#e5e7eb' }}>{item}</Text>
                    </List.Item>
                  )}
                />
              </Card>

              {/* 文件与文档 */}
              <Card
                size="small"
                title={<Text style={{ fontSize: 11, color: '#e5e7eb', fontWeight: 600 }}>文件与文档</Text>}
                style={{
                  background: '#0f172a',
                  border: '1px solid #1e293b',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                }}
                headStyle={{
                  background: '#020617',
                  borderBottom: '1px solid #1e293b',
                  padding: '8px 12px',
                  minHeight: 36,
                }}
                bodyStyle={{ padding: 10 }}
              >
                <Upload
                  beforeUpload={handleFileUpload}
                  showUploadList={false}
                  accept=".xlsx,.xls,.csv,.json,.txt,.md"
                >
                  <Button
                    block
                    icon={<UploadOutlined />}
                    style={{
                      marginBottom: 8,
                      background: '#020617',
                      borderColor: '#334155',
                      color: '#e5e7eb',
                    }}
                  >
                    上传表格 / 文档分析
                  </Button>
                </Upload>

                <Space direction="vertical" style={{ width: '100%' }} size={8}>
                  <FileItem name="订单_10-11月.xlsx" desc="已解析 · 3,240 行" />
                  <FileItem name="供应商报价_2025Q1.xlsx" desc="待分析 · 24 条报价" />
                </Space>
              </Card>
            </div>
          </Col>
        </Row>
      </Content>

      {/* 底部输入栏 - 固定在底部 */}
      <Footer
        style={{
          background: '#020617',
          borderTop: '1px solid #1e293b',
          padding: '8px 16px 12px',
          flexShrink: 0,
        }}
      >
        <div style={{ marginBottom: 8, fontSize: 11, color: '#64748b' }}>
          <Space>
            <Upload
              beforeUpload={handleFileUpload}
              showUploadList={false}
              accept=".xlsx,.xls,.csv,.json,.txt,.md"
            >
              <Button
                size="small"
                icon={<UploadOutlined />}
                style={{
                  background: '#020617',
                  borderColor: '#334155',
                  color: '#e5e7eb',
                }}
              >
                上传文件
              </Button>
            </Upload>
            <Button
              size="small"
              icon={<DeleteOutlined />}
              style={{
                background: '#020617',
                borderColor: '#334155',
                color: '#e5e7eb',
              }}
              onClick={handleClear}
            >
              清空对话
            </Button>
            <span style={{ marginLeft: 'auto' }}>
              提示：Enter 发送，Shift+Enter 换行
            </span>
          </Space>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <TextArea
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题，例如：最近 7 天 GMV 为什么下降？"
            disabled={loading}
            style={{
              flex: 1,
              background: '#020617',
              borderColor: '#334155',
              color: '#e5e7eb',
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!input.trim() || loading}
            style={{
              alignSelf: 'flex-end',
              background: '#6366f1',
              borderColor: '#6366f1',
            }}
          >
            发送
          </Button>
        </div>
      </Footer>

      {/* AI配置设置模态框 */}
      <Modal
        title="AI模型配置"
        open={isSettingsModalOpen}
        onOk={handleSaveSettings}
        onCancel={() => setIsSettingsModalOpen(false)}
        width={800}
        okText="保存"
        cancelText="取消"
        style={{ top: 20 }}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        <Form
          form={settingsForm}
          layout="vertical"
          initialValues={{
            provider: 'deepseek',
            deepseek_base_url: 'https://api.deepseek.com',
            deepseek_model: 'deepseek-chat',
            openai_base_url: 'https://api.openai.com/v1',
            openai_model: 'gpt-4o',
            timeout_seconds: 30,
            cache_enabled: true,
            cache_ttl_days: 30,
            daily_limit: 1000,
          }}
        >
          <Form.Item
            label="AI服务提供商"
            name="provider"
            rules={[{ required: true, message: '请选择AI服务提供商' }]}
          >
            <Select>
              <Select.Option value="deepseek">DeepSeek</Select.Option>
              <Select.Option value="openai">OpenAI</Select.Option>
            </Select>
          </Form.Item>

          <Tabs
            items={[
              {
                key: 'deepseek',
                label: 'DeepSeek配置',
                children: (
                  <>
                    <Form.Item
                      label="API Key"
                      name="deepseek_api_key"
                      rules={[{ required: true, message: '请输入DeepSeek API Key' }]}
                      extra="从 DeepSeek 官网获取 API Key"
                    >
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                    <Form.Item
                      label="Base URL"
                      name="deepseek_base_url"
                      rules={[{ required: true, message: '请输入Base URL' }]}
                    >
                      <Input placeholder="https://api.deepseek.com" />
                    </Form.Item>
                    <Form.Item
                      label="模型名称"
                      name="deepseek_model"
                      rules={[{ required: true, message: '请输入模型名称' }]}
                      extra="例如: deepseek-chat, deepseek-coder"
                    >
                      <Input placeholder="deepseek-chat" />
                    </Form.Item>
                  </>
                ),
              },
              {
                key: 'openai',
                label: 'OpenAI配置',
                children: (
                  <>
                    <Form.Item
                      label="API Key"
                      name="openai_api_key"
                      extra="从 OpenAI 官网获取 API Key"
                    >
                      <Input.Password placeholder="sk-..." />
                    </Form.Item>
                    <Form.Item
                      label="Base URL"
                      name="openai_base_url"
                      rules={[{ required: true, message: '请输入Base URL' }]}
                    >
                      <Input placeholder="https://api.openai.com/v1" />
                    </Form.Item>
                    <Form.Item
                      label="模型名称"
                      name="openai_model"
                      rules={[{ required: true, message: '请输入模型名称' }]}
                      extra="例如: gpt-4o, gpt-4-turbo, gpt-3.5-turbo"
                    >
                      <Input placeholder="gpt-4o" />
                    </Form.Item>
                  </>
                ),
              },
            ]}
          />

          <Form.Item label="通用配置">
            <Form.Item
              label="API调用超时时间（秒）"
              name="timeout_seconds"
              rules={[{ required: true, message: '请输入超时时间' }]}
              style={{ marginBottom: 16 }}
            >
              <InputNumber min={10} max={300} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              label="启用结果缓存"
              name="cache_enabled"
              valuePropName="checked"
              style={{ marginBottom: 16 }}
            >
              <Switch />
            </Form.Item>
            <Form.Item
              label="缓存过期天数"
              name="cache_ttl_days"
              rules={[{ required: true, message: '请输入缓存过期天数' }]}
              style={{ marginBottom: 16 }}
            >
              <InputNumber min={1} max={365} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              label="每日调用次数限制"
              name="daily_limit"
              rules={[{ required: true, message: '请输入每日调用次数限制' }]}
            >
              <InputNumber min={1} max={100000} style={{ width: '100%' }} />
            </Form.Item>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  )
}

// 一些复用的小组件 & 样式

const tagStyle: React.CSSProperties = {
  background: '#020617',
  borderColor: '#1e293b',
  color: '#cbd5f5',
  fontSize: 11,
}

const cardDarkStyle: React.CSSProperties = {
  background: '#020617',
  borderColor: '#1e293b',
}

const cardHeadDarkStyle: React.CSSProperties = {
  background: '#020617',
  borderBottom: '1px solid #1e293b',
  borderRadius: 8,
}

const MetricBlock: React.FC<{
  label: string
  value: string
  hint?: string
}> = ({ label, value, hint }) => (
  <div
    style={{
      background: '#0f172a',
      borderRadius: 8,
      padding: '6px 8px',
    }}
  >
    <div style={{ fontSize: 10, color: '#94a3b8' }}>{label}</div>
    <div style={{ fontSize: 13, color: '#e5e7eb', fontWeight: 600 }}>{value}</div>
    {hint && (
      <div style={{ fontSize: 10, color: '#4ade80', marginTop: 2 }}>{hint}</div>
    )}
  </div>
)

const FileItem: React.FC<{ name: string; desc: string }> = ({ name, desc }) => (
  <div
    style={{
      background: '#020617',
      borderRadius: 8,
      padding: '6px 8px',
      border: '1px solid #1e293b',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}
  >
    <div>
      <div style={{ fontSize: 12, color: '#e5e7eb' }}>{name}</div>
      <div style={{ fontSize: 10, color: '#64748b' }}>{desc}</div>
    </div>
    <Button type="link" size="small" style={{ fontSize: 10, paddingInline: 4 }}>
      分析
    </Button>
  </div>
)

const ChatBubble: React.FC<{ message: Message; isStreaming?: boolean }> = ({
  message,
  isStreaming,
}) => {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div
          style={{
            maxWidth: '70%',
            background: '#6366f1',
            color: '#f9fafb',
            borderRadius: 16,
            padding: '8px 12px',
            fontSize: 13,
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.content}
          <div
            style={{
              textAlign: 'right',
              fontSize: 10,
              marginTop: 2,
              opacity: 0.8,
            }}
          >
            {message.createdAt}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
      <Avatar
        size={28}
        style={{
          background: '#22c55e',
          color: '#022c22',
        }}
        icon={<RobotOutlined />}
      />
      <div
        style={{
          maxWidth: '72%',
          background: '#0f172a',
          borderRadius: 16,
          padding: '8px 12px',
          fontSize: 13,
          whiteSpace: 'pre-wrap',
        }}
      >
        {message.title && (
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#4ade80',
              marginBottom: 4,
            }}
          >
            {message.title}
          </div>
        )}
        <div>
          {message.content}
          {isStreaming && (
            <span
              style={{
                display: 'inline-block',
                width: 8,
                height: 16,
                background: 'currentColor',
                animation: 'blink 1s infinite',
                marginLeft: 4,
                verticalAlign: 'middle',
              }}
            />
          )}
        </div>
        <div
          style={{
            fontSize: 10,
            color: '#64748b',
            marginTop: 4,
          }}
        >
          FrogGPT · {message.createdAt}
        </div>
      </div>
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  )
}
