import React from 'react'
import { Select, Tooltip, Space, InputNumber, Button, Tag, Modal, Input, message } from 'antd'
import { EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

interface ProductTableColumnsProps {
  shops: any[] | undefined
  managerOptions: string[]
  onUpdateManager: (id: number, manager: string) => void
  isEditingSupplyPrice: { [key: number]: boolean }
  setIsEditingSupplyPrice: React.Dispatch<React.SetStateAction<{ [key: number]: boolean }>>
  editingSupplyPrice: { [key: number]: number | null }
  setEditingSupplyPrice: React.Dispatch<React.SetStateAction<{ [key: number]: number | null }>>
  onSaveSupplyPrice: (id: number, price: number) => void
  isSupplyPriceLoading: boolean
  isEditingCostPrice: { [key: number]: boolean }
  setIsEditingCostPrice: React.Dispatch<React.SetStateAction<{ [key: number]: boolean }>>
  editingCostPrice: { [key: number]: number | null }
  setEditingCostPrice: React.Dispatch<React.SetStateAction<{ [key: number]: number | null }>>
  onSaveCostPrice: (id: number, price: number) => void
  isCostPriceLoading: boolean
}

export function createProductTableColumns({
  shops,
  managerOptions,
  onUpdateManager,
  isEditingSupplyPrice,
  setIsEditingSupplyPrice,
  editingSupplyPrice,
  setEditingSupplyPrice,
  onSaveSupplyPrice,
  isSupplyPriceLoading,
  isEditingCostPrice,
  setIsEditingCostPrice,
  editingCostPrice,
  setEditingCostPrice,
  onSaveCostPrice,
  isCostPriceLoading,
}: ProductTableColumnsProps): ColumnsType<any> {
  return [
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 120,
      render: (manager: string, record: any) => (
        <Select
          value={manager || '-'}
          style={{ width: '100%' }}
          size="small"
          bordered={false}
          dropdownMatchSelectWidth={false}
          onChange={(value) => {
            if (value === '__custom__') {
              Modal.confirm({
                title: '输入新的负责人',
                content: (
                  <Input 
                    id="custom-manager-input" 
                    placeholder="请输入负责人姓名"
                    autoFocus
                  />
                ),
                onOk: () => {
                  const input = document.getElementById('custom-manager-input') as HTMLInputElement
                  const newManager = input?.value?.trim()
                  if (newManager) {
                    onUpdateManager(record.id, newManager)
                  }
                }
              })
            } else {
              onUpdateManager(record.id, value)
            }
          }}
          options={[
            ...managerOptions.map(m => ({ label: m, value: m })),
            { label: '+ 自定义', value: '__custom__' }
          ]}
        />
      ),
    },
    {
      title: '类目',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => {
        if (!category || category === '-') return '-'
        const parts = category.split('>').map(p => p.trim())
        const lastLevel = parts[parts.length - 1] || category
        if (parts.length > 1) {
          return (
            <Tooltip title={category}>
              <span style={{ fontSize: '12px', lineHeight: '1.4', cursor: 'help' }}>
                {lastLevel}
              </span>
            </Tooltip>
          )
        }
        return <span style={{ fontSize: '12px', lineHeight: '1.4' }}>{category}</span>
      },
    },
    {
      title: '经营站点',
      dataIndex: 'shop_id',
      key: 'site',
      width: 120,
      render: (shopId: number) => {
        const shop = shops?.find((s: any) => s.id === shopId)
        return shop?.region?.toUpperCase?.() || '-'
      },
    },
    {
      title: 'SKU ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 150,
    },
    {
      title: 'SKU货号',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
      render: (sku: string) => sku || '-',
    },
    {
      title: '累计销量',
      dataIndex: 'total_sales',
      key: 'total_sales',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => (a.total_sales || 0) - (b.total_sales || 0),
      defaultSortOrder: 'descend' as const,
      render: (totalSales: number) => totalSales || 0,
    },
    {
      title: '供货价',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 180,
      render: (price: number, record: any) => {
        const isEditing = isEditingSupplyPrice[record.id] || false
        const currentValue = editingSupplyPrice[record.id] !== undefined 
          ? editingSupplyPrice[record.id] 
          : (price ?? 0)

        return (
          <Space.Compact style={{ width: '100%' }}>
            <InputNumber
              value={currentValue}
              style={{ flex: 1 }}
              size="small"
              min={0}
              precision={2}
              placeholder="0"
              disabled={!isEditing}
              onChange={(value) => {
                setEditingSupplyPrice(prev => ({ ...prev, [record.id]: value }))
              }}
              addonAfter="CNY"
            />
            {isEditing ? (
              <>
                <Button
                  type="primary"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={() => onSaveSupplyPrice(record.id, currentValue ?? 0)}
                  loading={isSupplyPriceLoading}
                />
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => {
                    setIsEditingSupplyPrice(prev => { const n = {...prev}; delete n[record.id]; return n })
                    setEditingSupplyPrice(prev => { const n = {...prev}; delete n[record.id]; return n })
                  }}
                  disabled={isSupplyPriceLoading}
                />
              </>
            ) : (
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => {
                  setIsEditingSupplyPrice(prev => ({ ...prev, [record.id]: true }))
                  setEditingSupplyPrice(prev => ({ ...prev, [record.id]: price ?? 0 }))
                }}
              />
            )}
          </Space.Compact>
        )
      },
    },
    {
      title: '成本价格',
      dataIndex: 'current_cost_price',
      key: 'current_cost_price',
      width: 180,
      render: (costPrice: number, record: any) => {
        const isEditing = isEditingCostPrice[record.id] || false
        const currentValue = editingCostPrice[record.id] !== undefined 
          ? editingCostPrice[record.id] 
          : (costPrice ?? 0)

        return (
          <Space.Compact style={{ width: '100%' }}>
            <InputNumber
              value={currentValue}
              style={{ flex: 1 }}
              size="small"
              min={0}
              precision={2}
              placeholder="0"
              disabled={!isEditing}
              onChange={(value) => {
                setEditingCostPrice(prev => ({ ...prev, [record.id]: value }))
              }}
              addonAfter="CNY"
            />
            {isEditing ? (
              <>
                <Button
                  type="primary"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={() => onSaveCostPrice(record.id, currentValue ?? 0)}
                  loading={isCostPriceLoading}
                />
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => {
                    setIsEditingCostPrice(prev => { const n = {...prev}; delete n[record.id]; return n })
                    setEditingCostPrice(prev => { const n = {...prev}; delete n[record.id]; return n })
                  }}
                  disabled={isCostPriceLoading}
                />
              </>
            ) : (
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => {
                  setIsEditingCostPrice(prev => ({ ...prev, [record.id]: true }))
                  setEditingCostPrice(prev => ({ ...prev, [record.id]: costPrice ?? 0 }))
                }}
              />
            )}
          </Space.Compact>
        )
      },
    },
    {
      title: '上架日期',
      dataIndex: 'listed_at',
      key: 'listed_at',
      width: 140,
      sorter: (a: any, b: any) => {
        const dateA = a.listed_at || a.created_at
        const dateB = b.listed_at || b.created_at
        return new Date(dateA).getTime() - new Date(dateB).getTime()
      },
      render: (listedAt: string, record: any) => {
        const date = listedAt || record.created_at
        return date ? dayjs(date).format('YYYY-MM-DD') : '-'
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '在售中' : '未发布'}
        </Tag>
      ),
    },
  ]
}

