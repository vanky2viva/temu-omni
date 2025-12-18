import React from 'react'
import { Space, Button, Dropdown } from 'antd'
import { ExportOutlined, TagOutlined, FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

interface BatchActionsProps {
  selectedCount: number
  onCancel: () => void
  onExport: (format: 'csv' | 'excel') => void
  onTags: () => void
  onNotes: () => void
  onStatus: (status: string) => void
}

const BatchActions: React.FC<BatchActionsProps> = ({
  selectedCount,
  onCancel,
  onExport,
  onTags,
  onNotes,
  onStatus,
}) => {
  if (selectedCount === 0) return null

  return (
    <div className="batch-actions-bar">
      <Space>
        <span style={{ fontWeight: 'bold' }}>已选择 {selectedCount} 个订单</span>
        <Button type="text" size="small" onClick={onCancel}>取消选择</Button>
      </Space>
      <Space>
        <Dropdown
          menu={{
            items: [
              { key: 'export-csv', label: '导出为 CSV', icon: <ExportOutlined />, onClick: () => onExport('csv') },
              { key: 'export-excel', label: '导出为 Excel', icon: <ExportOutlined />, onClick: () => onExport('excel') },
            ],
          }}
          trigger={['click']}
        >
          <Button icon={<ExportOutlined />}>导出</Button>
        </Dropdown>
        <Button icon={<TagOutlined />} onClick={onTags}>标签</Button>
        <Button icon={<FileTextOutlined />} onClick={onNotes}>备注</Button>
        <Dropdown
          menu={{
            items: [
              { key: 'mark-shipped', label: '标记为已发货', icon: <CheckCircleOutlined />, onClick: () => onStatus('SHIPPED') },
              { key: 'mark-delivered', label: '标记为已送达', icon: <CheckCircleOutlined />, onClick: () => onStatus('DELIVERED') },
              { type: 'divider' },
              { key: 'mark-cancelled', label: '标记为已取消', icon: <CloseCircleOutlined />, danger: true, onClick: () => onStatus('CANCELLED') },
            ],
          }}
          trigger={['click']}
        >
          <Button>状态</Button>
        </Dropdown>
      </Space>
    </div>
  )
}

export default BatchActions
