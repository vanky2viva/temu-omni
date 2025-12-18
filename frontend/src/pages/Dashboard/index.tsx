import React from 'react'
import { Button, Row, Col, Spin } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import LazyECharts from '@/components/LazyECharts'
import { useDashboard } from './hooks/useDashboard'
import StatsCards from './components/StatsCards'

const Dashboard: React.FC = () => {
  const { isMobile, overview, overviewLoading, dailyData, dailyLoading } = useDashboard()

  if (overviewLoading || dailyLoading) return <Spin size="large" />

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2>📊 数据总览</h2>
        <Button icon={<ReloadOutlined />}>刷新</Button>
      </div>
      <StatsCards overview={overview} isMobile={isMobile} />
      {/* 趋势图表逻辑 */}
    </div>
  )
}

export default Dashboard

