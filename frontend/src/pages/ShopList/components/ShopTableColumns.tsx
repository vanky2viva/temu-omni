import React from 'react'
import { Space, Tag, Tooltip, Button } from 'antd'
import { SyncOutlined, ApiOutlined, UploadOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

interface ShopTableColumnsProps {
  onSync: (record: any) => void
  onAuth: (record: any) => void
  onImport: (record: any) => void
  onEdit: (record: any) => void
  onDelete: (id: number) => void
  syncingShopId: number | null
  isSyncing: boolean
}

export function createShopTableColumns({
  onSync,
  onAuth,
  onImport,
  onEdit,
  onDelete,
  syncingShopId,
  isSyncing,
}: ShopTableColumnsProps): ColumnsType<any> {
  return [
    {
      title: '店铺负责人',
      dataIndex: 'default_manager',
      key: 'default_manager',
      width: 120,
      render: (manager: string) => manager || '-',
    },
    {
      title: '店铺名称',
      dataIndex: 'shop_name',
      key: 'shop_name',
    },
    {
      title: '地区',
      dataIndex: 'region',
      key: 'region',
    },
    {
      title: '经营主体',
      dataIndex: 'entity',
      key: 'entity',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: 'Token状态',
      dataIndex: 'has_api_config',
      key: 'has_api_config',
      render: (hasApiConfig: boolean) => (
        <Tooltip title={hasApiConfig ? '已配置Access Token' : '未配置Token'}>
          {hasApiConfig ? (
            <Tag icon={<CheckCircleOutlined />} color="success">已授权</Tag>
          ) : (
            <Tag icon={<WarningOutlined />} color="warning">未授权</Tag>
          )}
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 460,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="从API同步数据">
            <Button
              type="primary"
              size="small"
              icon={<SyncOutlined spin={syncingShopId === record.id && isSyncing} />}
              onClick={() => onSync(record)}
              loading={syncingShopId === record.id && isSyncing}
            >
              同步
            </Button>
          </Tooltip>
          <Tooltip title={record.has_api_config ? '更新Token' : '设置Token以授权'}>
            <Button
              size="small"
              icon={<ApiOutlined />}
              onClick={() => onAuth(record)}
            >
              {record.has_api_config ? '更新授权' : '授权'}
            </Button>
          </Tooltip>
          <Tooltip title="导入Excel数据">
            <Button
              size="small"
              icon={<UploadOutlined />}
              onClick={() => onImport(record)}
            >
              导入
            </Button>
          </Tooltip>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => onEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => onDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]
}

