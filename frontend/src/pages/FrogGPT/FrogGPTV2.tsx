/**
 * FrogGPT 2.0 主页面
 * 使用 Ant Design X 组件重构
 */
import React, { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Select,
  Switch,
  Button,
  Space,
  Typography,
  Tag,
  message,
  Modal,
  Input,
  AutoComplete,
  Tooltip,
  Row,
  Col,
  Divider,
  Segmented,
} from 'antd'
import {
  SaveOutlined,
  ReloadOutlined,
  RobotOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { Welcome } from '@ant-design/x'
import { frogGptApi, shopApi, statisticsApi, analyticsApi } from '@/services/api'
import AiChatPanelV2 from './components/AiChatPanelV2'
import DecisionPanel from './components/DecisionPanel'
import MetricOverview from './MetricOverview'
import TrendsCharts from './components/TrendsCharts'
import type { DecisionData, MetricData, TrendData, SkuRankingItem } from './types'
import './frog-gpt.css'

const { Text } = Typography

const FrogGPTV2: React.FC = () => {
  // 状态管理
  const [selectedModel, setSelectedModel] = useState<string>('auto')
  const [temperature, setTemperature] = useState(0.7)
  const [includeSystemData, setIncludeSystemData] = useState(true)
  const [dataSummaryDays, setDataSummaryDays] = useState(7)
  const [selectedShopId, setSelectedShopId] = useState<number | undefined>()
  const [decisionData, setDecisionData] = useState<DecisionData | null>(null)
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [modelSearchValue, setModelSearchValue] = useState<string | null>(null)
  const [externalMessage, setExternalMessage] = useState<string | null>(null)
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    openrouter: '',
    openai: '',
    anthropic: '',
    gemini: '',
  })

  // 获取可用模型列表
  const { data: modelsData } = useQuery({
    queryKey: ['frog-gpt-models'],
    queryFn: frogGptApi.getModels,
    staleTime: 5 * 60 * 1000,
  })

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取数据摘要（用于指标展示）
  const { data: dataSummary } = useQuery({
    queryKey: ['frog-gpt-data-summary', dataSummaryDays],
    queryFn: () => frogGptApi.getDataSummary(dataSummaryDays),
    enabled: includeSystemData,
  })

  // 获取每日趋势数据
  const { data: dailyStats } = useQuery({
    queryKey: ['daily-statistics', dataSummaryDays, selectedShopId],
    queryFn: () => {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - dataSummaryDays)
      
      return statisticsApi.getDaily({
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        shop_ids: selectedShopId ? [selectedShopId] : undefined,
      })
    },
    enabled: includeSystemData,
  })

  // 获取SKU销售排行
  const { data: skuRankingData } = useQuery({
    queryKey: ['sku-sales-ranking', dataSummaryDays, selectedShopId],
    queryFn: () => {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - dataSummaryDays)
      
      return analyticsApi.getSkuSalesRanking({
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        shop_ids: selectedShopId ? [selectedShopId] : undefined,
        limit: 10,
      })
    },
    enabled: includeSystemData,
  })

  // 获取OpenRouter API配置
  const { data: apiConfig } = useQuery({
    queryKey: ['frog-gpt-api-config'],
    queryFn: frogGptApi.getApiConfig,
  })

  // 处理模型选项
  const modelOptions = useMemo(() => {
    const options: any[] = [
      {
        value: 'auto',
        label: (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag color="blue" style={{ margin: 0 }}>AUTO</Tag>
            <span>自动选择最佳模型（OpenRouter智能路由）</span>
          </div>
        ),
        searchText: 'auto 自动 智能路由 openrouter',
      },
    ]

    if (modelsData?.models) {
      modelsData.models.forEach((model: any) => {
        const modelName = model.name || model.id || ''
        const modelId = model.id || ''
        const description = model.description || ''
        const truncatedDescription = description.length > 80 
          ? description.substring(0, 80) + '...' 
          : description
        
        let priceText = ''
        if (model.pricing?.prompt) {
          const pricePerM = model.pricing.prompt * 1000000
          priceText = pricePerM < 1 
            ? `$${(pricePerM * 1000).toFixed(2)}/1M`
            : `$${pricePerM.toFixed(2)}/1M`
        }
        
        const searchKeywords = [
          modelName, modelId, description,
          modelId.split('/').pop(),
          modelId.split('/')[0],
        ].filter(Boolean).join(' ').toLowerCase()
        
        options.push({
          value: model.id,
          label: (
            <Tooltip 
              title={description ? (
                <div style={{ maxWidth: '400px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>{modelName}</div>
                  <div>{description}</div>
                  {model.context_length && (
                    <div style={{ marginTop: '4px', fontSize: '12px', color: '#94a3b8' }}>
                      上下文长度: {model.context_length.toLocaleString()} tokens
                    </div>
                  )}
                </div>
              ) : modelName}
              placement="right"
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', cursor: 'pointer' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 500, color: '#e2e8f0' }}>{modelName}</div>
                  {truncatedDescription && (
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                      {truncatedDescription}
                    </div>
                  )}
                </div>
                {priceText && (
                  <Tag color="green" style={{ margin: 0, fontSize: '10px', marginLeft: '8px', flexShrink: 0 }}>
                    {priceText}
                  </Tag>
                )}
              </div>
            </Tooltip>
          ),
          model: model,
          searchText: searchKeywords,
        })
      })
    }

    return options
  }, [modelsData])

  const filteredModelOptions = useMemo(() => {
    if (modelSearchValue === null || !modelSearchValue) {
      return modelOptions
    }
    const searchText = modelSearchValue.toLowerCase().trim()
    if (!searchText) {
      return modelOptions
    }
    const searchWords = searchText.split(/\s+/).filter(word => word.length > 0)
    return modelOptions.filter(option => 
      searchWords.every(word => option?.searchText?.includes(word) || false)
    )
  }, [modelOptions, modelSearchValue])

  const selectedModelDisplay = useMemo(() => {
    if (!selectedModel) return ''
    if (selectedModel === 'auto') return 'AUTO - 自动选择最佳模型'
    const option = modelOptions.find(opt => opt.value === selectedModel)
    if (option?.model) {
      return option.model.name || option.model.id || selectedModel
    }
    return selectedModel
  }, [selectedModel, modelOptions])

  // 计算指标数据
  const metrics: MetricData[] = useMemo(() => {
    if (!dataSummary) return []
    
    return [
      {
        label: `${dataSummaryDays}日 GMV`,
        value: `¥${((dataSummary.overview?.total_gmv || 0) / 1000).toFixed(1)}k`,
        trend: 'up',
        trendValue: '+12.3%',
      },
      {
        label: `${dataSummaryDays}日订单数`,
        value: (dataSummary.overview?.total_orders || 0).toLocaleString(),
        trend: 'up',
        trendValue: '+8.5%',
      },
      {
        label: '退款率',
        value: '2.3%',
        trend: 'down',
        trendValue: '-0.5%',
      },
      {
        label: '平均客单价',
        value: `¥${((dataSummary.overview?.total_gmv || 0) / (dataSummary.overview?.total_orders || 1)).toFixed(2)}`,
      },
    ]
  }, [dataSummary, dataSummaryDays])

  // 处理趋势数据（从API获取）
  const trendData: TrendData[] = useMemo(() => {
    if (!dailyStats || !Array.isArray(dailyStats)) {
      return []
    }
    
    return dailyStats.map((item: any) => ({
      date: item.date || item.period || '',
      gmv: item.gmv || item.total_gmv || 0,
      orders: item.orders || item.order_count || 0,
      profit: item.profit || item.total_profit || 0,
      refundRate: item.refund_rate || 0,
    })).sort((a, b) => a.date.localeCompare(b.date))
  }, [dailyStats])

  // 处理SKU排行数据（从API获取）
  const skuRanking: SkuRankingItem[] = useMemo(() => {
    if (!skuRankingData || !Array.isArray(skuRankingData)) {
      return []
    }
    
    return skuRankingData.map((item: any, index: number) => ({
      sku: item.sku || item.product_sku || `SKU-${index + 1}`,
      productName: item.product_name || item.name || '未知商品',
      quantity: item.quantity || item.sold_quantity || 0,
      orders: item.orders || item.order_count || 0,
      gmv: item.gmv || item.total_gmv || item.sales_amount || 0,
      profit: item.profit || item.total_profit || 0,
      refundRate: item.refund_rate || 0,
      rank: index + 1,
    })).slice(0, 10)
  }, [skuRankingData])

  // 当前店铺名称
  const currentShopName = useMemo(() => {
    if (!selectedShopId) return '全部店铺'
    const shop = shops?.find(s => s.id === selectedShopId)
    return shop?.name || '未知店铺'
  }, [selectedShopId, shops])

  // 处理决策数据更新
  const handleDecisionParsed = (data: DecisionData | null) => {
    setDecisionData(data)
  }

  // 处理快捷问题点击
  const handleQuickPromptClick = (prompt: string) => {
    // 直接发送到聊天面板
    setExternalMessage(prompt)
  }

  // 处理外部消息发送完成
  const handleExternalMessageSent = () => {
    setExternalMessage(null)
  }

  // 加载保存的配置（包括模型选择）
  useEffect(() => {
    const savedConfig = localStorage.getItem('frog-gpt-config')
    const savedKeys = localStorage.getItem('frog-gpt-api-keys')
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig)
        if (config.model) {
          setSelectedModel(config.model)
          setModelSearchValue(null)
        } else {
          // 如果没有保存的模型，默认使用 auto
          setSelectedModel('auto')
        }
        if (config.temperature !== undefined) setTemperature(config.temperature)
        if (config.includeSystemData !== undefined) setIncludeSystemData(config.includeSystemData)
        if (config.dataSummaryDays) setDataSummaryDays(config.dataSummaryDays)
        if (config.shopId) setSelectedShopId(config.shopId)
      } catch (error) {
        console.error('加载配置失败:', error)
        // 如果加载失败，使用默认值
        setSelectedModel('auto')
      }
    } else {
      // 如果没有保存的配置，使用默认值
      setSelectedModel('auto')
    }
    if (savedKeys) {
      try {
        const parsed = JSON.parse(savedKeys)
        setApiKeys({
          openrouter: parsed.openrouter || '',
          openai: parsed.openai || '',
          anthropic: parsed.anthropic || '',
          gemini: parsed.gemini || '',
        })
      } catch (error) {
        console.error('加载API Key失败:', error)
      }
    }
  }, [])

  // 保存配置（包括模型选择）
  const handleSaveConfig = () => {
    const config = {
      model: selectedModel,
      temperature,
      includeSystemData,
      dataSummaryDays,
      shopId: selectedShopId,
    }
    localStorage.setItem('frog-gpt-config', JSON.stringify(config))
    localStorage.setItem('frog-gpt-api-keys', JSON.stringify(apiKeys))
    message.success('配置已保存')
  }

  // 重置默认配置
  const handleResetConfig = () => {
    setSelectedModel('auto')
    setTemperature(0.7)
    setIncludeSystemData(true)
    setDataSummaryDays(7)
    setSelectedShopId(undefined)
    setModelSearchValue(null)
    setApiKeys({
      openrouter: '',
      openai: '',
      anthropic: '',
      gemini: '',
    })
    localStorage.removeItem('frog-gpt-config')
    localStorage.removeItem('frog-gpt-api-keys')
    message.success('已重置为默认配置')
  }

  // 打开设置弹窗
  const handleOpenConfig = () => {
    setConfigModalVisible(true)
    // 初始化模型搜索值
    if (selectedModel) {
      setModelSearchValue(null)
    }
  }

  return (
    <div
      className="frog-gpt-page"
      style={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        padding: '18px',
        gap: '14px',
      }}
    >
      {/* 顶部英雄区 */}
      <Card
        className="frog-gpt-hero-card frog-gpt-floating"
        styles={{ body: { padding: '18px 20px', position: 'relative' } }}
        variant="borderless"
      >
        <Row gutter={[16, 12]} align="middle" wrap>
          <Col flex="auto">
            <Welcome
              icon={<RobotOutlined style={{ color: '#60a5fa', fontSize: '22px' }} />}
              title={
                <Space size="middle">
                  <Text style={{ color: '#e2e8f0', fontSize: '18px', fontWeight: 600 }}>
                    FrogGPT 2.0 · 智能运营驾驶舱
                  </Text>
                  <Tag color="blue" className="frog-gpt-tag" style={{ margin: 0 }}>
                    OpenRouter Ready
                  </Tag>
                </Space>
              }
              description={
                <Space size="small" wrap>
                  <Text className="frog-gpt-soft-text">更灵动的动画、更友好的互动体验</Text>
                  <Divider type="vertical" style={{ borderColor: '#1f2937' }} />
                  <Text className="frog-gpt-soft-text">左侧数据洞察 · 右侧实时对话</Text>
                </Space>
              }
              extra={
                <Space size="small" wrap>
                  <span className="frog-gpt-badge success">✅ 已接入 OpenRouter API Key</span>
                  <span className="frog-gpt-badge warn">📅 数据窗口 {dataSummaryDays} 天</span>
                </Space>
              }
            />
            <Space wrap size="small" style={{ marginTop: 12 }}>
              <span className="frog-gpt-badge">
                🤖 模型: {selectedModelDisplay || selectedModel || 'AUTO'}
              </span>
              <span className="frog-gpt-badge">
                🎛️ 温度: {temperature}
              </span>
              <span className="frog-gpt-badge success">
                🛰️ 数据源: {includeSystemData ? '包含系统数据' : '对话模式'}
              </span>
            </Space>
          </Col>
          <Col xs={24} md="auto">
            <Space direction="vertical" size="small" align="end">
              <Space wrap>
                <Select
                  allowClear
                  value={selectedShopId}
                  onChange={(value) => setSelectedShopId(value ?? undefined)}
                  placeholder="全部店铺"
                  style={{ minWidth: 200 }}
                  options={(shops || []).map((shop: any) => ({
                    label: shop.name,
                    value: shop.id,
                  }))}
                />
                <Segmented
                  size="middle"
                  value={dataSummaryDays}
                  onChange={(value) => setDataSummaryDays(value as number)}
                  options={[
                    { label: '近3天', value: 3 },
                    { label: '近7天', value: 7 },
                    { label: '近14天', value: 14 },
                    { label: '30天', value: 30 },
                  ]}
                />
              </Space>
              <Space wrap align="center">
                <Segmented
                  size="middle"
                  value={temperature}
                  onChange={(value) => setTemperature(Number(value))}
                  options={[
                    { label: '稳定', value: 0.3 },
                    { label: '均衡', value: 0.7 },
                    { label: '创意', value: 0.9 },
                  ]}
                />
                <Space size={4} align="center">
                  <Text className="frog-gpt-soft-text">数据</Text>
                  <Switch
                    size="small"
                    checked={includeSystemData}
                    onChange={setIncludeSystemData}
                  />
                </Space>
                <Button
                  type="text"
                  icon={<SettingOutlined />}
                  onClick={handleOpenConfig}
                  style={{ color: '#93c5fd' }}
                >
                  高级设置
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSaveConfig}
                >
                  保存偏好
                </Button>
                <Button
                  ghost
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={handleResetConfig}
                >
                  重置
                </Button>
              </Space>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主内容区：左右分栏 */}
      <div style={{ display: 'flex', gap: '14px', flex: 1, overflow: 'hidden' }}>
        {/* 左侧：数据 & 决策视图（42%） */}
        <div style={{ width: '42%', display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'auto', paddingBottom: 8 }}>
          {/* AI 结构化决策区置顶 */}
          <DecisionPanel decisionData={decisionData} />

          {/* 运营指标速览 */}
          {metrics.length > 0 && <MetricOverview metrics={metrics} />}

          {/* 运营图表区 */}
          <TrendsCharts trendData={trendData} skuRanking={skuRanking} />
        </div>

        {/* 右侧：AI Chat 面板（58%） */}
        <div style={{ width: '58%', height: '100%' }}>
          <AiChatPanelV2
            shopId={selectedShopId?.toString()}
            shopName={currentShopName}
            model={selectedModel}
            temperature={temperature}
            includeSystemData={includeSystemData}
            dataSummaryDays={dataSummaryDays}
            onDecisionParsed={handleDecisionParsed}
            externalMessage={externalMessage}
            onExternalMessageSent={handleExternalMessageSent}
          />
        </div>
      </div>

      {/* 设置弹窗 */}
      <Modal
        title={
          <Space>
            <SettingOutlined style={{ color: '#60a5fa' }} />
            <span>FrogGPT 配置</span>
          </Space>
        }
        open={configModalVisible}
        onCancel={() => {
          setConfigModalVisible(false)
          setModelSearchValue(null)
        }}
        onOk={() => {
          handleSaveConfig()
          setConfigModalVisible(false)
        }}
        okText="保存"
        cancelText="取消"
        width={700}
        styles={{
          body: { background: '#0f172a', padding: '24px' },
          header: { background: '#1e293b', borderBottom: '1px solid #334155', color: '#e2e8f0' },
          footer: { background: '#1e293b', borderTop: '1px solid #334155' },
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 模型选择 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
              选择 AI 模型
            </Text>
            <AutoComplete
              value={modelSearchValue !== null ? modelSearchValue : (selectedModelDisplay || selectedModel || '')}
              onChange={(value) => {
                // 允许用户输入任何内容，包括空字符串
                setModelSearchValue(value)
              }}
              onSearch={(value) => {
                // 搜索时更新搜索值，允许空字符串以便用户清空
                setModelSearchValue(value)
              }}
              options={filteredModelOptions}
              style={{ width: '100%' }}
              placeholder="选择或搜索AI模型（支持AUTO自动选择）"
              onSelect={(value) => {
                // 选择模型后，更新选中值并清空搜索状态
                setSelectedModel(value)
                setModelSearchValue(null)
              }}
              onFocus={() => {
                // 获得焦点时，如果当前显示的是选中的模型，清空以便用户输入
                if (modelSearchValue === null && selectedModel) {
                  setModelSearchValue('')
                }
              }}
              onBlur={() => {
                // 失去焦点时，如果搜索值为空或不匹配，恢复显示选中的模型
                if (modelSearchValue === '') {
                  // 如果用户清空了内容，恢复显示已选模型
                  setModelSearchValue(null)
                } else if (modelSearchValue && modelSearchValue !== selectedModel) {
                  // 如果输入了内容但不匹配任何模型，检查是否是有效的模型ID
                  const match = modelOptions.find(opt => 
                    opt.value === modelSearchValue || 
                    opt.searchText?.includes(modelSearchValue.toLowerCase())
                  )
                  if (!match) {
                    // 没有匹配，恢复显示已选模型
                    setModelSearchValue(null)
                  } else {
                    // 有匹配，选择该模型
                    setSelectedModel(match.value)
                    setModelSearchValue(null)
                  }
                }
              }}
              notFoundContent="未找到匹配的模型"
              styles={{
                popup: {
                  background: '#1e293b',
                  borderColor: '#334155',
                  maxHeight: '400px',
                }
              }}
              allowClear
              onClear={() => {
                setSelectedModel('auto')
                setModelSearchValue(null)
              }}
            />
            <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px', display: 'block' }}>
              选择 AI 模型用于对话。AUTO 选项将自动选择最佳模型。
            </Text>
          </div>

          {/* 温度设置 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
              温度参数
            </Text>
            <Select
              value={temperature}
              onChange={setTemperature}
              style={{ width: '100%' }}
              options={[
                { label: '0.1 - 更确定、保守', value: 0.1 },
                { label: '0.3 - 较确定', value: 0.3 },
                { label: '0.5 - 平衡', value: 0.5 },
                { label: '0.7 - 推荐（平衡创造性和准确性）', value: 0.7 },
                { label: '0.9 - 更有创造性', value: 0.9 },
                { label: '1.0 - 高创造性', value: 1.0 },
              ]}
            />
            <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px', display: 'block' }}>
              控制 AI 输出的随机性和创造性。值越低越确定，值越高越有创造性。
            </Text>
          </div>

          {/* 数据设置 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
              数据设置
            </Text>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#e2e8f0' }}>包含系统数据</Text>
                <Switch
                  checked={includeSystemData}
                  onChange={setIncludeSystemData}
                  checkedChildren="是"
                  unCheckedChildren="否"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#e2e8f0' }}>数据天数</Text>
                <Select
                  value={dataSummaryDays}
                  onChange={setDataSummaryDays}
                  style={{ width: 150 }}
                  options={[
                    { label: '3天', value: 3 },
                    { label: '7天', value: 7 },
                    { label: '14天', value: 14 },
                    { label: '30天', value: 30 },
                  ]}
                />
              </div>
            </Space>
            <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px', display: 'block' }}>
              包含系统数据将在对话中包含运营数据摘要，帮助 AI 提供更准确的建议。
            </Text>
          </div>

          {/* 模型 API Key 配置 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
              模型 API Key 配置
            </Text>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Input
                value={apiKeys.openrouter}
                onChange={(e) => setApiKeys(prev => ({ ...prev, openrouter: e.target.value }))}
                placeholder="OpenRouter API Key（推荐）"
                allowClear
              />
              <Input
                value={apiKeys.openai}
                onChange={(e) => setApiKeys(prev => ({ ...prev, openai: e.target.value }))}
                placeholder="OpenAI API Key"
                allowClear
              />
              <Input
                value={apiKeys.anthropic}
                onChange={(e) => setApiKeys(prev => ({ ...prev, anthropic: e.target.value }))}
                placeholder="Anthropic/Claude API Key"
                allowClear
              />
              <Input
                value={apiKeys.gemini}
                onChange={(e) => setApiKeys(prev => ({ ...prev, gemini: e.target.value }))}
                placeholder="Google Gemini API Key"
                allowClear
              />
            </Space>
            <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px', display: 'block' }}>
              支持主流模型接入，优先使用 OpenRouter；如需切换模型，请在上方选择对应模型并保存。
            </Text>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default FrogGPTV2
