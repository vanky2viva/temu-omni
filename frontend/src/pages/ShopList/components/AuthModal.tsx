import React from 'react'
import { Modal, Form, Input } from 'antd'

interface AuthModalProps {
  visible: boolean
  onOk: (values: any) => void
  onCancel: () => void
  loading: boolean
  shopName: string
}

const AuthModal: React.FC<AuthModalProps> = ({
  visible,
  onOk,
  onCancel,
  loading,
  shopName,
}) => {
  const [form] = Form.useForm()

  return (
    <Modal
      title={`授权店铺：${shopName}`}
      open={visible}
      onOk={async () => {
        const values = await form.validateFields()
        onOk(values)
      }}
      onCancel={onCancel}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
        <Form.Item label="Temu店铺ID" name="shop_id" rules={[{ required: true }]}>
          <Input placeholder="例如：635517726820718" />
        </Form.Item>
        <Form.Item label="Access Token" name="access_token" rules={[{ required: true }]}>
          <Input.TextArea rows={3} placeholder="粘贴该店铺的Access Token" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default AuthModal

