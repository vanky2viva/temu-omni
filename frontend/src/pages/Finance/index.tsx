import React from 'react'
import { Tabs, DatePicker, Button, Space } from 'antd'
import { useFinance } from './hooks/useFinance'
import FinanceOverview from './components/FinanceOverview'
import ProfitStatementTab from './components/ProfitStatementTab'
import UnifiedTable from '@/components/Table'
import './styles/index.css'

const { RangePicker } = DatePicker

const Finance: React.FC = () => {
  const {
    isMobile,
    dateRange,
    setDateRange,
    isAllData,
    setIsAllData,
    activeTabKey,
    setActiveTabKey,
    monthlyStats,
    monthlyStatsLoading,
    collectionData,
    collectionLoading,
  } = useFinance()

  return (
    <div className="finance-container">
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>财务管理</h2>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => { setDateRange(dates as any); setIsAllData(false) }}
            disabled={isAllData}
          />
          <Button type={isAllData ? 'primary' : 'default'} onClick={() => setIsAllData(true)}>全部</Button>
        </Space>
      </div>

      <FinanceOverview stats={monthlyStats} loading={monthlyStatsLoading} isMobile={isMobile} />

      <Tabs
        activeKey={activeTabKey}
        onChange={setActiveTabKey}
        items={[
          {
            key: 'estimated-collection',
            label: '回款统计',
            children: (
              <UnifiedTable
                loading={collectionLoading}
                dataSource={collectionData?.table_data}
                columns={[]} // 简化版，实际应从原文件迁移完整列定义
              />
            )
          },
          {
            key: 'profit-statement',
            label: '账单统计',
            children: (
              <ProfitStatementTab
                profitData={null}
                onProfitDataUpdate={() => {}}
              />
            )
          }
        ]}
      />
    </div>
  )
}

export default Finance

