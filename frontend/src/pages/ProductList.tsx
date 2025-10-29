import { useState } from 'react'
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
} from 'antd'
import { PlusOutlined, DollarOutlined } from '@ant-design/icons'
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
  })

  // 获取商品列表
  const { data: products, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: productApi.getProducts,
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

  const columns = [
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
    },
    {
      title: '所属店铺',
      dataIndex: 'shop_id',
      key: 'shop_id',
      width: 150,
      render: (shopId: number) => {
        const shop = shops?.find((s: any) => s.id === shopId)
        return shop?.shop_name || '-'
      },
    },
    {
      title: '当前售价',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      render: (price: number, record: any) =>
        price ? `${price} ${record.currency}` : '-',
    },
    {
      title: '库存',
      dataIndex: 'stock_quantity',
      key: 'stock_quantity',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '在售' : '下架'}
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
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>商品管理</h2>
      </div>

      <Table
        columns={columns}
        dataSource={products}
        rowKey="id"
        loading={isLoading}
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

