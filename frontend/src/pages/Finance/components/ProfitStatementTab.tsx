import React, { useState } from 'react'
import { Card, Upload, Button, Row, Col, Progress, Modal, message, Statistic, Space } from 'antd'
import { UploadOutlined, FileExcelOutlined, DollarOutlined } from '@ant-design/icons'
import UnifiedTable from '@/components/Table'
import { profitStatementApi } from '@/services/api'
import { createProfitTableColumns } from './ProfitTableColumns'

const ProfitStatementTab: React.FC<any> = ({ profitData, onProfitDataUpdate }) => {
  const [calculating, setCalculating] = useState(false)
  const [revenueExpanded, setRevenueExpanded] = useState<Record<string, boolean>>({})

  const columns = createProfitTableColumns(
    (text) => { navigator.clipboard.writeText(text); message.success('已复制') },
    revenueExpanded,
    (key) => setRevenueExpanded(prev => ({ ...prev, [key]: !prev[key] }))
  )

  return (
    <div>
      <Card title="上传账单" style={{ marginBottom: 24 }}>
        <Space wrap>
          <Upload showUploadList={false} beforeUpload={(file) => {
            profitStatementApi.uploadCollection(file).then(res => onProfitDataUpdate(res.data))
            return false
          }}>
            <Button icon={<UploadOutlined />}>上传结算表</Button>
          </Upload>
          <Button type="primary" loading={calculating} onClick={() => setCalculating(true)}>计算利润</Button>
        </Space>
      </Card>

      {profitData?.items && (
        <Card title="利润明细">
          <UnifiedTable
            variant="profit-statement"
            columns={columns}
            dataSource={profitData.items}
            rowKey="parent_order_sn"
          />
        </Card>
      )}
    </div>
  )
}

export default ProfitStatementTab

