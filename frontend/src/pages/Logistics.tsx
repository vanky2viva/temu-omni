import { Table, Tag, Card, Space, Button } from 'antd'
import type { ColumnsType } from 'antd/es/table'

interface LogisticsData {
  key: string
  orderSn: string
  trackingNumber: string
  carrier: string
  status: string
  destination: string
  shipDate: string
  deliveryDate: string
}

function Logistics() {
  const columns: ColumnsType<LogisticsData> = [
    {
      title: '订单号',
      dataIndex: 'orderSn',
      key: 'orderSn',
      width: 120,
    },
    {
      title: '物流单号',
      dataIndex: 'trackingNumber',
      key: 'trackingNumber',
      width: 140,
    },
    {
      title: '承运商',
      dataIndex: 'carrier',
      key: 'carrier',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colorMap: { [key: string]: string } = {
          '已发货': 'blue',
          '运输中': 'processing',
          '已签收': 'success',
          '异常': 'error',
        }
        return <Tag color={colorMap[status]}>{status}</Tag>
      },
    },
    {
      title: '目的地',
      dataIndex: 'destination',
      key: 'destination',
      width: 100,
    },
    {
      title: '发货日期',
      dataIndex: 'shipDate',
      key: 'shipDate',
      width: 100,
    },
    {
      title: '预计送达',
      dataIndex: 'deliveryDate',
      key: 'deliveryDate',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: () => (
        <Space size="small">
          <Button type="link" size="small">追踪</Button>
          <Button type="link" size="small">详情</Button>
        </Space>
      ),
    },
  ]

  const data: LogisticsData[] = [
    {
      key: '1',
      orderSn: 'ORD00000001',
      trackingNumber: 'TRK2024001',
      carrier: 'UPS',
      status: '运输中',
      destination: 'US',
      shipDate: '2024-10-20',
      deliveryDate: '2024-10-25',
    },
    {
      key: '2',
      orderSn: 'ORD00000002',
      trackingNumber: 'TRK2024002',
      carrier: 'FedEx',
      status: '已签收',
      destination: 'UK',
      shipDate: '2024-10-18',
      deliveryDate: '2024-10-23',
    },
    {
      key: '3',
      orderSn: 'ORD00000003',
      trackingNumber: 'TRK2024003',
      carrier: 'DHL',
      status: '已发货',
      destination: 'DE',
      shipDate: '2024-10-22',
      deliveryDate: '2024-10-27',
    },
  ]

  return (
    <div>
      <h2 style={{ 
        marginBottom: 24, 
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        🚚 物流管理
      </h2>
      
      <Card className="chart-card" style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary">刷新</Button>
          <Button>导出</Button>
          <Button>批量追踪</Button>
        </Space>
      </Card>

      <Card className="chart-card">
        <Table 
          columns={columns} 
          dataSource={data}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />
      </Card>
    </div>
  )
}

export default Logistics

