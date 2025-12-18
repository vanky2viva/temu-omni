import React from 'react'
import { Row, Col } from 'antd'
import { ShoppingOutlined, InboxOutlined, CheckCircleFilled, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import EnhancedKPICard from '@/components/EnhancedKPICard'
import PercentagePieIcon from '@/components/PercentagePieIcon'
import type { OrderStatusStatistics } from '../types'

interface OrderStatsProps {
  statusStats: OrderStatusStatistics | undefined
  isLoadingStats: boolean
  isMobile: boolean
}

const OrderStats: React.FC<OrderStatsProps> = ({ statusStats, isLoadingStats, isMobile }) => {
  return (
    <div className="order-stats-container">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '总订单数',
              value: statusStats?.total_orders ?? 0,
              trend: statusStats?.trends?.total || [],
              todayChange: statusStats?.today_changes?.total,
              weekChange: statusStats?.week_changes?.total,
              color: '#fa8c16',
              icon: <ShoppingOutlined style={{ fontSize: '20px', color: '#fff' }} />,
              description: '累计订单总数',
            }}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '未发货',
              value: statusStats?.processing ?? 0,
              trend: statusStats?.trends?.processing || [],
              todayChange: statusStats?.today_changes?.processing,
              weekChange: statusStats?.week_changes?.processing,
              color: '#faad14',
              icon: <InboxOutlined style={{ fontSize: '20px', color: '#fff' }} />,
              description: '待处理订单',
            }}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '已发货',
              value: statusStats?.shipped ?? 0,
              trend: [],
              todayChange: statusStats?.today_changes?.shipped,
              showWeekChange: false,
              color: '#58a6ff',
              icon: <CheckCircleFilled style={{ fontSize: '20px', color: '#fff' }} />,
              description: '已发货订单',
            }}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '已送达',
              value: statusStats?.delivered ?? 0,
              trend: [],
              todayChange: statusStats?.today_changes?.delivered,
              showWeekChange: false,
              color: '#52c41a',
              icon: <CheckCircleOutlined style={{ fontSize: '20px', color: '#fff' }} />,
              description: '已完成订单',
            }}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '延误订单',
              value: statusStats?.delayed_orders ?? 0,
              color: '#ff4d4f',
              icon: <WarningOutlined style={{ fontSize: '20px', color: '#fff' }} />,
              description: '需要关注',
            }}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <EnhancedKPICard
            isMobile={isMobile}
            data={{
              loading: isLoadingStats,
              title: '延误率',
              value: statusStats?.delay_rate ?? 0,
              precision: 2,
              suffix: '%',
              color: (statusStats?.delay_rate ?? 0) > 10 ? '#ff4d4f' : '#52c41a',
              icon: (
                <PercentagePieIcon
                  percentage={statusStats?.delay_rate ?? 0}
                  size={36}
                  color={(statusStats?.delay_rate ?? 0) > 10 ? '#ff4d4f' : '#52c41a'}
                  backgroundColor="rgba(255, 255, 255, 0.08)"
                />
              ),
              description: '延误订单占比',
            }}
          />
        </Col>
      </Row>
    </div>
  )
}

export default OrderStats
