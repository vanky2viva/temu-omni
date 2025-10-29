import { Table, Tag, Card, Space, Button, Row, Col, Statistic } from 'antd'
import { DollarOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

interface FinanceData {
  key: string
  date: string
  orderSn: string
  amount: number
  cost: number
  profit: number
  status: string
  paymentMethod: string
}

function Finance() {
  const columns: ColumnsType<FinanceData> = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 100,
    },
    {
      title: '订单号',
      dataIndex: 'orderSn',
      key: 'orderSn',
      width: 120,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => `$${amount.toFixed(2)}`,
    },
    {
      title: '成本',
      dataIndex: 'cost',
      key: 'cost',
      width: 100,
      render: (cost: number) => `$${cost.toFixed(2)}`,
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      render: (profit: number) => (
        <span style={{ color: profit > 0 ? '#3fb950' : '#f85149' }}>
          ${profit.toFixed(2)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const colorMap: { [key: string]: string } = {
          '已结算': 'success',
          '待结算': 'warning',
          '已退款': 'error',
        }
        return <Tag color={colorMap[status]}>{status}</Tag>
      },
    },
    {
      title: '支付方式',
      dataIndex: 'paymentMethod',
      key: 'paymentMethod',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: () => (
        <Space size="small">
          <Button type="link" size="small">查看</Button>
          <Button type="link" size="small">导出</Button>
        </Space>
      ),
    },
  ]

  const data: FinanceData[] = [
    {
      key: '1',
      date: '2024-10-25',
      orderSn: 'ORD00000001',
      amount: 58.24,
      cost: 35.50,
      profit: 22.74,
      status: '已结算',
      paymentMethod: 'Credit Card',
    },
    {
      key: '2',
      date: '2024-10-25',
      orderSn: 'ORD00000002',
      amount: 81.45,
      cost: 48.20,
      profit: 33.25,
      status: '已结算',
      paymentMethod: 'PayPal',
    },
    {
      key: '3',
      date: '2024-10-24',
      orderSn: 'ORD00000003',
      amount: 63.45,
      cost: 38.90,
      profit: 24.55,
      status: '待结算',
      paymentMethod: 'Credit Card',
    },
  ]

  return (
    <div>
      <h2 style={{ 
        marginBottom: 24, 
        color: '#c9d1d9',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        💰 财务管理
      </h2>
      
      {/* 财务统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="本月总收入"
              value={74403.62}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="本月总利润"
              value={33502.25}
              precision={2}
              prefix={<RiseOutlined />}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="利润率"
              value={45.03}
              precision={2}
              suffix="%"
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card className="chart-card" style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary">财务报表</Button>
          <Button>导出账单</Button>
          <Button>结算管理</Button>
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

export default Finance

