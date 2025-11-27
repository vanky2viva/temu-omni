import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Space, Modal, Form, Input, Switch, message, Tag, Tooltip, Select, Progress, Descriptions, Card, Typography } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined, CheckCircleOutlined, WarningOutlined, SyncOutlined, UploadOutlined } from '@ant-design/icons'
import { shopApi, syncApi } from '@/services/api'
import ImportDataModal from '@/components/ImportDataModal'

const { Text } = Typography

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
  const { data: shops, isLoading, error: shopsError } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0, // 禁用缓存，总是获取最新数据
  })
  
  // 处理错误
  useEffect(() => {
    if (shopsError) {
      const error: any = shopsError
      const msg = error?.response?.data?.detail || error?.message || '店铺列表加载失败'
      message.error(msg)
    }
  }, [shopsError])

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
      // 清除所有相关查询缓存并重新获取
      queryClient.invalidateQueries({ queryKey: ['shops'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.message || '店铺删除失败'
      message.error(msg)
      console.error('删除店铺错误:', error)
    },
  })

  // 行级同步loading和进度
  const [syncingShopId, setSyncingShopId] = useState<number | null>(null)
  const [syncProgress, setSyncProgress] = useState<any>(null)
  const [syncProgressModalVisible, setSyncProgressModalVisible] = useState(false)
  const [syncLogs, setSyncLogs] = useState<any[]>([])
  const progressIntervalRef = useRef<number | null>(null)
  const logScrollRef = useRef<HTMLDivElement>(null)

  // 同步数据
  const syncMutation = useMutation({
    mutationFn: ({ shopId, fullSync }: { shopId: number; fullSync: boolean }) =>
      syncApi.syncShopAll(shopId, fullSync),
    onSuccess: (response: any) => {
      // 启动进度轮询
      setSyncingShopId(response?.data?.shop_id)
      setSyncProgressModalVisible(true)
      startProgressPolling(response?.data?.shop_id)
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
      setSyncingShopId(null)
    },
  })

  // 轮询同步进度
  const startProgressPolling = (shopId: number) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
    }
    
    // 立即查询一次进度和日志
    const fetchProgressAndLogs = async () => {
      try {
        const [progressResponse, logsResponse] = await Promise.all([
          syncApi.getSyncProgress(shopId),
          syncApi.getSyncLogs(shopId, 50)
        ])
        const progress = progressResponse?.data || progressResponse
        const logs = logsResponse?.data || []
        setSyncProgress(progress)
        setSyncLogs(logs)
        // 自动滚动到顶部（最新日志在前）
        setTimeout(() => {
          if (logScrollRef.current) {
            logScrollRef.current.scrollTop = 0
          }
        }, 100)
      } catch (error) {
        console.error('获取进度或日志失败:', error)
      }
    }
    
    fetchProgressAndLogs()
    
    // 每1秒查询一次进度和日志
    progressIntervalRef.current = window.setInterval(async () => {
      try {
        const [progressResponse, logsResponse] = await Promise.all([
          syncApi.getSyncProgress(shopId),
          syncApi.getSyncLogs(shopId, 50)
        ])
        const progress = progressResponse?.data || progressResponse
        const logs = logsResponse?.data || []
        setSyncProgress(progress)
        setSyncLogs(logs)
        // 自动滚动到顶部（最新日志在前）
        setTimeout(() => {
          if (logScrollRef.current) {
            logScrollRef.current.scrollTop = 0
          }
        }, 100)
        
        // 如果同步完成或失败，停止轮询
        const status = progress?.status
        if (status === 'completed' || status === 'error') {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current)
            progressIntervalRef.current = null
          }
          
          // 刷新数据
          queryClient.invalidateQueries({ queryKey: ['shops'] })
          queryClient.invalidateQueries({ queryKey: ['statistics'] })
          queryClient.invalidateQueries({ queryKey: ['orders'] })
          queryClient.invalidateQueries({ queryKey: ['products'] })
          
          setSyncingShopId(null)
          
          // 显示结果
          if (status === 'completed') {
            let successMsg = '数据同步完成！\n\n'
            
            // 订单同步结果
            if (progress.orders) {
              if (progress.orders.error) {
                successMsg += `❌ 订单同步失败: ${progress.orders.error}\n`
              } else {
                const orderTotal = progress.orders.total || 0
                const orderNew = progress.orders.new || 0
                const orderUpdated = progress.orders.updated || 0
                const orderFailed = progress.orders.failed || 0
                if (orderTotal > 0 || orderNew > 0 || orderUpdated > 0) {
                  successMsg += `✅ 订单：获取 ${orderTotal} 条，新增 ${orderNew} 条，更新 ${orderUpdated} 条`
                  if (orderFailed > 0) {
                    successMsg += `，失败 ${orderFailed} 条`
              }
              successMsg += '\n'
                } else {
                  successMsg += `ℹ️ 订单：无新数据\n`
                }
              }
            } else {
              successMsg += `ℹ️ 订单：未执行\n`
            }
            
            // 商品同步结果
            if (progress.products) {
              if (progress.products.error) {
                successMsg += `❌ 商品同步失败: ${progress.products.error}\n`
              } else {
                const productTotal = progress.products.total || 0
                const productNew = progress.products.new || 0
                const productUpdated = progress.products.updated || 0
                const productFailed = progress.products.failed || 0
                if (productTotal > 0 || productNew > 0 || productUpdated > 0) {
                  successMsg += `✅ 商品：获取 ${productTotal} 条，新增 ${productNew} 条，更新 ${productUpdated} 条`
                  if (productFailed > 0) {
                    successMsg += `，失败 ${productFailed} 条`
                  }
                  successMsg += '\n'
                } else {
                  successMsg += `ℹ️ 商品：无新数据\n`
                }
              }
            } else {
              successMsg += `ℹ️ 商品：未执行\n`
            }
            
            // 分类同步结果
            if (progress.categories !== undefined) {
              if (typeof progress.categories === 'object' && progress.categories?.error) {
                successMsg += `❌ 分类同步失败: ${progress.categories.error}`
              } else {
                const categoryCount = typeof progress.categories === 'number' ? progress.categories : 0
                successMsg += `✅ 分类：同步 ${categoryCount} 个分类`
              }
            }
            
            message.success({
              content: successMsg,
              duration: 5, // 显示5秒
            })
            
            // 不自动关闭，让用户手动关闭以查看详细结果和日志
          } else {
            message.error({
              content: `同步失败: ${progress?.error || '未知错误'}`,
              duration: 5,
            })
            // 不自动关闭，让用户手动关闭以查看详细错误信息
          }
        }
      } catch (error) {
        console.error('获取进度失败:', error)
      }
    }, 500) // 每500ms轮询一次，更快地更新进度
  }

  // 清理轮询
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [])

  // 监听模态框关闭，清除残留的遮罩层
  useEffect(() => {
    if (!syncProgressModalVisible) {
      // 模态框关闭后，清除可能残留的遮罩层
      const timer = setTimeout(() => {
        // 清除所有残留的遮罩层
        const masks = document.querySelectorAll('.ant-modal-mask')
        masks.forEach((mask) => {
          mask.remove()
        })
        // 清除可能残留的模态框容器
        const wrappers = document.querySelectorAll('.ant-modal-wrap')
        wrappers.forEach((wrapper) => {
          if (!wrapper.querySelector('.ant-modal')) {
            wrapper.remove()
          }
        })
        // 清除body上的样式
        document.body.style.overflow = ''
        document.body.style.paddingRight = ''
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [syncProgressModalVisible])

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

  const handleOpenModal = async (shop?: any) => {
    setEditingShop(shop)
    if (shop) {
      // 编辑时，获取完整的店铺信息（包含 access_token 等敏感字段）
      try {
        const shopDetail: any = await shopApi.getShop(shop.id)
        // 保存原始值，用于判断是否修改
        const originalValues = {
          access_token: shopDetail.access_token || '',
          cn_access_token: shopDetail.cn_access_token || '',
        }
        // 将原始值存储到表单的隐藏字段中，用于后续比较
        form.setFieldsValue({
          ...shopDetail,
          access_token: originalValues.access_token,
          cn_access_token: originalValues.cn_access_token,
          _original_access_token: originalValues.access_token, // 保存原始值用于比较
          _original_cn_access_token: originalValues.cn_access_token, // 保存原始值用于比较
        })
      } catch (error) {
        // 如果获取详情失败，使用列表中的数据
        const originalValues = {
          access_token: shop.access_token || '',
          cn_access_token: shop.cn_access_token || '',
        }
        form.setFieldsValue({
          ...shop,
          access_token: originalValues.access_token,
          cn_access_token: originalValues.cn_access_token,
          _original_access_token: originalValues.access_token,
          _original_cn_access_token: originalValues.cn_access_token,
        })
      }
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
      
      // 处理敏感字段：如果值没有变化，不更新该字段
      if (editingShop) {
        const originalAccessToken = values._original_access_token || ''
        const originalCnAccessToken = values._original_cn_access_token || ''
        
        // 如果值没有变化，删除该字段（不更新）
        if (values.access_token === originalAccessToken) {
          delete values.access_token
        } else if (values.access_token === '') {
          // 如果是空字符串，表示用户要清空该字段
          values.access_token = null
        }
        
        if (values.cn_access_token === originalCnAccessToken) {
          delete values.cn_access_token
        } else if (values.cn_access_token === '') {
          // 如果是空字符串，表示用户要清空该字段
          values.cn_access_token = null
        }
        
        // 删除用于比较的隐藏字段
        delete values._original_access_token
        delete values._original_cn_access_token
        
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
    if (!shop.has_api_config) {
      message.warning('请先配置店铺的 Access Token')
      return
    }
    
    // 检查是否有历史数据，决定同步模式
    const hasHistoryData = shop.last_sync_at
    
    Modal.confirm({
      title: '同步店铺数据',
      content: (
        <div>
          <p>确定要同步店铺 <strong>{shop.shop_name}</strong> 的数据吗？</p>
          <p style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
            {hasHistoryData ? (
              <>
                <strong>全量同步模式：</strong>将同步所有订单和商品数据。
                <br />
                系统会自动识别新增和更新的数据。
              </>
            ) : (
              <>
                <strong>首次同步：</strong>将同步所有订单和商品数据。
                <br />
                后续同步将自动进行增量更新。
              </>
            )}
            <br />
            <span style={{ color: '#ff4d4f' }}>同步过程可能需要几分钟，请耐心等待。</span>
          </p>
        </div>
      ),
      okText: '开始同步',
      cancelText: '取消',
      onOk: () => {
        setSyncProgress(null)
        // 始终使用全量同步，系统会自动处理增量逻辑
        syncMutation.mutate({ shopId: shop.id, fullSync: true })
      },
    })
  }

  const handleCloseProgressModal = () => {
    const cleanup = () => {
      setSyncProgressModalVisible(false)
      setSyncProgress(null)
      setSyncingShopId(null)
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      // 强制清除所有遮罩层和残留元素
      setTimeout(() => {
        // 清除所有残留的遮罩层
        const masks = document.querySelectorAll('.ant-modal-mask')
        masks.forEach((mask) => {
          mask.remove()
        })
        // 清除可能残留的模态框容器
        const wrappers = document.querySelectorAll('.ant-modal-wrap')
        wrappers.forEach((wrapper) => {
          if (!wrapper.querySelector('.ant-modal')) {
            wrapper.remove()
          }
        })
        // 清除body上的样式
        document.body.style.overflow = ''
        document.body.style.paddingRight = ''
      }, 200)
    }
    
    if (syncProgress?.status === 'running') {
      Modal.confirm({
        title: '确认关闭',
        content: '同步仍在进行中，关闭后仍可在后台继续。是否确认关闭？',
        onOk: cleanup,
      })
    } else {
      cleanup()
    }
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
      fixed: 'right' as const,
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
        dataSource={Array.isArray(shops) ? shops : []}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        pagination={{
          pageSize: 50,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
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
            <Select placeholder="请选择地区" allowClear={false}>
              <Select.Option value="us">US（美国）</Select.Option>
              <Select.Option value="eu">EU（欧洲）</Select.Option>
              <Select.Option value="global">GLOBAL（全球）</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            label="Access Token"
            name="access_token"
            rules={[{ required: !editingShop, message: '请输入 Access Token' }]}
            extra={editingShop ? "如需更新Token，请通过「授权/更新授权」按钮设置；此处留空表示不修改。已有值已隐藏显示。" : "店铺授权所需的访问令牌，从 Temu 卖家中心获取"}
          >
            <Input.Password 
              style={{ fontFamily: 'monospace' }}
              placeholder={editingShop ? "（已有值已隐藏，输入新值可更新）" : "粘贴该店铺的 Access Token"} 
              visibilityToggle={true}
            />
          </Form.Item>
          
          <Form.Item
            label="CN 区域配置（商品列表、发品等）"
            name="cn_access_token"
            extra={
              <div>
                <div style={{ marginBottom: 4, color: '#ff4d4f', fontWeight: 'bold' }}>
                  ⚠️ 重要：CN 区域的 app_key、secret、access_token 和接口地址必须都来自 CN 区域，不能混用！
                </div>
                <div>
                  请从{' '}
                  <a 
                    href="https://agentpartner.temu.com/document?cataId=875196199516&docId=909799935182" 
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    指定地址
                  </a>
                  {' '}获取授权。
                  {editingShop ? '留空表示不修改。已有值已隐藏显示。' : '如果填写了 CN Access Token，系统会自动使用 CN 区域的配置。'}
                </div>
              </div>
            }
          >
            <Input.Password 
              style={{ fontFamily: 'monospace' }}
              placeholder={editingShop ? "（已有值已隐藏，输入新值可更新）" : "粘贴 CN 区域的 Access Token（可选）"} 
              visibilityToggle={true}
            />
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
          
          {editingShop && (
            <Form.Item
              label="启用状态"
              name="is_active"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          )}
        </Form>
        
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          background: '#f0f2f5', 
          borderRadius: 4 
        }}>
          <p style={{ margin: 0, fontSize: 12, color: '#666' }}>
            💡 提示：App Key 和 App Secret 已内置在系统中。
            <br />
            {!editingShop && (
              <>
                添加店铺时需要填写 Access Token。如果还没有获取 Token，请访问{' '}
                <a 
                  href="https://seller.temu.com/open-platform/client-manage" 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Temu 卖家中心
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

      {/* 同步进度模态框 */}
      <Modal
        title="同步进度"
        open={syncProgressModalVisible}
        onCancel={handleCloseProgressModal}
        footer={[
          <Button key="close" onClick={handleCloseProgressModal}>
            {syncProgress?.status === 'running' ? '后台运行' : '关闭'}
          </Button>
        ]}
        closable={syncProgress?.status !== 'running'}
        maskClosable={syncProgress?.status !== 'running'}
        mask={true}
        destroyOnClose={true}
        forceRender={false}
        getContainer={false}
        afterClose={() => {
          // 确保清理所有状态
          setSyncProgress(null)
          setSyncingShopId(null)
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current)
            progressIntervalRef.current = null
          }
          // 强制清除所有遮罩层和残留元素
          setTimeout(() => {
            // 清除所有残留的遮罩层
            const masks = document.querySelectorAll('.ant-modal-mask')
            masks.forEach((mask) => {
              mask.remove()
            })
            // 清除可能残留的模态框容器
            const wrappers = document.querySelectorAll('.ant-modal-wrap')
            wrappers.forEach((wrapper) => {
              if (!wrapper.querySelector('.ant-modal')) {
                wrapper.remove()
              }
            })
            // 清除body上的样式
            document.body.style.overflow = ''
            document.body.style.paddingRight = ''
          }, 200)
        }}
      >
        {syncProgress && (
          <div>
            <Progress
              percent={syncProgress.progress || 0}
              status={syncProgress.status === 'error' ? 'exception' : syncProgress.status === 'completed' ? 'success' : 'active'}
              strokeColor={syncProgress.status === 'completed' ? '#52c41a' : undefined}
            />
            <div style={{ marginTop: 16 }}>
              <p><strong>当前状态：</strong>{syncProgress.current_step || '准备中...'}</p>
              
              {/* 显示预估时间和处理速度 */}
              {syncProgress.status === 'running' && syncProgress.time_info && (
                <div style={{ marginTop: 12, padding: 12, background: '#e6f7ff', borderRadius: 4, border: '1px solid #91d5ff' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div>
                      <strong>处理速度：</strong>
                      <Text strong style={{ color: '#1890ff' }}>
                        {syncProgress.time_info.processing_speed?.toFixed(1) || 0} 订单/秒
                      </Text>
                    </div>
                    {syncProgress.estimated_completion_timestamp && (
                      <div>
                        <strong>预计完成：</strong>
                        <Text strong style={{ color: '#1890ff' }}>
                          {new Date(syncProgress.estimated_completion_timestamp * 1000).toLocaleTimeString()}
                        </Text>
                      </div>
                    )}
                  </div>
                  {syncProgress.time_info.estimated_remaining_seconds && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      剩余时间：约 {Math.floor(syncProgress.time_info.estimated_remaining_seconds / 60)} 分 {Math.floor(syncProgress.time_info.estimated_remaining_seconds % 60)} 秒
                    </div>
                  )}
                  {syncProgress.time_info.processed_count !== undefined && syncProgress.time_info.total_count !== undefined && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
                      进度：{syncProgress.time_info.processed_count} / {syncProgress.time_info.total_count} 订单
                    </div>
                  )}
                </div>
              )}
              
              {/* 同步日志输出框 - 同步中或已完成时都显示 */}
              {(syncProgress.status === 'running' || syncProgress.status === 'completed' || syncProgress.status === 'error') && (
                <Card 
                  title={`同步日志 ${syncProgress.status === 'completed' ? '(已完成)' : syncProgress.status === 'error' ? '(失败)' : '(进行中)'}`}
                  size="small" 
                  style={{ marginTop: 16 }}
                  bodyStyle={{ padding: 12, maxHeight: '400px', overflow: 'auto' }}
                >
                  <div 
                    ref={logScrollRef}
                    style={{ 
                      fontFamily: 'monospace', 
                      fontSize: '12px',
                      lineHeight: '1.6',
                      maxHeight: '350px',
                      overflowY: 'auto',
                      background: '#1e1e1e',
                      color: '#d4d4d4',
                      padding: '12px',
                      borderRadius: '4px'
                    }}
                  >
                    {syncLogs.length === 0 ? (
                      <div style={{ color: '#888' }}>等待日志输出...</div>
                    ) : (
                      // 日志已经是从新到旧排序（最新的在前），直接显示
                      syncLogs.map((log: any, index: number) => {
                        const logTime = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''
                        const logLevel = log.level || 'info'
                        const logColor = 
                          logLevel === 'error' ? '#f48771' :
                          logLevel === 'warning' ? '#dcdcaa' :
                          logLevel === 'success' ? '#4ec9b0' :
                          '#d4d4d4'
                        
                        return (
                          <div key={index} style={{ marginBottom: 4 }}>
                            <span style={{ color: '#808080' }}>[{logTime}]</span>{' '}
                            <span style={{ color: logColor }}>{log.message}</span>
                          </div>
                        )
                      })
                    )}
                  </div>
                </Card>
              )}
              
              {syncProgress.status === 'completed' && (
                <div style={{ marginTop: 16, padding: 12, background: '#f6f8fa', borderRadius: 4 }}>
                  <Descriptions column={1} size="small">
                        <Descriptions.Item label="订单同步">
                      {syncProgress.orders ? (
                        syncProgress.orders.error ? (
                          <span style={{ color: '#ff4d4f' }}>
                            同步失败: {syncProgress.orders.error}
                          </span>
                        ) : (
                          <>
                          总数: {syncProgress.orders.total || 0}
                          {syncProgress.orders.new > 0 && ` | 新增: ${syncProgress.orders.new}`}
                          {syncProgress.orders.updated > 0 && ` | 更新: ${syncProgress.orders.updated}`}
                          {syncProgress.orders.failed > 0 && ` | 失败: ${syncProgress.orders.failed}`}
                      </>
                        )
                      ) : (
                        <span style={{ color: '#999' }}>未执行</span>
                    )}
                    </Descriptions.Item>
                        <Descriptions.Item label="商品同步">
                      {syncProgress.products ? (
                        syncProgress.products.error ? (
                          <span style={{ color: '#ff4d4f' }}>
                            同步失败: {syncProgress.products.error}
                          </span>
                        ) : (
                          <>
                          总数: {syncProgress.products.total || 0}
                          {syncProgress.products.new > 0 && ` | 新增: ${syncProgress.products.new}`}
                          {syncProgress.products.updated > 0 && ` | 更新: ${syncProgress.products.updated}`}
                          {syncProgress.products.failed > 0 && ` | 失败: ${syncProgress.products.failed}`}
                      </>
                        )
                      ) : (
                        <span style={{ color: '#999' }}>未执行</span>
                    )}
                    </Descriptions.Item>
                    {syncProgress.categories !== undefined && (
                      <Descriptions.Item label="分类同步">
                        {typeof syncProgress.categories === 'object' && syncProgress.categories?.error ? (
                          <span style={{ color: '#ff4d4f' }}>
                            同步失败: {syncProgress.categories.error}
                          </span>
                        ) : (
                          `${syncProgress.categories || 0} 个分类`
                        )}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </div>
              )}
              
              {syncProgress.status === 'error' && (
                <div style={{ marginTop: 16, padding: 12, background: '#fff2f0', borderRadius: 4, color: '#ff4d4f' }}>
                  <p><strong>错误信息：</strong></p>
                  <p>{syncProgress.error || '未知错误'}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

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

