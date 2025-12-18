import React from 'react'
import { Card, Select, Space, Row, Col, Statistic, Tag, Avatar, Badge, Button } from 'antd'
import { CrownOutlined } from '@ant-design/icons'
import UnifiedTable from '@/components/Table'
import LazyECharts from '@/components/LazyECharts'
import { useHotSeller } from './hooks/useHotSeller'

const HotSellerPage: React.FC = () => {
  const {
    isMobile,
    year, setYear,
    month, setMonth,
    selectedShops, setSelectedShops,
    selectedManager, setSelectedManager,
    isDetailModalOpen, setIsDetailModalOpen,
    shops,
    rankingData,
    isLoading,
    managerSkus,
    skuLoading,
  } = useHotSeller()

  // 这里的列定义和图表配置应从原文件搬移
  const rankingColumns: any[] = [] 
  const gmvChartOption = {}

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}><CrownOutlined /> 爆单榜</h2>
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select value={year} onChange={setYear} options={[]} />
          <Select value={month} onChange={setMonth} options={[]} />
          <Select mode="multiple" value={selectedShops} onChange={setSelectedShops} options={shops?.map((s: any) => ({ label: s.shop_name, value: s.id }))} />
        </Space>
      </Card>

      <UnifiedTable
        variant="default"
        columns={rankingColumns}
        dataSource={rankingData?.ranking}
        loading={isLoading}
        isMobile={isMobile}
        onRow={(record) => ({ onClick: () => { setSelectedManager(record); setIsDetailModalOpen(true) } })}
      />
    </div>
  )
}

export default HotSellerPage

