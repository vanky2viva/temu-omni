import React from 'react'
import { Space, Select, Input, Button, Modal } from 'antd'
import { SearchOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ProductListFilters } from '../types'

interface ProductFiltersProps {
  filters: ProductListFilters
  setFilters: React.Dispatch<React.SetStateAction<ProductListFilters>>
  shops: any[] | undefined
  managerOptions: string[]
  categoryOptions: string[]
  onClearProducts: () => void
  isClearing: boolean
  onSearch: () => void
}

const ProductFilters: React.FC<ProductFiltersProps> = ({
  filters,
  setFilters,
  shops,
  managerOptions,
  categoryOptions,
  onClearProducts,
  isClearing,
  onSearch,
}) => {
  return (
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Space size="middle" wrap>
        <span>店铺：</span>
        <Select
          allowClear
          placeholder="全部店铺"
          style={{ width: 200 }}
          value={filters.shopId}
          onChange={(val) => setFilters(prev => ({ ...prev, shopId: val }))}
          options={shops?.map((s: any) => ({ label: s.shop_name, value: s.id }))}
        />

        <span>负责人：</span>
        <Select
          allowClear
          placeholder="全部负责人"
          style={{ width: 160 }}
          value={filters.manager}
          onChange={(val) => setFilters(prev => ({ ...prev, manager: val }))}
          options={managerOptions.map(m => ({ label: m, value: m }))}
        />

        <span>类目：</span>
        <Select
          allowClear
          placeholder="全部类目"
          style={{ width: 160 }}
          value={filters.category}
          onChange={(val) => setFilters(prev => ({ ...prev, category: val }))}
          options={categoryOptions.map(c => ({ label: c, value: c }))}
        />

        <span>关键词：</span>
        <Input
          allowClear
          style={{ width: 220 }}
          prefix={<SearchOutlined />}
          placeholder="商品名/SKU"
          value={filters.keyword}
          onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
          onPressEnter={onSearch}
        />

        <span>状态：</span>
        <Select
          style={{ width: 160 }}
          value={filters.statusFilter}
          onChange={(val) => setFilters(prev => ({ ...prev, statusFilter: val }))}
          options={[
            { label: '在售中', value: 'published' },
            { label: '未发布', value: 'unpublished' },
            { label: '全部', value: 'all' },
          ]}
        />
      </Space>
      <Space>
        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={onClearProducts}
          loading={isClearing}
        >
          清理商品数据
        </Button>
      </Space>
    </div>
  )
}

export default ProductFilters

