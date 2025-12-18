import React from 'react'
import { Table as AntTable, TableProps as AntTableProps } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import './styles.css'

export interface UnifiedTableProps<T = any> extends Omit<AntTableProps<T>, 'className'> {
  /**
   * 表格变体样式
   * - default: 默认样式
   * - order-list: 订单列表样式
   * - compact: 紧凑样式
   * - profit-statement: 利润表样式
   */
  variant?: 'default' | 'order-list' | 'compact' | 'profit-statement'
  /**
   * 是否启用移动端优化
   */
  isMobile?: boolean
  /**
   * 自定义类名
   */
  className?: string
}

/**
 * 统一的表格组件
 * 封装了项目中常用的表格样式和配置
 */
function UnifiedTable<T extends Record<string, any> = any>({
  variant = 'default',
  isMobile = false,
  className = '',
  size,
  scroll,
  pagination,
  ...props
}: UnifiedTableProps<T>) {
  // 根据变体生成类名
  const variantClass = `unified-table-${variant}`
  const finalClassName = `unified-table ${variantClass} ${className}`.trim()

  // 移动端优化：自动调整size和scroll
  const finalSize = size || (isMobile ? 'small' : 'middle')
  const finalScroll = scroll || (isMobile ? { x: 'max-content' } : undefined)

  // 移动端优化：简化分页
  const finalPagination = pagination !== false
    ? {
        ...pagination,
        showSizeChanger: isMobile ? false : (pagination as any)?.showSizeChanger ?? true,
        showQuickJumper: isMobile ? false : (pagination as any)?.showQuickJumper ?? false,
        showLessItems: isMobile ? true : (pagination as any)?.showLessItems ?? false,
        simple: isMobile ? true : (pagination as any)?.simple ?? false,
      }
    : false

  return (
    <AntTable<T>
      {...props}
      className={finalClassName}
      size={finalSize}
      scroll={finalScroll}
      pagination={finalPagination}
    />
  )
}

export default UnifiedTable
export type { ColumnsType }

