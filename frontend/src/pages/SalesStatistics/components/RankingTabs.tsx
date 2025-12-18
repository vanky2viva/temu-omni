import React from 'react'
import { Tabs, Space } from 'antd'
import { AppstoreOutlined, TeamOutlined } from '@ant-design/icons'
import UnifiedTable from '@/components/Table'

const RankingTabs: React.FC<any> = ({ activeTab, onTabChange, skuRanking, skuLoading, isMobile }) => {
  return (
    <Tabs
      activeKey={activeTab}
      onChange={onTabChange}
      items={[
        {
          key: 'sku',
          label: <Space><AppstoreOutlined /><span>SKU排行</span></Space>,
          children: (
            <UnifiedTable
              variant="compact"
              loading={skuLoading}
              dataSource={skuRanking?.ranking}
              rowKey="sku"
              isMobile={isMobile}
              pagination={{ pageSize: 15 }}
            />
          )
        },
        {
          key: 'manager',
          label: <Space><TeamOutlined /><span>负责人业绩</span></Space>,
          children: <div>负责人排行内容（待完善）</div>
        }
      ]}
    />
  )
}

export default RankingTabs

