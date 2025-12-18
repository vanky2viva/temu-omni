/**
 * 订单表格列定义组件
 */
import { Button, Tag, Tooltip } from 'antd'
import { CopyOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { ProcessedOrder } from '../types'
import { STATUS_COLORS, STATUS_LABELS } from '../constants'
import dayjs from 'dayjs'

interface OrderTableColumnsProps {
  onCopy: (text: string) => void
  onRowClick: (orderId: number) => void
}

export function createOrderTableColumns({
  onCopy,
  onRowClick,
}: OrderTableColumnsProps): ColumnsType<ProcessedOrder> {
  return [
    {
      title: '订单号',
      dataIndex: 'parent_order_sn',
      key: 'parent_order_sn',
      width: 150,
      fixed: 'left' as const,
      align: 'left' as const,
      render: (parentSn: string, record: ProcessedOrder) => {
        const displayValue = parentSn || record.order_sn || '-'

        if (!record._hasParent) {
          return {
            children: (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  justifyContent: 'flex-start',
                }}
                onClick={() => onRowClick(record.id)}
              >
                <span
                  style={{
                    fontFamily: 'monospace',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {displayValue}
                </span>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    onCopy(displayValue)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              </div>
            ),
            props: { rowSpan: 1 },
          }
        }

        if (record._isFirstInGroup && record._groupSize && record._groupSize > 1) {
          return {
            children: (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '12px',
                  justifyContent: 'flex-start',
                }}
              >
                <span
                  style={{
                    fontFamily: 'monospace',
                    fontWeight: 'bold',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {displayValue}
                </span>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    onCopy(displayValue)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              </div>
            ),
            props: { rowSpan: record._groupSize },
          }
        } else if (record._groupSize && record._groupSize > 1) {
          return {
            children: null,
            props: { rowSpan: 0 },
          }
        }
        return {
          children: (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                justifyContent: 'flex-start',
              }}
            >
              <span
                style={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displayValue}
              </span>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                onClick={(e) => {
                  e.stopPropagation()
                  onCopy(displayValue)
                }}
                style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
              />
            </div>
          ),
          props: { rowSpan: 1 },
        }
      },
    },
    {
      title: '子订单号',
      dataIndex: 'order_sn',
      key: 'order_sn',
      width: 150,
      fixed: 'left' as const,
      align: 'left' as const,
      render: (sn: string, record: ProcessedOrder) => {
        if (record._hasParent && record._groupSize && record._groupSize > 1 && !record._isFirstInGroup) {
          return {
            children: null,
            props: { rowSpan: 0 },
          }
        }

        const displaySn = sn || '-'

        return {
          children: (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                justifyContent: 'flex-start',
              }}
            >
              <span
                style={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displaySn}
              </span>
              {sn && (
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    onCopy(sn)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              )}
            </div>
          ),
          props:
            record._hasParent && record._groupSize && record._groupSize > 1 && record._isFirstInGroup
              ? { rowSpan: record._groupSize }
              : { rowSpan: 1 },
        }
      },
    },
    {
      title: '包裹号',
      dataIndex: 'package_sn',
      key: 'package_sn',
      width: 150,
      ellipsis: true,
      align: 'left' as const,
      render: (sn: string, record: ProcessedOrder) => {
        if (record._hasParent && record._groupSize && record._groupSize > 1 && !record._isFirstInGroup) {
          return {
            children: null,
            props: { rowSpan: 0 },
          }
        }

        const displaySn = sn || '-'

        return {
          children: (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                justifyContent: 'flex-start',
              }}
            >
              <span
                style={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displaySn}
              </span>
              {sn && (
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined style={{ fontSize: '12px' }} />}
                  onClick={(e) => {
                    e.stopPropagation()
                    onCopy(sn)
                  }}
                  style={{ padding: '0 4px', minWidth: 'auto', height: '20px', flexShrink: 0 }}
                />
              )}
            </div>
          ),
          props:
            record._hasParent && record._groupSize && record._groupSize > 1 && record._isFirstInGroup
              ? { rowSpan: record._groupSize }
              : { rowSpan: 1 },
        }
      },
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 250,
      ellipsis: true,
      align: 'left' as const,
      render: (text: string) => {
        if (!text) return '-'
        const displayText = text.length > 20 ? text.substring(0, 20) + '...' : text
        return (
          <Tooltip title={text}>
            <span>{displayText}</span>
          </Tooltip>
        )
      },
    },
    {
      title: 'SKU货号',
      dataIndex: 'product_sku',
      key: 'product_sku',
      width: 150,
      align: 'left' as const,
      render: (sku: string) => sku || '-',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'center' as const,
    },
    {
      title: '订单金额',
      dataIndex: 'total_price',
      key: 'total_price',
      width: 120,
      align: 'right' as const,
      render: (price: number | null | undefined) => {
        if (price === null || price === undefined || price === 0) return '-'
        const priceNum = typeof price === 'number' ? price : parseFloat(String(price)) || 0
        return (
          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>¥{priceNum.toFixed(2)}</span>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => {
        const statusKey = status?.toUpperCase() || 'PENDING'
        return <Tag color={STATUS_COLORS[statusKey]}>{STATUS_LABELS[statusKey] || status}</Tag>
      },
    },
    {
      title: '下单时间',
      dataIndex: 'order_time',
      key: 'order_time',
      width: 180,
      align: 'left' as const,
      render: (time: string) => (time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    {
      title: '最晚发货时间',
      dataIndex: 'shipping_time',
      key: 'latest_shipping_time',
      width: 180,
      align: 'left' as const,
      render: (time: string, record: ProcessedOrder) => {
        const displayTime = record._latestShippingTime || time

        if (!displayTime) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize && record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }

        if (record._groupSize && record._groupSize > 1 && record._hasParent) {
          if (record._isFirstInGroup) {
            return {
              children: <div style={{ fontSize: '12px' }}>{dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}</div>,
              props: { rowSpan: record._groupSize },
            }
          } else {
            return {
              children: null,
              props: { rowSpan: 0 },
            }
          }
        }

        return {
          children: <div style={{ fontSize: '12px' }}>{dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}</div>,
          props: { rowSpan: 1 },
        }
      },
    },
    {
      title: '签收时间',
      dataIndex: 'delivery_time',
      key: 'delivery_time',
      width: 180,
      render: (time: string, record: ProcessedOrder) => {
        const isDelivered = record.status === 'DELIVERED'

        if (!isDelivered) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize && record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }

        const displayTime =
          record._groupSize && record._groupSize > 1 && record._hasParent
            ? record._groupDeliveryTime
            : time

        if (!displayTime) {
          return {
            children: <span style={{ color: '#999' }}>-</span>,
            props: {
              rowSpan: record._groupSize && record._groupSize > 1 && record._hasParent ? record._groupSize : 1,
            },
          }
        }

        if (record._groupSize && record._groupSize > 1 && record._hasParent) {
          if (record._isFirstInGroup) {
            return {
              children: <div style={{ fontSize: '12px' }}>{dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}</div>,
              props: { rowSpan: record._groupSize },
            }
          } else {
            return {
              children: null,
              props: { rowSpan: 0 },
            }
          }
        }

        return {
          children: <div style={{ fontSize: '12px' }}>{dayjs(displayTime).format('YYYY-MM-DD HH:mm:ss')}</div>,
          props: { rowSpan: 1 },
        }
      },
    },
  ]
}

