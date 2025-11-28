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
  Segmented,
  Radio,
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
  const [selectedShopId, setSelectedShopId] = useState<number | undefined>()
  const [decisionData, setDecisionData] = useState<DecisionData | null>(null)
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [modelSearchValue, setModelSearchValue] = useState<string | null>(null)
  const [externalMessage, setExternalMessage] = useState<string | null>(null)
  const [connectionType, setConnectionType] = useState<'openrouter' | 'direct'>('openrouter')
  const [directProvider, setDirectProvider] = useState<string>('openai')
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    openrouter: '',
    openai: '',
    anthropic: '',
    gemini: '',
  })

  // 获取可用模型列表（仅当使用 OpenRouter 时）
  const { data: modelsData } = useQuery({
    queryKey: ['frog-gpt-models', connectionType],
    queryFn: frogGptApi.getModels,
    enabled: connectionType === 'openrouter', // 只在选择 OpenRouter 时获取模型列表
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  })

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取数据摘要（用于指标展示）- 全部时间数据
  const { data: dataSummary } = useQuery({
    queryKey: ['frog-gpt-data-summary', selectedShopId],
    queryFn: () => frogGptApi.getDataSummary(undefined), // 不传days参数，获取全部数据
    enabled: includeSystemData,
  })

  // 获取每日趋势数据 - 全部时间数据
  const { data: dailyStats } = useQuery({
    queryKey: ['daily-statistics', selectedShopId],
    queryFn: () => {
      return statisticsApi.getDaily({
        shop_ids: selectedShopId ? [selectedShopId] : undefined,
        // 不传 start_date 和 end_date，获取全部数据
      })
    },
    enabled: includeSystemData,
  })

  // 获取SKU销售排行 - 全部时间数据
  const { data: skuRankingData } = useQuery({
    queryKey: ['sku-sales-ranking', selectedShopId],
    queryFn: () => {
      return analyticsApi.getSkuSalesRanking({
        shop_ids: selectedShopId ? [selectedShopId] : undefined,
        limit: 10,
        // 不传 start_date 和 end_date，获取全部数据
      })
    },
    enabled: includeSystemData,
  })

  // 验证 API Key 配置状态
  const [apiKeyStatus, setApiKeyStatus] = useState<{
    configured: boolean
    valid: boolean
    message: string
  }>({ configured: false, valid: false, message: '' })
  
  // 检查 API Key 配置状态
  useEffect(() => {
    const checkApiKeyStatus = async () => {
      try {
        const backendKeys = await frogGptApi.getAllProvidersApiKeys() as any
        const hasOpenRouterKey = backendKeys?.openrouter?.has_api_key || backendKeys?.openrouter?.api_key
        
        if (hasOpenRouterKey) {
          try {
            const verifyResult = await frogGptApi.verifyApiKey('openrouter') as any
            if (verifyResult?.valid) {
              setApiKeyStatus({
                configured: true,
                valid: true,
                message: `✅ API Key 已配置并验证成功${verifyResult.models_count ? `，可访问 ${verifyResult.models_count} 个模型` : ''}`
              })
            } else {
              setApiKeyStatus({
                configured: true,
                valid: false,
                message: `⚠️ API Key 已配置但验证失败: ${verifyResult?.message || '未知错误'}`
              })
            }
          } catch (error: any) {
            setApiKeyStatus({
              configured: true,
              valid: false,
              message: `⚠️ API Key 验证失败: ${error.response?.data?.detail || error.message || '未知错误'}`
            })
          }
        } else {
          setApiKeyStatus({
            configured: false,
            valid: false,
            message: '❌ 未配置 OpenRouter API Key，请在高级设置中配置'
          })
        }
      } catch (error) {
        console.error('检查 API Key 状态失败:', error)
        setApiKeyStatus({
          configured: false,
          valid: false,
          message: '无法检查 API Key 状态'
        })
      }
    }
    
    checkApiKeyStatus()
  }, [])

  // 处理模型选项（从 OpenRouter API 获取）
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

    // 从 OpenRouter API 获取的模型列表
    if (modelsData?.models && Array.isArray(modelsData.models)) {
      modelsData.models.forEach((model: any) => {
        const modelName = model.name || model.id || ''
        const modelId = model.id || ''
        const description = model.description || ''
        const truncatedDescription = description.length > 80 
          ? description.substring(0, 80) + '...' 
          : description
        
        // 格式化价格信息
        let priceText = ''
        if (model.pricing?.prompt) {
          const pricePerM = model.pricing.prompt * 1000000
          priceText = pricePerM < 1 
            ? `$${(pricePerM * 1000).toFixed(2)}/1M`
            : `$${pricePerM.toFixed(2)}/1M`
        }
        
        // 构建搜索关键词（支持模糊匹配）
        // 包括：模型名称、ID、描述、ID的各个部分（如 openai/gpt-4 可以匹配 "openai"、"gpt-4"、"gpt"、"4"）
        const idParts = modelId.split('/').filter(Boolean)
        const searchKeywords = [
          modelName,
          modelId,
          description,
          ...idParts, // 添加 ID 的各个部分
          ...idParts.flatMap((part: string) => part.split('-')), // 将 "gpt-4" 拆分为 ["gpt", "4"]
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
                  {model.pricing && (
                    <div style={{ marginTop: '4px', fontSize: '12px', color: '#94a3b8' }}>
                      价格: {priceText || '免费'}
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

  // 模糊匹配过滤模型选项
  const filteredModelOptions = useMemo(() => {
    if (modelSearchValue === null || !modelSearchValue) {
      return modelOptions
    }
    const searchText = modelSearchValue.toLowerCase().trim()
    if (!searchText) {
      return modelOptions
    }
    
    // 支持多关键词搜索，每个关键词都要匹配
    const searchWords = searchText.split(/\s+/).filter(word => word.length > 0)
    
    return modelOptions.filter(option => {
      if (!option?.searchText) return false
      // 所有搜索词都必须出现在 searchText 中
      return searchWords.every(word => option.searchText.includes(word))
    })
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
        label: `累计 GMV`,
        value: `¥${((dataSummary.overview?.total_gmv || 0) / 1000).toFixed(1)}k`,
        trend: 'up',
        trendValue: '+12.3%',
      },
      {
        label: `累计订单数`,
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
  }, [dataSummary])

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
    const shop = shops?.find((s: any) => s.id === selectedShopId)
    return shop?.name || '未知店铺'
  }, [selectedShopId, shops])

  // 处理决策数据更新
  const handleDecisionParsed = (data: DecisionData | null) => {
    setDecisionData(data)
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
        // 恢复连接类型和直接接入的供应商
        if (parsed.connectionType) {
          setConnectionType(parsed.connectionType)
        }
        if (parsed.directProvider) {
          setDirectProvider(parsed.directProvider)
        }
      } catch (error) {
        console.error('加载API Key失败:', error)
      }
    }
    
    // 从后端加载已保存的API Key（如果本地没有）
    const loadApiKeysFromBackend = async () => {
      try {
        const backendKeys = await frogGptApi.getAllProvidersApiKeys()
        setApiKeys(prev => ({
          openrouter: prev.openrouter || (backendKeys?.openrouter?.api_key || ''),
          openai: prev.openai || (backendKeys?.openai?.api_key || ''),
          anthropic: prev.anthropic || (backendKeys?.anthropic?.api_key || ''),
          gemini: prev.gemini || (backendKeys?.gemini?.api_key || ''),
        }))
        
        // 如果后端有 OpenRouter API Key，验证其有效性
        const openrouterKey = backendKeys?.openrouter?.api_key
        if (openrouterKey) {
          try {
            const verifyResult = await frogGptApi.verifyApiKey('openrouter')
            if (verifyResult?.valid) {
              console.log(`✅ API Key 验证成功！${verifyResult.models_count ? `可访问 ${verifyResult.models_count} 个模型` : ''}`)
            } else {
              console.warn(`⚠️ API Key 验证失败: ${verifyResult?.message || '未知错误'}`)
            }
          } catch (error) {
            console.error('验证 API Key 失败:', error)
          }
        }
      } catch (error) {
        console.error('从后端加载API Key失败:', error)
      }
    }
    loadApiKeysFromBackend()
  }, [])

  // 保存配置（包括模型选择）
  const handleSaveConfig = async () => {
    try {
      // 保存到本地存储
    const config = {
      model: selectedModel,
      temperature,
      includeSystemData,
      shopId: selectedShopId,
    }
    localStorage.setItem('frog-gpt-config', JSON.stringify(config))
      localStorage.setItem('frog-gpt-api-keys', JSON.stringify({
        ...apiKeys,
        connectionType,
        directProvider,
      }))
      
      // 保存API Key到后端数据库
      const keysToSave: any = {}
      if (connectionType === 'openrouter' && apiKeys.openrouter) {
        keysToSave.openrouter = apiKeys.openrouter
      } else if (connectionType === 'direct') {
        if (directProvider === 'openai' && apiKeys.openai) {
          keysToSave.openai = apiKeys.openai
        } else if (directProvider === 'anthropic' && apiKeys.anthropic) {
          keysToSave.anthropic = apiKeys.anthropic
        } else if (directProvider === 'gemini' && apiKeys.gemini) {
          keysToSave.gemini = apiKeys.gemini
        }
      }
      
      // 如果有API Key需要保存，调用后端API
      if (Object.keys(keysToSave).length > 0) {
        const result = await frogGptApi.updateAllProvidersApiKeys(keysToSave)
        if (result?.verified) {
          message.success(`✅ API Key 已保存并验证成功！${result.models_count ? `可访问 ${result.models_count} 个模型` : ''}`)
        } else if (result?.message) {
          message.warning(`⚠️ ${result.message}`)
        } else {
          message.success('配置已保存')
        }
        
        // 额外验证 API Key（如果保存的是 OpenRouter）
        if (keysToSave.openrouter) {
          try {
            const verifyResult = await frogGptApi.verifyApiKey('openrouter')
            if (verifyResult?.valid) {
              console.log(`✅ API Key 验证成功：${verifyResult.message || 'API Key 有效'}`)
            } else {
              console.warn(`⚠️ API Key 验证失败：${verifyResult?.message || '未知错误'}`)
            }
          } catch (error) {
            console.error('验证 API Key 失败:', error)
          }
        }
      } else {
        message.success('配置已保存')
      }
    } catch (error: any) {
      console.error('保存配置失败:', error)
      message.error(`保存配置失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    }
  }

  // 重置默认配置
  const handleResetConfig = () => {
    setSelectedModel('auto')
    setTemperature(0.7)
    setIncludeSystemData(true)
    setSelectedShopId(undefined)
    setModelSearchValue(null)
    setConnectionType('openrouter')
    setDirectProvider('openai')
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
        styles={{ body: { padding: '10px 16px', position: 'relative' } }}
        variant="borderless"
      >
        <Row gutter={[12, 8]} align="middle" wrap>
          <Col flex="auto">
            <Welcome
              icon={<RobotOutlined style={{ color: '#60a5fa', fontSize: '18px' }} />}
              title={
                <Space size="small">
                  <Text style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 600 }}>
                    FrogGPT 2.0 · 智能运营驾驶舱
                  </Text>
                  <Tag color="blue" className="frog-gpt-tag" style={{ margin: 0, fontSize: '12px', padding: '2px 8px' }}>
                    OpenRouter Ready
                  </Tag>
                </Space>
              }
              description={null}
              extra={
                <Space size="small" wrap>
                  <span className={`frog-gpt-badge ${apiKeyStatus.valid ? 'success' : apiKeyStatus.configured ? 'warn' : ''}`}>
                    {apiKeyStatus.configured 
                      ? (apiKeyStatus.valid ? '✅ OpenRouter API Key 已配置并验证' : '⚠️ OpenRouter API Key 配置异常')
                      : '❌ 未配置 OpenRouter API Key'}
                  </span>
                  <span className="frog-gpt-badge warn">📅 数据范围: 全部时间</span>
                </Space>
              }
            />
          </Col>
          <Col xs={24} md="auto">
            <Space size="small" align="center" style={{ flexWrap: 'nowrap' }}>
              <span className="frog-gpt-badge">
                🤖 模型: {selectedModelDisplay || selectedModel || 'AUTO'}
              </span>
              <span className="frog-gpt-badge">
                🎛️ 温度: {temperature}
              </span>
              <span className="frog-gpt-badge success">
                🛰️ 数据源: {includeSystemData ? '包含系统数据' : '对话模式'}
              </span>
              <Tooltip title="测试 OpenRouter API 连接，验证是否能正确获得回复">
                <Button
                  type="primary"
                  size="small"
                  onClick={async () => {
                    try {
                      const hide = message.loading('正在测试连接...', 0)
                      const result = await frogGptApi.testConnection(selectedModel || 'auto') as any
                      hide()
                      if (result.success) {
                        message.success(`✅ 连接测试成功！使用的模型: ${result.model_used || selectedModel || 'auto'}`)
                        if (result.response_content) {
                          console.log('测试响应内容:', result.response_content)
                        }
                      } else {
                        message.error(`❌ 连接测试失败: ${result.message}`)
                      }
                    } catch (error: any) {
                      message.destroy()
                      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误'
                      message.error(`❌ 连接测试失败: ${errorMsg}`)
                      console.error('测试连接错误:', error)
                    }
                  }}
                  style={{ marginLeft: '8px' }}
                >
                  🔗 测试连接
                </Button>
              </Tooltip>
                <Select
                  allowClear
                  value={selectedShopId}
                  onChange={(value) => setSelectedShopId(value ?? undefined)}
                  placeholder="全部店铺"
                  style={{ minWidth: 200 }}
                showSearch
                optionFilterProp="label"
                  options={(shops || []).map((shop: any) => ({
                  label: shop.name || shop.shop_name || `店铺 ${shop.id}`,
                    value: shop.id,
                  }))}
                />
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
            dataSummaryDays={undefined}
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* 第一步：选择接入方式 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '12px', fontSize: '16px' }}>
              步骤 1：选择接入方式
            </Text>
            <Radio.Group
              value={connectionType}
              onChange={(e) => {
                setConnectionType(e.target.value)
                // 切换接入方式时，如果使用 OpenRouter，默认选择 auto 模型
                if (e.target.value === 'openrouter') {
                  setSelectedModel('auto')
                }
              }}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Radio value="openrouter" style={{ color: '#e2e8f0' }}>
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: '4px' }}>OpenRouter（推荐）</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      一个 API Key 即可访问多种模型，包括 OpenAI、Anthropic、Google 等
                    </div>
                  </div>
                </Radio>
                <Radio value="direct" style={{ color: '#e2e8f0' }}>
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: '4px' }}>直接接入</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      直接使用特定供应商的 API，需要各自的 API Key
                    </div>
                  </div>
                </Radio>
              </Space>
            </Radio.Group>
          </div>

          {/* 第二步：配置 API Key */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '12px', fontSize: '16px' }}>
              步骤 2：配置 API Key
            </Text>
            {connectionType === 'openrouter' ? (
              <div>
                <Input.Password
                  value={apiKeys.openrouter}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, openrouter: e.target.value }))}
                  placeholder="请输入 OpenRouter API Key"
                  allowClear
                  style={{ width: '100%' }}
                />
                <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px', display: 'block' }}>
                  在 <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa' }}>OpenRouter.ai</a> 注册并获取 API Key
                </Text>
              </div>
            ) : (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
                    选择供应商
                  </Text>
                  <Select
                    value={directProvider}
                    onChange={setDirectProvider}
                    style={{ width: '100%' }}
                    options={[
                      { label: 'OpenAI', value: 'openai' },
                      { label: 'Anthropic (Claude)', value: 'anthropic' },
                      { label: 'Google (Gemini)', value: 'gemini' },
                    ]}
                  />
                </div>
                <div>
                  <Text style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
                    API Key
                  </Text>
                  {directProvider === 'openai' && (
                    <Input.Password
                      value={apiKeys.openai}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, openai: e.target.value }))}
                      placeholder="请输入 OpenAI API Key"
                      allowClear
                      style={{ width: '100%' }}
                    />
                  )}
                  {directProvider === 'anthropic' && (
                    <Input.Password
                      value={apiKeys.anthropic}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, anthropic: e.target.value }))}
                      placeholder="请输入 Anthropic API Key"
                      allowClear
                      style={{ width: '100%' }}
                    />
                  )}
                  {directProvider === 'gemini' && (
                    <Input.Password
                      value={apiKeys.gemini}
                      onChange={(e) => setApiKeys(prev => ({ ...prev, gemini: e.target.value }))}
                      placeholder="请输入 Google Gemini API Key"
                      allowClear
                      style={{ width: '100%' }}
                    />
                  )}
                </div>
              </Space>
            )}
          </div>

          {/* 第三步：选择模型 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '12px', fontSize: '16px' }}>
              步骤 3：选择 AI 模型
            </Text>
            {connectionType === 'openrouter' ? (
              <div>
                <AutoComplete
                  value={modelSearchValue !== null ? modelSearchValue : (selectedModelDisplay || selectedModel || '')}
                  onChange={(value) => setModelSearchValue(value)}
                  onSearch={(value) => setModelSearchValue(value)}
              options={filteredModelOptions}
              style={{ width: '100%' }}
              placeholder="选择或搜索AI模型（支持AUTO自动选择）"
              onSelect={(value) => {
                setSelectedModel(value)
                setModelSearchValue(null)
              }}
              onFocus={() => {
                if (modelSearchValue === null && selectedModel) {
                  setModelSearchValue('')
                }
              }}
              onBlur={() => {
                if (modelSearchValue === '') {
                  setModelSearchValue(null)
                } else if (modelSearchValue && modelSearchValue !== selectedModel) {
                  const match = modelOptions.find(opt => 
                    opt.value === modelSearchValue || 
                    opt.searchText?.includes(modelSearchValue.toLowerCase())
                  )
                  if (!match) {
                    setModelSearchValue(null)
                  } else {
                    setSelectedModel(match.value)
                    setModelSearchValue(null)
                  }
                }
              }}
              notFoundContent="未找到匹配的模型"
              dropdownStyle={{
                background: '#1e293b',
                border: '1px solid #334155',
                maxHeight: 400,
              }}
              allowClear
              onClear={() => {
                setSelectedModel('auto')
                setModelSearchValue(null)
              }}
            />
                <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px', display: 'block' }}>
                  选择 AI 模型用于对话。AUTO 选项将自动选择最佳模型。OpenRouter 支持多种模型。
                </Text>
              </div>
            ) : (
              <div>
                <Select
                  value={selectedModel}
                  onChange={setSelectedModel}
                  style={{ width: '100%' }}
                  placeholder="选择模型"
                  options={
                    directProvider === 'openai' ? [
                      { label: 'GPT-4 Turbo', value: 'openai/gpt-4-turbo' },
                      { label: 'GPT-4', value: 'openai/gpt-4' },
                      { label: 'GPT-3.5 Turbo', value: 'openai/gpt-3.5-turbo' },
                    ] : directProvider === 'anthropic' ? [
                      { label: 'Claude 3.5 Sonnet', value: 'anthropic/claude-3.5-sonnet' },
                      { label: 'Claude 3 Opus', value: 'anthropic/claude-3-opus' },
                      { label: 'Claude 3 Sonnet', value: 'anthropic/claude-3-sonnet' },
                    ] : [
                      { label: 'Gemini Pro', value: 'google/gemini-pro' },
                      { label: 'Gemini Pro Vision', value: 'google/gemini-pro-vision' },
                    ]
                  }
                />
                <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px', display: 'block' }}>
                  选择 {directProvider === 'openai' ? 'OpenAI' : directProvider === 'anthropic' ? 'Anthropic' : 'Google'} 的模型
            </Text>
              </div>
            )}
          </div>

          {/* 第四步：其他设置 */}
          <div>
            <Text strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '12px', fontSize: '16px' }}>
              步骤 4：其他设置
            </Text>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* 温度设置 */}
              <div>
                <Text style={{ color: '#e2e8f0', display: 'block', marginBottom: '8px' }}>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <Text style={{ color: '#e2e8f0' }}>包含系统数据</Text>
                <Switch
                  checked={includeSystemData}
                  onChange={setIncludeSystemData}
                  checkedChildren="是"
                  unCheckedChildren="否"
                />
              </div>
                <Text type="secondary" style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px', display: 'block' }}>
              包含系统数据将在对话中包含运营数据摘要，帮助 AI 提供更准确的建议。
            </Text>
          </div>
            </Space>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default FrogGPTV2
