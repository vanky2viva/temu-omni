import React from 'react'
import { Tooltip, Button, Space } from 'antd'
import { CopyOutlined, CheckCircleOutlined, WarningOutlined, RightOutlined, DownOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

export function createProfitTableColumns(
  onCopy: (text: string) => void,
  revenueExpanded: Record<string, boolean>,
  onRevenueToggle: (key: string) => void
): ColumnsType<any> {
  return [
    {
      title: 'PO单号',
      dataIndex: 'parent_order_sn',
      key: 'parent_order_sn',
      width: 180,
      fixed: 'left' as const,
      render: (val: string) => (
        <Space>
          <span style={{ fontFamily: 'monospace', fontSize: '11px' }}>{val}</span>
          <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => onCopy(val)} />
        </Space>
      ),
    },
    {
      title: '利润 / 利润率',
      key: 'profit_and_rate',
      width: 180,
      align: 'right' as const,
      fixed: 'right' as const,
      render: (_: any, record: any) => {
        const profit = record.profit || 0
        const profitRate = record.profit_rate || 0
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span style={{ fontWeight: 'bold', color: profit >= 0 ? '#52c41a' : '#f5222d' }}>
              ¥{profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
            <span style={{ fontSize: '12px', opacity: 0.8 }}>{profitRate.toFixed(2)}%</span>
          </div>
        )
      },
    },
  ]
}

