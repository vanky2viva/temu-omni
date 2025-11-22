/**订单详情Drawer组件*/
import { Drawer, Descriptions, Card, Tag, Timeline, Space, Button, Input, message, Empty, Image, Spin } from 'antd'
import { CopyOutlined, CloseOutlined, PlusOutlined, CheckOutlined, ExclamationCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { orderApi } from '@/services/api'
import dayjs from 'dayjs'
import { useState, useEffect } from 'react'

const { TextArea } = Input

interface OrderDetailDrawerProps {
  visible: boolean
  orderId: number | null
  onClose: () => void
}

export default function OrderDetailDrawer({ visible, orderId, onClose }: OrderDetailDrawerProps) {
  const [editingNote, setEditingNote] = useState(false)
  const [noteContent, setNoteContent] = useState('')
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
  
  // 获取订单详情
  const { data: orderDetail, isLoading } = useQuery({
    queryKey: ['order-detail', orderId],
    queryFn: async () => {
      if (!orderId) return null
      // 暂时使用getOrder API，后续可以添加专门的详情API
      const result = await orderApi.getOrder(orderId)
      return result
    },
    enabled: visible && !!orderId,
    staleTime: 30000,
  })
  
  // 复制到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }
  
  // 计算延误信息
  const getDelayInfo = (order: any) => {
    if (!order) return null
    
    const now = dayjs()
    let latestDeliveryTime = null
    
    // 优先使用latestDeliveryTime
    if (order.raw_data?.latestDeliveryTime) {
      latestDeliveryTime = dayjs(order.raw_data.latestDeliveryTime)
    } else if (order.expect_ship_latest_time) {
      latestDeliveryTime = dayjs(order.expect_ship_latest_time).add(14, 'day')
    } else if (order.order_time) {
      latestDeliveryTime = dayjs(order.order_time).add(21, 'day')
    }
    
    if (!latestDeliveryTime) return null
    
    const hoursRemaining = latestDeliveryTime.diff(now, 'hour')
    const isDelayed = now.isAfter(latestDeliveryTime)
    
    return {
      latestDeliveryTime,
      hoursRemaining,
      isDelayed,
      statusText: isDelayed ? '已延误' : hoursRemaining > 48 ? '正常' : '即将延误'
    }
  }
  
  const delayInfo = getDelayInfo(orderDetail)
  
  // 获取物流时间线
  const getLogisticsTimeline = (order: any) => {
    if (!order) return []
    
    const timeline: any[] = []
    
    // 发货时间
    if (order.ship_time) {
      timeline.push({
        color: 'green',
        status: '已发货',
        time: order.ship_time,
        description: `物流单号: ${order.tracking_number || '暂无'}`,
      })
    }
    
    // 清关时间（从raw_data获取）
    if (order.raw_data?.clearanceTime) {
      timeline.push({
        color: 'blue',
        status: '已清关',
        time: order.raw_data.clearanceTime,
      })
    }
    
    // 派送时间（从raw_data获取）
    if (order.raw_data?.deliveryTime) {
      timeline.push({
        color: 'orange',
        status: '派送中',
        time: order.raw_data.deliveryTime,
      })
    }
    
    // 签收时间
    if (order.delivery_time) {
      timeline.push({
        color: 'gray',
        status: '已签收',
        time: order.delivery_time,
      })
    } else if (order.status === 'DELIVERED') {
      timeline.push({
        color: 'gray',
        status: '已签收',
        time: order.updated_at,
      })
    }
    
    return timeline
  }
  
  const logisticsTimeline = getLogisticsTimeline(orderDetail)
  
  // 状态标签颜色
  const statusColors: Record<string, string> = {
    PENDING: 'default',
    PROCESSING: 'processing',
    SHIPPED: 'warning',
    DELIVERED: 'success',
    CANCELLED: 'error',
  }
  
  const statusLabels: Record<string, string> = {
    PENDING: '待处理',
    PROCESSING: '未发货',
    SHIPPED: '已发货',
    DELIVERED: '已送达',
    CANCELLED: '已取消',
  }
  
  return (
    <Drawer
      title="订单详情"
      placement="right"
      width={isMobile ? '100%' : 600}
      onClose={onClose}
      open={visible}
      extra={
        <Button type="text" icon={<CloseOutlined />} onClick={onClose} />
      }
      destroyOnClose
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
        </div>
      ) : !orderDetail ? (
        <Empty description="订单不存在" />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 订单基础信息 */}
          <Card title="订单信息" size="small">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="订单号">
                <Space>
                  <span style={{ fontFamily: 'monospace' }}>{orderDetail.parent_order_sn || orderDetail.order_sn}</span>
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(orderDetail.parent_order_sn || orderDetail.order_sn)}
                  />
                </Space>
              </Descriptions.Item>
              {orderDetail.order_sn && orderDetail.order_sn !== orderDetail.parent_order_sn && (
                <Descriptions.Item label="子订单号">
                  <Space>
                    <span style={{ fontFamily: 'monospace' }}>{orderDetail.order_sn}</span>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(orderDetail.order_sn)}
                    />
                  </Space>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="订单状态">
                <Tag color={statusColors[orderDetail.status] || 'default'}>
                  {statusLabels[orderDetail.status] || orderDetail.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="店铺">
                {orderDetail.shop?.shop_name || '未知店铺'}
              </Descriptions.Item>
              <Descriptions.Item label="下单时间">
                {orderDetail.order_time ? dayjs(orderDetail.order_time).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              {orderDetail.pay_time && (
                <Descriptions.Item label="付款时间">
                  {dayjs(orderDetail.pay_time).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="金额">
                {orderDetail.currency || 'USD'} {orderDetail.total_price?.toFixed(2) || '0.00'}
              </Descriptions.Item>
              {orderDetail.quantity && (
                <Descriptions.Item label="数量">
                  {orderDetail.quantity}
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
          
          {/* 商品信息 */}
          <Card title="商品信息" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {orderDetail.product_image && (
                <Image
                  src={orderDetail.product_image}
                  alt={orderDetail.product_name}
                  width={100}
                  height={100}
                  style={{ objectFit: 'cover', borderRadius: '4px' }}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                />
              )}
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{orderDetail.product_name || '-'}</div>
                {orderDetail.product_sku && (
                  <div style={{ color: '#999', fontSize: '12px', marginBottom: '4px' }}>
                    SKU: {orderDetail.product_sku}
                  </div>
                )}
                {orderDetail.quantity && (
                  <div style={{ marginTop: '8px' }}>
                    <span>数量: {orderDetail.quantity}</span>
                    {orderDetail.unit_price && (
                      <span style={{ marginLeft: '16px' }}>
                        单价: {orderDetail.currency || 'USD'} {orderDetail.unit_price.toFixed(2)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Space>
          </Card>
          
          {/* 物流信息 */}
          {logisticsTimeline.length > 0 && (
            <Card title="物流信息" size="small">
              <Timeline
                items={logisticsTimeline.map((item: any) => ({
                  color: item.color,
                  children: (
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{item.status}</div>
                      <div style={{ color: '#999', fontSize: '12px' }}>
                        {dayjs(item.time).format('YYYY-MM-DD HH:mm:ss')}
                      </div>
                      {item.description && (
                        <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                          {item.description}
                        </div>
                      )}
                    </div>
                  ),
                }))}
              />
            </Card>
          )}
          
          {/* 履约风险信息 */}
          {delayInfo && (
            <Card title="履约风险" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                {delayInfo.isDelayed ? (
                  <div style={{ color: '#ff4d4f' }}>
                    <ExclamationCircleOutlined style={{ marginRight: '8px' }} />
                    已延误
                  </div>
                ) : delayInfo.hoursRemaining <= 48 ? (
                  <div style={{ color: '#faad14' }}>
                    <ClockCircleOutlined style={{ marginRight: '8px' }} />
                    距离最晚发货还有 {delayInfo.hoursRemaining} 小时
                  </div>
                ) : (
                  <div style={{ color: '#52c41a' }}>
                    <CheckOutlined style={{ marginRight: '8px' }} />
                    当前未延误
                  </div>
                )}
                <div style={{ color: '#999', fontSize: '12px' }}>
                  最晚送达时间: {delayInfo.latestDeliveryTime.format('YYYY-MM-DD HH:mm:ss')}
                </div>
              </Space>
            </Card>
          )}
          
          {/* 备注和标签 */}
          <Card 
            title="备注和标签" 
            size="small"
            extra={
              <Button
                type="text"
                size="small"
                icon={editingNote ? <CheckOutlined /> : <PlusOutlined />}
                onClick={() => {
                  if (editingNote && noteContent.trim()) {
                    // TODO: 保存备注
                    message.success('备注已保存')
                    setEditingNote(false)
                    setNoteContent('')
                  } else {
                    setEditingNote(true)
                  }
                }}
              />
            }
          >
            {editingNote ? (
              <TextArea
                placeholder="请输入备注..."
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                rows={3}
                autoFocus
              />
            ) : (
              <Empty description="暂无备注" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Space>
      )}
    </Drawer>
  )
}

