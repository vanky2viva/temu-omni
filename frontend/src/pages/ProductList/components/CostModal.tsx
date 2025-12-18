import React from 'react'
import { Modal, Form, Input, InputNumber, Select } from 'antd'

interface CostModalProps {
  visible: boolean
  onOk: (values: any) => void
  onCancel: () => void
  loading: boolean
  productName: string
}

const CostModal: React.FC<CostModalProps> = ({
  visible,
  onOk,
  onCancel,
  loading,
  productName,
}) => {
  const [form] = Form.useForm()

  return (
    <Modal
      title={`录入成本 - ${productName}`}
      open={visible}
      onOk={async () => {
        const values = await form.validateFields()
        onOk(values)
      }}
      onCancel={onCancel}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
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
          initialValue="CNY"
          rules={[{ required: true, message: '请选择货币' }]}
        >
          <Select>
            <Select.Option value="CNY">CNY</Select.Option>
            <Select.Option value="USD">USD</Select.Option>
            <Select.Option value="EUR">EUR</Select.Option>
            <Select.Option value="GBP">GBP</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="备注" name="notes">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CostModal

