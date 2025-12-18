import React from 'react'
import { Space, Select, Input, DatePicker, Button, Collapse, Dropdown, Modal } from 'antd'
import { SearchOutlined, FolderOutlined, SaveOutlined, DeleteOutlined, ReloadOutlined, FilterOutlined, DownOutlined, UpOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import type { OrderListFilters, OrderListView } from '../types'

const { RangePicker } = DatePicker

interface OrderFiltersProps {
  filters: OrderListFilters
  setFilters: React.Dispatch<React.SetStateAction<OrderListFilters>>
  isMobile: boolean
  shops: any[] | undefined
  userViews: OrderListView[] | undefined
  currentViewId: number | null
  showAdvancedFilters: boolean
  setShowAdvancedFilters: (show: boolean) => void
  onSaveView: () => void
  onLoadView: (view: OrderListView) => void
  onDeleteView: (viewId: number) => void
  onFilterChange: () => void
  onReset: () => void
}

const OrderFilters: React.FC<OrderFiltersProps> = ({
  filters,
  setFilters,
  isMobile,
  shops,
  userViews,
  currentViewId,
  showAdvancedFilters,
  setShowAdvancedFilters,
  onSaveView,
  onLoadView,
  onDeleteView,
  onFilterChange,
  onReset,
}) => {
  return (
    <>
      <div className="order-filters-main">
        <Space size={isMobile ? "small" : "middle"} wrap={isMobile} direction={isMobile ? "vertical" : "horizontal"} style={{ width: '100%' }}>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'save',
                  label: '保存当前视图',
                  icon: <SaveOutlined />,
                  onClick: onSaveView,
                },
                ...(userViews && userViews.length > 0 ? [
                  { type: 'divider' as const },
                  ...userViews.map((view) => ({
                    key: `view-${view.id}`,
                    label: (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                        <span>{view.name}{view.is_default && ' (默认)'}</span>
                        <Button
                          type="text"
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={(e) => {
                            e.stopPropagation()
                            Modal.confirm({
                              title: '确认删除',
                              content: `确定要删除视图"${view.name}"吗？`,
                              onOk: () => onDeleteView(view.id),
                            })
                          }}
                        />
                      </div>
                    ),
                    onClick: () => onLoadView(view),
                  }))
                ] : []),
              ],
            }}
            trigger={['click']}
          >
            <Button icon={<FolderOutlined />}>
              {currentViewId ? userViews?.find(v => v.id === currentViewId)?.name || '选择视图' : '视图'}
            </Button>
          </Dropdown>

          <Input
            placeholder="搜索订单号、商品名称或SKU..."
            prefix={<SearchOutlined />}
            allowClear
            value={filters.searchKeyword}
            onChange={(e) => {
              setFilters(prev => ({ ...prev, searchKeyword: e.target.value }))
              onFilterChange()
            }}
            onPressEnter={onFilterChange}
            style={{ width: isMobile ? '100%' : '280px' }}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
            <span style={{ opacity: 0.7, fontSize: '14px' }}>店铺：</span>
            <Select
              mode="multiple"
              style={{ width: isMobile ? '100%' : 180 }}
              placeholder="全部店铺"
              allowClear
              value={filters.shopIds.length > 0 ? filters.shopIds : undefined}
              onChange={(values) => {
                setFilters(prev => ({ ...prev, shopIds: values || [], shopId: values && values.length === 1 ? values[0] : undefined }))
                onFilterChange()
              }}
              options={shops?.map((shop: any) => ({ label: shop.shop_name, value: shop.id }))}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto' }}>
            <span style={{ opacity: 0.7, fontSize: '14px' }}>状态：</span>
            <Select
              style={{ width: isMobile ? '100%' : 150 }}
              placeholder="全部状态"
              allowClear
              value={filters.statusFilter}
              onChange={(value) => {
                setFilters(prev => ({ ...prev, statusFilter: value, statusFilters: value ? [value] : [] }))
                onFilterChange()
              }}
              options={[
                { label: '待处理', value: 'PENDING' },
                { label: '未发货', value: 'PROCESSING' },
                { label: '已发货', value: 'SHIPPED' },
                { label: '已送达', value: 'DELIVERED' },
                { label: '已取消', value: 'CANCELLED' },
              ]}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: isMobile ? '100%' : 'auto', flexWrap: isMobile ? 'wrap' : 'nowrap' }}>
            <span style={{ opacity: 0.7, fontSize: '14px' }}>日期：</span>
            <Select
              placeholder="快捷选择"
              allowClear
              style={{ width: isMobile ? '100%' : 120 }}
              onChange={(value) => {
                let start: dayjs.Dayjs | null = null
                let end: dayjs.Dayjs = dayjs()
                if (value === 'today') start = dayjs().startOf('day')
                else if (value === 'yesterday') { start = dayjs().subtract(1, 'day').startOf('day'); end = dayjs().subtract(1, 'day').endOf('day') }
                else if (value === 'last7days') start = dayjs().subtract(6, 'day').startOf('day')
                else if (value === 'last30days') start = dayjs().subtract(29, 'day').startOf('day')
                else if (value === 'thisMonth') start = dayjs().startOf('month')
                else if (value === 'lastMonth') { start = dayjs().subtract(1, 'month').startOf('month'); end = dayjs().subtract(1, 'month').endOf('month') }
                
                setFilters(prev => ({ ...prev, dateRange: start ? [start, end] : null }))
                onFilterChange()
              }}
              options={[
                { label: '今天', value: 'today' },
                { label: '昨天', value: 'yesterday' },
                { label: '最近7天', value: 'last7days' },
                { label: '最近30天', value: 'last30days' },
                { label: '本月', value: 'thisMonth' },
                { label: '上月', value: 'lastMonth' },
              ]}
            />
            <RangePicker
              value={filters.dateRange}
              onChange={(dates) => {
                setFilters(prev => ({ ...prev, dateRange: dates as any }))
                onFilterChange()
              }}
              format="YYYY-MM-DD"
              style={{ width: isMobile ? '100%' : 240 }}
            />
          </div>

          <Button icon={<ReloadOutlined />} onClick={onReset}>重置</Button>
        </Space>
      </div>

      <div className="order-filters-advanced">
        <Collapse
          activeKey={showAdvancedFilters ? ['advanced'] : []}
          onChange={(keys) => setShowAdvancedFilters(keys.length > 0)}
          style={{ background: 'transparent', border: 'none' }}
          items={[{
            key: 'advanced',
            label: (
              <Space>
                <FilterOutlined />
                <span>高级筛选</span>
                {showAdvancedFilters ? <UpOutlined /> : <DownOutlined />}
              </Space>
            ),
            children: (
              <Space size={isMobile ? "small" : "middle"} wrap direction={isMobile ? "vertical" : "horizontal"} style={{ width: '100%', paddingTop: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ opacity: 0.7, fontSize: '14px' }}>订单号：</span>
                  <Input
                    placeholder="订单号"
                    allowClear
                    value={filters.orderSn}
                    onChange={(e) => { setFilters(prev => ({ ...prev, orderSn: e.target.value })); onFilterChange() }}
                    style={{ width: 200 }}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ opacity: 0.7, fontSize: '14px' }}>商品名称：</span>
                  <Input
                    placeholder="商品名称"
                    allowClear
                    value={filters.productName}
                    onChange={(e) => { setFilters(prev => ({ ...prev, productName: e.target.value })); onFilterChange() }}
                    style={{ width: 200 }}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ opacity: 0.7, fontSize: '14px' }}>SKU：</span>
                  <Input
                    placeholder="SKU"
                    allowClear
                    value={filters.productSku}
                    onChange={(e) => { setFilters(prev => ({ ...prev, productSku: e.target.value })); onFilterChange() }}
                    style={{ width: 200 }}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ opacity: 0.7, fontSize: '14px' }}>延误风险：</span>
                  <Select
                    style={{ width: 150 }}
                    placeholder="全部"
                    allowClear
                    value={filters.delayRiskLevel}
                    onChange={(value) => { setFilters(prev => ({ ...prev, delayRiskLevel: value })); onFilterChange() }}
                    options={[
                      { label: '正常', value: 'normal' },
                      { label: '临界', value: 'warning' },
                      { label: '延误', value: 'delayed' },
                    ]}
                  />
                </div>
              </Space>
            )
          }]}
        />
      </div>
    </>
  )
}

export default OrderFilters
