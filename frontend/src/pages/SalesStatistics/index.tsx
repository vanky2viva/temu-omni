import React from 'react'
import { Button, Space, DatePicker, Select, Tooltip } from 'antd'
import { ReloadOutlined, RocketOutlined } from '@ant-design/icons'
import { useSalesStatistics } from './hooks/useSalesStatistics'
import StatsCards from './components/StatsCards'
import RankingTabs from './components/RankingTabs'
import './styles/index.css'

const { RangePicker } = DatePicker

const SalesStatistics: React.FC = () => {
  const {
    isMobile,
    dateRange,
    setDateRange,
    quickSelectValue,
    setQuickSelectValue,
    shopIds,
    setShopIds,
    activeTab,
    setActiveTab,
    isRefreshing,
    countdown,
    handleRefresh,
    shops,
    salesOverview,
    skuRanking,
    skuLoading,
  } = useSalesStatistics()

  return (
    <div className="sales-statistics-container" style={{ padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}><RocketOutlined /> 销售数据分析</h1>
        <Space>
          <span style={{ fontSize: 12, color: '#8b949e' }}>自动刷新: {countdown}s</span>
          <Button icon={<ReloadOutlined />} loading={isRefreshing} onClick={handleRefresh}>刷新</Button>
        </Space>
      </div>

      <div className="bulma-card" style={{ padding: 12, marginBottom: 16 }}>
        <Space wrap>
          <RangePicker value={dateRange} onChange={setDateRange as any} />
          <Select
            style={{ width: 200 }}
            mode="multiple"
            placeholder="选择店铺"
            value={shopIds}
            onChange={setShopIds}
            options={shops?.map((s: any) => ({ label: s.shop_name, value: s.id }))}
          />
        </Space>
      </div>

      <StatsCards data={salesOverview} isMobile={isMobile} />

      <div className="bulma-card" style={{ padding: 12 }}>
        <RankingTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          skuRanking={skuRanking}
          skuLoading={skuLoading}
          isMobile={isMobile}
        />
      </div>
    </div>
  )
}

export default SalesStatistics

