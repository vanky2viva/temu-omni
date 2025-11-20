import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Tag,
  Tooltip,
} from 'antd'
import { PlusOutlined, DollarOutlined, SearchOutlined, DeleteOutlined } from '@ant-design/icons'
import { productApi, shopApi } from '@/services/api'
import dayjs from 'dayjs'

function ProductList() {
  const [isCostModalOpen, setIsCostModalOpen] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<any>(null)
  const [costForm] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取店铺列表
  const { data: shops } = useQuery({
    queryKey: ['shops'],
    queryFn: shopApi.getShops,
    staleTime: 0,
  })

  // 筛选条件
  const [shopId, setShopId] = useState<number | undefined>()
  // 状态筛选：published | unpublished | all（默认已发布）
  const [statusFilter, setStatusFilter] = useState<'published' | 'unpublished' | 'all'>('published')
  const [manager, setManager] = useState<string | undefined>()
  const [category, setCategory] = useState<string | undefined>()
  const [keyword, setKeyword] = useState<string>('')

  // 获取商品列表（携带筛选参数）
  const { data: products, isLoading } = useQuery({
    queryKey: ['products', { shopId, statusFilter, manager, category, keyword }],
    queryFn: () =>
      productApi.getProducts({
        shop_id: shopId,
        is_active:
          statusFilter === 'published' ? true : statusFilter === 'unpublished' ? false : undefined,
        manager,
        category,
        q: keyword?.trim() || undefined,
        skip: 0,
        limit: 10000, // 增加limit以获取更多商品
      }),
    staleTime: 0,
  })

  // 创建成本记录
  const createCostMutation = useMutation({
    mutationFn: productApi.createProductCost,
    onSuccess: () => {
      message.success('成本记录添加成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      handleCloseCostModal()
    },
    onError: () => {
      message.error('成本记录添加失败')
    },
  })

  // 更新商品负责人
  const updateManagerMutation = useMutation({
    mutationFn: ({ id, manager }: { id: number; manager: string }) =>
      productApi.updateProduct(id, { manager }),
    onSuccess: () => {
      message.success('负责人更新成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      message.error('负责人更新失败')
    },
  })

  // 清理商品数据
  const clearProductsMutation = useMutation({
    mutationFn: (shopId?: number) => productApi.clearProducts(shopId),
    onSuccess: (data: any) => {
      message.success(data.message || '商品数据清理成功')
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '商品数据清理失败')
    },
  })

  const handleClearProducts = () => {
    Modal.confirm({
      title: '确认清理商品数据',
      content: shopId 
        ? `确定要清理当前店铺的所有商品数据吗？此操作不可恢复！`
        : '确定要清理所有店铺的商品数据吗？此操作不可恢复！',
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => {
        clearProductsMutation.mutate(shopId)
      },
    })
  }

  const handleUpdateManager = (productId: number, newManager: string) => {
    if (newManager === '-' || newManager === '__custom__') return
    updateManagerMutation.mutate({ id: productId, manager: newManager })
  }

  const handleOpenCostModal = (product: any) => {
    setSelectedProduct(product)
    costForm.setFieldsValue({
      product_id: product.id,
      effective_from: dayjs(),
      currency: 'USD',
    })
    setIsCostModalOpen(true)
  }

  const handleCloseCostModal = () => {
    setIsCostModalOpen(false)
    setSelectedProduct(null)
    costForm.resetFields()
  }

  const handleSubmitCost = async () => {
    try {
      const values = await costForm.validateFields()
      createCostMutation.mutate({
        ...values,
        effective_from: values.effective_from.toISOString(),
      })
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  // 供筛选使用的负责人/类目选项（基于当前数据集）
  const managerOptions = useMemo(() => {
    const set = new Set<string>()
    products?.forEach((p: any) => p?.manager && set.add(p.manager))
    return Array.from(set)
  }, [products])

  const categoryOptions = useMemo(() => {
    const set = new Set<string>()
    products?.forEach((p: any) => p?.category && set.add(p.category))
    return Array.from(set)
  }, [products])

  const columns = [
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '负责人',
      dataIndex: 'manager',
      key: 'manager',
      width: 120,
      render: (manager: string, record: any) => (
        <Select
          value={manager || '-'}
          style={{ width: '100%' }}
          size="small"
          bordered={false}
          dropdownMatchSelectWidth={false}
          onChange={(value) => handleUpdateManager(record.id, value)}
          options={[
            ...managerOptions.map(m => ({ label: m, value: m })),
            { label: '+ 自定义', value: '__custom__' }
          ]}
          onSelect={(value) => {
            if (value === '__custom__') {
              Modal.confirm({
                title: '输入新的负责人',
                content: (
                  <Input 
                    id="custom-manager-input" 
                    placeholder="请输入负责人姓名"
                    autoFocus
                  />
                ),
                onOk: () => {
                  const input = document.getElementById('custom-manager-input') as HTMLInputElement
                  const newManager = input?.value?.trim()
                  if (newManager) {
                    handleUpdateManager(record.id, newManager)
                  }
                }
              })
            }
          }}
        />
      ),
    },
    {
      title: '类目',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => {
        if (!category || category === '-') return '-'
        
        // 提取最后一级类目（用 > 分隔）
        const parts = category.split('>').map(p => p.trim())
        const lastLevel = parts[parts.length - 1] || category
        
        // 如果有多个级别，使用 Tooltip 显示完整信息
        if (parts.length > 1) {
          return (
            <Tooltip title={category}>
              <span style={{ fontSize: '12px', lineHeight: '1.4', cursor: 'help' }}>
                {lastLevel}
              </span>
            </Tooltip>
          )
        }
        
        // 如果只有一个级别，直接显示
        return (
          <span style={{ fontSize: '12px', lineHeight: '1.4' }}>{category}</span>
        )
      },
    },
    {
      title: '经营站点',
      dataIndex: 'shop_id',
      key: 'site',
      width: 120,
      render: (shopId: number) => {
        const shop = shops?.find((s: any) => s.id === shopId)
        return shop?.region?.toUpperCase?.() || '-'
      },
    },
    {
      title: 'SPU ID',
      dataIndex: 'spu_id',
      key: 'spu_id',
      width: 140,
      render: (_: any, record: any) => {
        // 从description中提取SPU ID
        if (record.description) {
          // 支持多种格式：SPU: xxx 或 SPU:xxx
          const match = record.description.match(/SPU:\s*([^\s\n]+)/i)
          if (match && match[1]) return match[1]
        }
        // 如果直接有spu_id字段，也支持
        if (record.spu_id) return record.spu_id
        return '-'
      },
    },
    {
      title: 'SKC ID',
      dataIndex: 'skc_id',
      key: 'skc_id',
      width: 140,
      render: (skc_id: string) => skc_id || '-',
    },
    {
      title: 'SKU ID',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 150,
    },
    {
      title: 'SKU货号',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
      render: (sku: string) => sku || '-',
    },
    {
      title: '申报价格',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      render: (price: number, record: any) => {
        if (!price) return '-'
        // 申报价格单位是人民币，统一显示为RMB
        // 如果是CNY或RMB，显示为人民币，否则默认显示为RMB（因为申报价格都是人民币）
        const currency = (record.currency === 'CNY' || record.currency === 'RMB') ? 'RMB' : 'RMB'
        return `${price} ${currency}`
      },
    },
    {
      title: '申报价格状态',
      dataIndex: 'price_status',
      key: 'price_status',
      width: 140,
      render: (price_status: string) => price_status || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '已发布' : '未发布'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<DollarOutlined />}
            onClick={() => handleOpenCostModal(record)}
          >
            录入成本
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space size="middle" wrap>
          <span>店铺：</span>
          <Select
            allowClear
            placeholder="全部店铺"
            style={{ width: 200 }}
            value={shopId}
            onChange={setShopId as any}
            options={shops?.map((s: any) => ({ label: s.shop_name, value: s.id }))}
          />

          <span>负责人：</span>
          <Select
            allowClear
            placeholder="全部负责人"
            style={{ width: 160 }}
            value={manager}
            onChange={setManager}
            options={managerOptions.map(m => ({ label: m, value: m }))}
          />

          <span>类目：</span>
          <Select
            allowClear
            placeholder="全部类目"
            style={{ width: 160 }}
            value={category}
            onChange={setCategory}
            options={categoryOptions.map(c => ({ label: c, value: c }))}
          />

          <span>关键词：</span>
          <Input
            allowClear
            style={{ width: 220 }}
            prefix={<SearchOutlined />}
            placeholder="商品名/SKU"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={() => queryClient.invalidateQueries({ queryKey: ['products'] })}
          />

          <span>状态：</span>
          <Select
            style={{ width: 160 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { label: '已发布', value: 'published' },
              { label: '未发布', value: 'unpublished' },
              { label: '全部', value: 'all' },
            ]}
          />
        </Space>
        <Space>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleClearProducts}
            loading={clearProductsMutation.isPending}
          >
            清理商品数据
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={products}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1400 }}
      />

      <Modal
        title={`录入成本 - ${selectedProduct?.product_name}`}
        open={isCostModalOpen}
        onOk={handleSubmitCost}
        onCancel={handleCloseCostModal}
        confirmLoading={createCostMutation.isPending}
      >
        <Form form={costForm} layout="vertical">
          <Form.Item name="product_id" hidden>
            <Input />
          </Form.Item>
          <Form.Item
            label="成本价"
            name="cost_price"
            rules={[{ required: true, message: '请输入成本价' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              precision={2}
              placeholder="请输入成本价"
            />
          </Form.Item>
          <Form.Item
            label="货币"
            name="currency"
            rules={[{ required: true, message: '请选择货币' }]}
          >
            <Select>
              <Select.Option value="USD">USD</Select.Option>
              <Select.Option value="EUR">EUR</Select.Option>
              <Select.Option value="GBP">GBP</Select.Option>
              <Select.Option value="CNY">CNY</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="备注" name="notes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProductList

