import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Space, Modal, Form, Input, Switch, message, Tag, Tooltip } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined, CheckCircleOutlined, WarningOutlined, SyncOutlined, UploadOutlined } from '@ant-design/icons'
import { shopApi, syncApi } from '@/services/api'
import ImportDataModal from '@/components/ImportDataModal'

function ShopList() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingShop, setEditingShop] = useState<any>(null)
  const [form] = Form.useForm()
  const [authForm] = Form.useForm()
  const queryClient = useQueryClient()
  
  // 导入数据模态框
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [importingShop, setImportingShop] = useState<any>(null)

  // 获取店铺列表
  const { data: shops, isLoading } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.message || '店铺列表加载失败'
      message.error(msg)
    },
  })

  // 创建店铺
  const createMutation = useMutation({
    mutationFn: shopApi.createShop,
    onSuccess: () => {
      message.success('店铺创建成功')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      handleCloseModal()
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.message || '店铺创建失败'
      message.error(msg)
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

  // 行级同步loading
  const [syncingShopId, setSyncingShopId] = useState<number | null>(null)

  // 同步数据
  const syncMutation = useMutation({
    mutationFn: ({ shopId, fullSync }: { shopId: number; fullSync: boolean }) =>
      syncApi.syncShopAll(shopId, fullSync),
    onSuccess: (response: any, variables) => {
      message.destroy('sync')
      message.success('数据同步成功！')
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      
      console.log('同步响应:', response)
      
      // 显示同步结果详情
      const results = response?.data?.results || response?.results
      Modal.success({
        title: '✅ 同步完成',
        content: (
          <div>
            <p>店铺数据已同步成功！</p>
            {results && (
              <div style={{ marginTop: 12, padding: 12, background: '#f6f8fa', borderRadius: 4 }}>
                <p style={{ fontWeight: 'bold', marginBottom: 8 }}>同步统计：</p>
                <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
                  {results.orders && (
                    <li>
                      订单: 已有 <strong>{results.orders.total || 0}</strong> 条
                      {results.orders.new > 0 && ` (新增 ${results.orders.new} 条)`}
                      {results.orders.updated > 0 && ` (更新 ${results.orders.updated} 条)`}
                    </li>
                  )}
                  {results.products && (
                    <li>
                      商品: 已有 <strong>{results.products.total || 0}</strong> 条
                      {results.products.new > 0 && ` (新增 ${results.products.new} 条)`}
                      {results.products.updated > 0 && ` (更新 ${results.products.updated} 条)`}
                    </li>
                  )}
                  {results.categories !== undefined && (
                    <li>分类: <strong>{results.categories}</strong> 个</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        ),
      })
    },
    onError: (error: any) => {
      message.destroy('sync')
      console.error('同步错误:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '数据同步失败'
      message.error(errorMsg)
      Modal.error({
        title: '❌ 同步失败',
        content: errorMsg,
      })
    },
    onSettled: () => {
      setSyncingShopId(null)
    },
  })

  // 授权（设置Access Token）
  const [authModalShop, setAuthModalShop] = useState<any>(null)
  const authorizeMutation = useMutation({
    mutationFn: ({ id, token, shopId }: { id: number; token: string; shopId?: string }) => shopApi.authorizeShop(id, token, shopId),
    onSuccess: () => {
      message.success('授权成功')
      authForm.resetFields()
      setAuthModalShop(null)
      queryClient.invalidateQueries({ queryKey: ['shops'] })
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || '授权失败，请检查Token和店铺ID'
      message.error(msg)
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

  const handleSync = (shop: any) => {
    Modal.confirm({
      title: '同步店铺数据',
      content: (
        <div>
          <p>确定要同步店铺 <strong>{shop.shop_name}</strong> 的数据吗？</p>
          <p style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
            将同步最近30天的订单、商品和分类数据。
            <br />
            首次同步可能需要2-5分钟，请耐心等待。
          </p>
        </div>
      ),
      okText: '开始同步',
      cancelText: '取消',
      onOk: () => {
        message.loading({ content: '正在同步数据...', key: 'sync', duration: 0 })
        setSyncingShopId(shop.id)
        syncMutation.mutate({ shopId: shop.id, fullSync: true })
      },
    })
  }

  const handleOpenImportModal = (shop: any) => {
    setImportingShop(shop)
    setIsImportModalOpen(true)
  }

  const handleCloseImportModal = () => {
    setImportingShop(null)
    setIsImportModalOpen(false)
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
      width: 460,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="从API同步数据">
            <Button
              type="primary"
              size="small"
              icon={<SyncOutlined spin={syncingShopId === record.id && syncMutation.isPending} />}
              onClick={() => handleSync(record)}
              loading={syncingShopId === record.id && syncMutation.isPending}
            >
              同步
            </Button>
          </Tooltip>
          <Tooltip title={record.has_api_config ? '更新Token' : '设置Token以授权'}>
            <Button
              size="small"
              icon={<ApiOutlined />}
              onClick={() => {
                setAuthModalShop(record)
                authForm.setFieldsValue({ access_token: '' })
              }}
            >
              {record.has_api_config ? '更新授权' : '授权'}
            </Button>
          </Tooltip>
          <Tooltip title="导入Excel数据">
            <Button
              size="small"
              icon={<UploadOutlined />}
              onClick={() => handleOpenImportModal(record)}
            >
              导入
            </Button>
          </Tooltip>
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
          {/* 创建时不再填写店铺ID，授权时绑定 */}
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
            rules={[{ required: true, message: '请选择地区' }]}
          >
            <select style={{ width: '100%', height: 32, borderRadius: 6, border: '1px solid #d9d9d9' }}>
              <option value="us">US（美国）</option>
              <option value="eu">EU（欧洲）</option>
              <option value="global">GLOBAL（全球）</option>
            </select>
          </Form.Item>
          <Form.Item label="经营主体" name="entity">
            <Input />
          </Form.Item>
          <Form.Item label="负责人" name="default_manager" extra="默认将该店铺下新增/导入的商品绑定到此负责人">
            <Input placeholder="请输入负责人姓名或工号" />
          </Form.Item>
          <Form.Item label="备注" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          
          {/* 新增店铺时Access Token不再必填，移除必填校验并默认隐藏 */}
          
          {editingShop && (
            <>
              <Form.Item
                label="Access Token"
                name="access_token"
                extra="如需更新Token，请通过“授权/更新授权”按钮设置；此处留空表示不修改"
              >
                <Input.TextArea rows={3} placeholder="（建议使用授权按钮设置）" />
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
            添加店铺时无需填写 Access Token，可在列表中点击“授权”按钮后设置。
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

      {/* 导入数据模态框 */}
      {importingShop && (
        <ImportDataModal
          visible={isImportModalOpen}
          shopId={importingShop.id}
          shopName={importingShop.shop_name}
          onClose={handleCloseImportModal}
        />
      )}

      {/* 授权模态框 */}
      <Modal
        title={authModalShop ? `授权店铺：${authModalShop.shop_name}` : '授权店铺'}
        open={!!authModalShop}
        onOk={async () => {
          try {
            const values = await authForm.validateFields()
            authorizeMutation.mutate({ id: authModalShop.id, token: values.access_token, shopId: values.shop_id })
          } catch (e) {}
        }}
        onCancel={() => {
          setAuthModalShop(null)
          authForm.resetFields()
        }}
        confirmLoading={authorizeMutation.isPending}
     >
        <Form form={authForm} layout="vertical">
          <Form.Item
            label="Temu店铺ID"
            name="shop_id"
            rules={[{ required: true, message: '请输入Temu店铺ID' }]}
            extra="授权时绑定平台店铺ID，用于后续同步识别"
          >
            <Input placeholder="例如：635517726820718" />
          </Form.Item>
          <Form.Item
            label="Access Token"
            name="access_token"
            rules={[{ required: true, message: '请输入Access Token' }]}
            extra="授权店铺所需的访问令牌。将用于调用Temu API进行数据同步。"
          >
            <Input.TextArea rows={3} placeholder="粘贴该店铺的Access Token" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ShopList

