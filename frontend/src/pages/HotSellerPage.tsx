import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Select, Space, Table, Modal, Row, Col, Statistic, Tag, Avatar, Badge } from 'antd'
import { CrownOutlined, ShoppingOutlined } from '@ant-design/icons'
import LazyECharts from '@/components/LazyECharts'
import { shopApi } from '@/services/api'
import axios from 'axios'
import dayjs from 'dayjs'

function HotSellerPage() {
  const [isMobile, setIsMobile] = useState(false)

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  const currentDate = dayjs()
  const [year, setYear] = useState(currentDate.year())
  const [month, setMonth] = useState(currentDate.month() + 1)
  const [selectedShops, setSelectedShops] = useState<number[]>([])
  const [selectedManager, setSelectedManager] = useState<any>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 获取爆单榜数据
  const { data: rankingData, isLoading } = useQuery({
    queryKey: ['hot-seller-ranking', year, month, selectedShops],
    queryFn: async () => {
      const params: any = { year, month }
      if (selectedShops.length > 0) {
        params.shop_ids = selectedShops
      }
      const response = await axios.get('/api/analytics/hot-seller-ranking', { params })
      return response.data
    },
  })

  // 获取负责人的SKU详情
  const { data: managerSkus, isLoading: skuLoading } = useQuery({
    queryKey: ['manager-skus', selectedManager?.manager, year, month],
    queryFn: async () => {
      if (!selectedManager) return null
      const params: any = { 
        manager: selectedManager.manager,
        year,
        month
      }
      const response = await axios.get('/api/analytics/manager-sku-details', { params })
      return response.data
    },
    enabled: !!selectedManager,
  })

  // 生成年份选项
  const yearOptions = []
  for (let y = currentDate.year(); y >= currentDate.year() - 2; y--) {
    yearOptions.push({ label: `${y}年`, value: y })
  }

  // 月份选项
  const monthOptions = []
  for (let m = 1; m <= 12; m++) {
    monthOptions.push({ label: `${m}月`, value: m })
  }

  // 获取奖牌图标
  const getMedalIcon = (rank: number) => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return null
  }

  // 获取排名颜色
  const getRankColor = (rank: number) => {
    if (rank === 1) return '#FFD700'
    if (rank === 2) return '#C0C0C0'
    if (rank === 3) return '#CD7F32'
    return '#1890ff'
  }

  const handleRowClick = (record: any) => {
    setSelectedManager(record)
    setIsDetailModalOpen(true)
  }

  // 排行榜表格列
  const rankingColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => (
        <Space>
          {getMedalIcon(rank) && <span style={{ fontSize: 20 }}>{getMedalIcon(rank)}</span>}
          <Badge 
            count={rank} 
            style={{ 
              backgroundColor: getRankColor(rank),
              fontSize: 14,
            }}
          />
        </Space>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 120,
      render: (manager: string, record: any) => (
        <Space>
          <Avatar style={{ backgroundColor: getRankColor(record.rank) }}>
            {manager.charAt(0)}
          </Avatar>
          <span style={{ fontWeight: 'bold' }}>{manager}</span>
        </Space>
      ),
    },
    {
      title: '店铺',
      dataIndex: 'shop',
      key: 'shop',
      width: 150,
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 130,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.gmv - b.gmv,
      render: (val: number) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          ${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.orders - b.orders,
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.quantity - b.quantity,
      render: (val: number) => `${val} 件`,
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 130,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.profit - b.profit,
      render: (val: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          ${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      title: '客单价',
      dataIndex: 'avg_order_value',
      key: 'avg_order_value',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.avg_order_value - b.avg_order_value,
      render: (val: number) => `$${val.toFixed(2)}`,
    },
  ]

  // SKU详情表格列
  const skuColumns = [
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '销量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.quantity - b.quantity,
      render: (val: number) => `${val} 件`,
    },
    {
      title: '订单数',
      dataIndex: 'orders',
      key: 'orders',
      width: 100,
      align: 'right' as const,
    },
    {
      title: 'GMV',
      dataIndex: 'gmv',
      key: 'gmv',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.gmv - b.gmv,
      render: (val: number) => `$${val.toFixed(2)}`,
    },
    {
      title: '利润',
      dataIndex: 'profit',
      key: 'profit',
      width: 120,
      align: 'right' as const,
      sorter: (a: any, b: any) => a.profit - b.profit,
      render: (val: number) => (
        <span style={{ color: val >= 0 ? '#52c41a' : '#ff4d4f' }}>
          ${val.toFixed(2)}
        </span>
      ),
    },
  ]

  // GMV趋势图配置
  const gmvChartOption = {
    title: {
      text: 'GMV排行榜',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: 'GMV (CNY)',
    },
    yAxis: {
      type: 'category',
      data: rankingData?.ranking?.slice(0, 10).map((item: any) => item.manager).reverse() || [],
    },
    series: [
      {
        name: 'GMV',
        type: 'bar',
        data: rankingData?.ranking?.slice(0, 10).map((item: any) => item.gmv).reverse() || [],
        itemStyle: {
          color: (params: any) => {
            const colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#1890ff']
            const rank = 10 - params.dataIndex
            return rank <= 3 ? colors[rank - 1] : colors[3]
          },
        },
        label: {
          show: true,
          position: 'right',
          formatter: (params: any) => `$${params.value.toFixed(0)}`,
        },
      },
    ],
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: isMobile ? '18px' : '24px' }}>
        <CrownOutlined style={{ color: '#faad14', marginRight: 8 }} />
        爆单榜
      </h2>

      {/* 筛选条件 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size={isMobile ? "small" : "middle"} wrap direction={isMobile ? "vertical" : "horizontal"}>
          <span>统计周期：</span>
          <Select
            value={year}
            onChange={setYear}
            style={{ width: 100 }}
            options={yearOptions}
          />
          <Select
            value={month}
            onChange={setMonth}
            style={{ width: 80 }}
            options={monthOptions}
          />

          <span>店铺筛选：</span>
          <Select
            mode="multiple"
            style={{ minWidth: 200 }}
            placeholder="全部店铺"
            allowClear
            value={selectedShops}
            onChange={setSelectedShops}
            options={shops?.map((shop: any) => ({
              label: shop.shop_name,
              value: shop.id,
            }))}
          />
        </Space>
      </Card>

      {/* 前三名卡片展示 */}
      {rankingData?.ranking && rankingData.ranking.length > 0 && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {rankingData.ranking.slice(0, 3).map((item: any) => (
            <Col xs={24} sm={12} md={8} lg={8} key={item.rank}>
              <Card
                hoverable
                onClick={() => handleRowClick(item)}
                style={{
                  borderColor: getRankColor(item.rank),
                  borderWidth: 2,
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 40, marginBottom: 8 }}>
                    {getMedalIcon(item.rank)}
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
                    {item.manager}
                  </div>
                  <Tag color="blue">{item.shop}</Tag>
                  <Row gutter={8} style={{ marginTop: 16 }}>
                    <Col span={12}>
                      <Statistic
                        title="GMV"
                        value={item.gmv}
                        precision={0}
                        prefix="$"
                        valueStyle={{ fontSize: 16, color: getRankColor(item.rank) }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="订单"
                        value={item.orders}
                        suffix="单"
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Col>
                  </Row>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* GMV图表 */}
      <Card style={{ marginBottom: 16 }}>
        <LazyECharts option={gmvChartOption} style={{ height: isMobile ? 300 : 400 }} />
      </Card>

      {/* 完整排行榜表格 */}
      <Card title="完整排行榜（点击查看详情）">
        <Table
          columns={rankingColumns}
          dataSource={rankingData?.ranking}
          rowKey={(record) => `${record.manager}-${record.shop}`}
          loading={isLoading}
          onRow={(record) => ({
            onClick: () => handleRowClick(record),
            style: { cursor: 'pointer' },
          })}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 位负责人`,
          }}
        />
      </Card>

      {/* 负责人SKU详情模态框 */}
      <Modal
        title={
          <Space>
            <Avatar style={{ backgroundColor: '#1890ff' }}>
              {selectedManager?.manager?.charAt(0)}
            </Avatar>
            <span>{selectedManager?.manager} 的SKU销售详情</span>
            <Tag color="blue">{selectedManager?.shop}</Tag>
          </Space>
        }
        open={isDetailModalOpen}
        onCancel={() => setIsDetailModalOpen(false)}
        width={900}
        footer={null}
      >
        {/* 汇总统计 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总GMV"
                value={selectedManager?.gmv || 0}
                precision={2}
                prefix={<ShoppingOutlined />}
                suffix="CNY"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总订单"
                value={selectedManager?.orders || 0}
                prefix={<ShoppingOutlined />}
                suffix="单"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总销量"
                value={selectedManager?.quantity || 0}
                suffix="件"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总利润"
                value={selectedManager?.profit || 0}
                precision={2}
                prefix="$"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>

        {/* SKU详情表格 */}
        <Table
          columns={skuColumns}
          dataSource={managerSkus}
          rowKey="sku"
          loading={skuLoading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 个SKU`,
          }}
        />
      </Modal>
    </div>
  )
}

export default HotSellerPage
