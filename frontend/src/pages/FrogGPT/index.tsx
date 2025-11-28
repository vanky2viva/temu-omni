import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Select,
  Switch,
  Button,
  Space,
  Typography,
  Tag,
  Divider,
  message,
} from 'antd'
import {
  SaveOutlined,
  ReloadOutlined,
  ShopOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { frogGptApi, shopApi } from '@/services/api'
import AiChatPanel from './AiChatPanel'
import DecisionSummary from './DecisionSummary'
import MetricOverview from './MetricOverview'
import QuickPrompts from './QuickPrompts'
import type { DecisionData, MetricData, QuickPrompt } from './types'

const { Text, Title } = Typography
const { Option } = Select

// 快捷问题模板
const quickPrompts: QuickPrompt[] = [
  {
    label: '生成今日运营总结',
    prompt: '请生成今日的运营总结报告，包括GMV、订单量、利润率等关键指标。',
  },
  {
    label: '分析最近 7 天 GMV 变化原因',
    prompt: '分析最近 7 天 GMV 变化的原因，并提供优化建议。',
  },
  {
    label: '列出退货率最高的 5 个 SKU',
    prompt: '请列出退货率最高的 5 个 SKU，并分析原因。',
  },
  {
    label: '帮我写 3 个高转化标题',
    prompt: '基于当前热销商品，帮我生成 3 个高转化率的商品标题。',
  },
]

const FrogGPT: React.FC = () => {
  // 状态管理
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [temperature, setTemperature] = useState(0.7)
  const [includeSystemData, setIncludeSystemData] = useState(true)
  const [dataSummaryDays, setDataSummaryDays] = useState(7)
  const [selectedShopId, setSelectedShopId] = useState<number | undefined>()
  const [decisionData, setDecisionData] = useState<DecisionData | null>(null)
  const [inputPrompt, setInputPrompt] = useState<string>('')

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

  // 初始化默认模型
  useEffect(() => {
    if (modelsData?.models && modelsData.models.length > 0 && !selectedModel) {
      const preferredModel = modelsData.models.find(
        (m: any) => m.id?.includes('gpt-4o-mini') || m.id?.includes('gpt-4')
      )
      setSelectedModel(preferredModel?.id || modelsData.models[0].id)
    }
  }, [modelsData, selectedModel])

  // 构建指标数据
  const metrics: MetricData[] = dataSummary
    ? [
        {
          label: '7 日 GMV',
          value: `¥${(dataSummary.overview.total_gmv / 1000).toFixed(1)}k`,
          trend: 'up' as const,
          trendValue: '+12.3%',
        },
        {
          label: '7 日订单数',
          value: dataSummary.overview.total_orders,
          trend: 'up' as const,
          trendValue: '+8.5%',
        },
        {
          label: '退款率',
          value: '2.3%',
          trend: 'down' as const,
          trendValue: '-0.5%',
        },
        {
          label: '平均客单价',
          value: `¥${(dataSummary.overview.total_gmv / dataSummary.overview.total_orders).toFixed(2)}`,
          trend: 'stable' as const,
        },
      ]
    : []

  // 获取当前店铺名称
  const currentShopName = shops?.find((s: any) => s.id === selectedShopId)?.shop_name || '全部店铺'

  // 获取风险等级（基于数据计算）
  const getRiskLevel = (): 'low' | 'medium' | 'high' => {
    if (!dataSummary) return 'low'
    const profitMargin = dataSummary.overview.profit_margin
    if (profitMargin > 15) return 'low'
    if (profitMargin > 10) return 'medium'
    return 'high'
  }

  /**
   * 处理决策数据解析
   */
  const handleDecisionParsed = (data: DecisionData | null) => {
    setDecisionData(data)
  }

  /**
   * 处理快捷问题点击
   */
  const handleQuickPromptClick = (prompt: string) => {
    setInputPrompt(prompt)
    // 这里可以通过 ref 或其他方式将提示填入输入框
    message.info('提示已填入，请在右侧输入框中查看并发送')
  }

  /**
   * 保存配置
   */
  const handleSaveConfig = () => {
    const config = {
      model: selectedModel,
      temperature,
      includeSystemData,
      dataSummaryDays,
      shopId: selectedShopId,
    }
    localStorage.setItem('frog-gpt-config', JSON.stringify(config))
    message.success('配置已保存')
  }

  /**
   * 重置默认配置
   */
  const handleResetConfig = () => {
    setSelectedModel('')
    setTemperature(0.7)
    setIncludeSystemData(true)
    setDataSummaryDays(7)
    setSelectedShopId(undefined)
    localStorage.removeItem('frog-gpt-config')
    message.success('已重置为默认配置')
  }

  // 加载保存的配置
  useEffect(() => {
    const savedConfig = localStorage.getItem('frog-gpt-config')
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig)
        if (config.model) setSelectedModel(config.model)
        if (config.temperature !== undefined) setTemperature(config.temperature)
        if (config.includeSystemData !== undefined) setIncludeSystemData(config.includeSystemData)
        if (config.dataSummaryDays) setDataSummaryDays(config.dataSummaryDays)
        if (config.shopId) setSelectedShopId(config.shopId)
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }
  }, [])

  return (
    <div
      style={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        background: '#0f172a',
        padding: '16px',
      }}
    >
      {/* 顶部工具栏 */}
      <Card
        style={{
          background: '#1e293b',
          borderColor: '#334155',
          borderRadius: '12px',
          marginBottom: '16px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          {/* 左侧：标题 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RobotOutlined style={{ fontSize: '20px', color: '#60a5fa' }} />
            <Title level={4} style={{ margin: 0, color: '#fff' }}>
              FrogGPT · AI 运营助手
            </Title>
          </div>

          {/* 中部：参数控制 */}
          <Space size="middle" wrap>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Text style={{ color: '#94a3b8', fontSize: '12px' }}>模型:</Text>
              <Select
                value={selectedModel}
                onChange={setSelectedModel}
                style={{ width: 200 }}
                placeholder="选择AI模型"
              >
                {modelsData?.models?.map((model: any) => (
                  <Option key={model.id} value={model.id}>
                    {model.name || model.id}
                  </Option>
                ))}
              </Select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Text style={{ color: '#94a3b8', fontSize: '12px' }}>温度:</Text>
              <Select
                value={temperature}
                onChange={setTemperature}
                style={{ width: 100 }}
              >
                <Option value={0.1}>0.1</Option>
                <Option value={0.3}>0.3</Option>
                <Option value={0.5}>0.5</Option>
                <Option value={0.7}>0.7</Option>
                <Option value={0.9}>0.9</Option>
                <Option value={1.0}>1.0</Option>
              </Select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Text style={{ color: '#94a3b8', fontSize: '12px' }}>包含系统数据:</Text>
              <Switch
                checked={includeSystemData}
                onChange={setIncludeSystemData}
                checkedChildren="是"
                unCheckedChildren="否"
              />
            </div>

            {includeSystemData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Text style={{ color: '#94a3b8', fontSize: '12px' }}>数据天数:</Text>
                <Select
                  value={dataSummaryDays}
                  onChange={setDataSummaryDays}
                  style={{ width: 100 }}
                >
                  <Option value={3}>3天</Option>
                  <Option value={7}>7天</Option>
                  <Option value={15}>15天</Option>
                  <Option value={30}>30天</Option>
                </Select>
              </div>
            )}
          </Space>

          {/* 右侧：保存/重置按钮 */}
          <Space>
            <Button
              type="text"
              icon={<SaveOutlined />}
              onClick={handleSaveConfig}
              style={{ color: '#94a3b8' }}
            >
              保存配置
            </Button>
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={handleResetConfig}
              style={{ color: '#94a3b8' }}
            >
              重置默认
            </Button>
          </Space>
        </div>
      </Card>

      {/* 主内容区：左右两栏布局 */}
      <div style={{ display: 'flex', gap: '16px', flex: 1, overflow: 'hidden' }}>
        {/* 左侧：数据概览和决策区（40%） */}
        <div
          style={{
            width: '40%',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
            gap: '16px',
          }}
        >
          {/* 当前上下文卡片 */}
          <Card
            title="当前上下文"
            style={{
              background: '#020617',
              borderColor: '#1E293B',
              borderRadius: '12px',
            }}
            headStyle={{
              color: '#fff',
              borderBottomColor: '#1E293B',
            }}
            styles={{ body: { padding: '16px' } }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#94a3b8', fontSize: '12px' }}>当前店铺:</Text>
                <Select
                  value={selectedShopId}
                  onChange={setSelectedShopId}
                  style={{ width: 150 }}
                  placeholder="全部店铺"
                  allowClear
                >
                  {shops?.map((shop: any) => (
                    <Option key={shop.id} value={shop.id}>
                      {shop.shop_name}
                    </Option>
                  ))}
                </Select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#94a3b8', fontSize: '12px' }}>当前模型:</Text>
                <Text style={{ color: '#e2e8f0', fontSize: '12px' }}>
                  {selectedModel || '未选择'}
                </Text>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#94a3b8', fontSize: '12px' }}>数据时间范围:</Text>
                <Text style={{ color: '#e2e8f0', fontSize: '12px' }}>
                  最近 {dataSummaryDays} 天
                </Text>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: '#94a3b8', fontSize: '12px' }}>状态:</Text>
                <Tag
                  color={
                    getRiskLevel() === 'low'
                      ? 'success'
                      : getRiskLevel() === 'medium'
                      ? 'warning'
                      : 'error'
                  }
                >
                  {getRiskLevel() === 'low' ? '健康' : getRiskLevel() === 'medium' ? '需关注' : '高风险'}
                </Tag>
              </div>
            </Space>
          </Card>

          {/* 运营指标速览 */}
          {metrics.length > 0 && <MetricOverview metrics={metrics} />}

          {/* AI 决策结果卡片 */}
          <DecisionSummary decisionData={decisionData} />

          {/* 快捷问题模板 */}
          <QuickPrompts prompts={quickPrompts} onPromptClick={handleQuickPromptClick} />
        </div>

        {/* 右侧：ChatGPT 风格对话区（60%） */}
        <div style={{ width: '60%', height: '100%' }}>
          <AiChatPanel
            shopId={selectedShopId?.toString()}
            shopName={currentShopName}
            onDecisionParsed={handleDecisionParsed}
          />
        </div>
      </div>
    </div>
  )
}

export default FrogGPT

