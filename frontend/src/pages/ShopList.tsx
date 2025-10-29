import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Space, Modal, Form, Input, Switch, message, Tag, Tooltip } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { shopApi } from '@/services/api'

function ShopList() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingShop, setEditingShop] = useState<any>(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取店铺列表
  const { data: shops, isLoading } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
  })

  // 创建店铺
  const createMutation = useMutation({
    mutationFn: shopApi.createShop,
    onSuccess: () => {
      message.success('店铺创建成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      handleCloseModal()
    },
    onError: () => {
      message.error('店铺创建失败')
    },
  })

  // 更新店铺
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      shopApi.updateShop(id, data),
    onSuccess: () => {
      message.success('店铺更新成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      handleCloseModal()
    },
    onError: () => {
      message.error('店铺更新失败')
    },
  })

  // 删除店铺
  const deleteMutation = useMutation({
    mutationFn: shopApi.deleteShop,
    onSuccess: () => {
      message.success('店铺删除成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
    },
    onError: () => {
      message.error('店铺删除失败')
    },
  })

  const handleOpenModal = (shop?: any) => {
    setEditingShop(shop)
    if (shop) {
      form.setFieldsValue(shop)
    } else {
      form.resetFields()
    }
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingShop(null)
    form.resetFields()
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingShop) {
        updateMutation.mutate({ id: editingShop.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个店铺吗？此操作将同时删除相关的所有订单和商品数据。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(id),
    })
  }


  const columns = [
    {
      title: '店铺ID',
      dataIndex: 'shop_id',
      key: 'shop_id',
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
            <Tag icon={<CheckCircleOutlined />} color="success">
              已授权
            </Tag>
          ) : (
            <Tag icon={<WarningOutlined />} color="warning">
              未授权
            </Tag>
          )}
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 250,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>店铺管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
        >
          添加店铺
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={shops}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingShop ? '编辑店铺' : '添加店铺'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="店铺ID"
            name="shop_id"
            rules={[{ required: true, message: '请输入店铺ID' }]}
          >
            <Input disabled={!!editingShop} />
          </Form.Item>
          <Form.Item
            label="店铺名称"
            name="shop_name"
            rules={[{ required: true, message: '请输入店铺名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="地区"
            name="region"
            rules={[{ required: true, message: '请输入地区' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="经营主体" name="entity">
            <Input />
          </Form.Item>
          <Form.Item label="备注" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          
          {!editingShop && (
            <Form.Item
              label="Access Token"
              name="access_token"
              rules={[{ required: true, message: '请输入Access Token' }]}
              extra="店铺授权后获得的访问令牌，用于数据同步"
            >
              <Input.TextArea 
                rows={3} 
                placeholder="粘贴店铺的Access Token"
              />
            </Form.Item>
          )}
          
          {editingShop && (
            <>
              <Form.Item
                label="Access Token"
                name="access_token"
                extra="如需更新Token，请重新输入；留空表示不修改"
              >
                <Input.TextArea 
                  rows={3} 
                  placeholder="粘贴新的Access Token（可选）"
                />
              </Form.Item>
              <Form.Item
                label="启用状态"
                name="is_active"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </>
          )}
        </Form>
        
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          background: '#f0f2f5', 
          borderRadius: 4 
        }}>
          <p style={{ margin: 0, fontSize: 12, color: '#666' }}>
            💡 提示：App Key和App Secret已在系统设置中全局配置。
            <br />
            添加店铺时只需要填写该店铺的Access Token。
            {!editingShop && (
              <>
                <br />
                如果还没有获取Token，请访问{' '}
                <a 
                  href="https://agentpartner.temu.com/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Temu开放平台
                </a>
                {' '}进行店铺授权。
              </>
            )}
          </p>
        </div>
      </Modal>
    </div>
  )
}

export default ShopList

