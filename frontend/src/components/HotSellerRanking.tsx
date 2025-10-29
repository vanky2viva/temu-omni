import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Select, Space, List, Avatar, Statistic, Row, Col, Badge } from 'antd'
import { CrownOutlined, TrophyOutlined, DollarOutlined } from '@ant-design/icons'
import { shopApi } from '@/services/api'
import axios from 'axios'
import dayjs from 'dayjs'

function HotSellerRanking() {
  const currentDate = dayjs()
  const [year, setYear] = useState(currentDate.year())
  const [month, setMonth] = useState(currentDate.month() + 1)
  const [selectedShops, setSelectedShops] = useState<number[]>([])

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
    if (rank === 1) return <TrophyOutlined style={{ color: '#FFD700', fontSize: 24 }} />
    if (rank === 2) return <TrophyOutlined style={{ color: '#C0C0C0', fontSize: 22 }} />
    if (rank === 3) return <TrophyOutlined style={{ color: '#CD7F32', fontSize: 20 }} />
    return null
  }

  // 获取排名颜色
  const getRankColor = (rank: number) => {
    if (rank === 1) return '#FFD700'
    if (rank === 2) return '#C0C0C0'
    if (rank === 3) return '#CD7F32'
    return '#666'
  }

  return (
    <Card
      title={
        <Space>
          <CrownOutlined style={{ color: '#faad14' }} />
          <span>爆单榜</span>
        </Space>
      }
      extra={
        <Space size="small">
          <Select
            size="small"
            value={year}
            onChange={setYear}
            style={{ width: 80 }}
            options={yearOptions}
          />
          <Select
            size="small"
            value={month}
            onChange={setMonth}
            style={{ width: 70 }}
            options={monthOptions}
          />
        </Space>
      }
      style={{ height: '100%' }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 店铺筛选 */}
        <Select
          mode="multiple"
          size="small"
          style={{ width: '100%' }}
          placeholder="全部店铺"
          allowClear
          value={selectedShops}
          onChange={setSelectedShops}
          options={shops?.map((shop: any) => ({
            label: shop.shop_name,
            value: shop.id,
          }))}
        />

        {/* 排行榜列表 */}
        <List
          loading={isLoading}
          dataSource={rankingData?.ranking || []}
          renderItem={(item: any) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Badge count={getMedalIcon(item.rank) || item.rank} style={{ backgroundColor: getRankColor(item.rank) }}>
                    <Avatar
                      style={{
                        backgroundColor: item.rank <= 3 ? getRankColor(item.rank) : '#1890ff',
                        fontSize: 16,
                      }}
                    >
                      {item.manager.charAt(0)}
                    </Avatar>
                  </Badge>
                }
                title={
                  <Space>
                    <span style={{ fontWeight: 'bold' }}>{item.manager}</span>
                    <span style={{ fontSize: 12, color: '#999' }}>({item.shop})</span>
                  </Space>
                }
                description={
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Statistic
                          title="GMV"
                          value={item.gmv}
                          precision={0}
                          valueStyle={{ fontSize: 14 }}
                          prefix="$"
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="订单"
                          value={item.orders}
                          valueStyle={{ fontSize: 14 }}
                          suffix="单"
                        />
                      </Col>
                    </Row>
                    <div style={{ fontSize: 12, color: '#52c41a' }}>
                      利润: ${item.profit.toFixed(0)} | 客单价: ${item.avg_order_value}
                    </div>
                  </Space>
                }
              />
            </List.Item>
          )}
        />

        {(!rankingData?.ranking || rankingData.ranking.length === 0) && !isLoading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            当前周期暂无数据
          </div>
        )}
      </Space>
    </Card>
  )
}

export default HotSellerRanking

