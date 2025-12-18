import React, { useEffect } from 'react'
import { Modal, Form, Input, Select, Switch } from 'antd'
import { shopApi } from '@/services/api'

interface ShopModalProps {
  visible: boolean
  onOk: (values: any) => void
  onCancel: () => void
  loading: boolean
  shop: any
}

const ShopModal: React.FC<ShopModalProps> = ({
  visible,
  onOk,
  onCancel,
  loading,
  shop,
}) => {
  const [form] = Form.useForm()

  useEffect(() => {
    if (visible) {
      if (shop) {
        shopApi.getShop(shop.id).then((detail: any) => {
          form.setFieldsValue({
            ...detail,
            _original_access_token: detail.access_token || '',
            _original_cn_access_token: detail.cn_access_token || '',
          })
        }).catch(() => {
          form.setFieldsValue(shop)
        })
      } else {
        form.resetFields()
      }
    }
  }, [visible, shop, form])

  const handleOk = async () => {
    const values = await form.validateFields()
    
    // 敏感字段处理逻辑保持不变
    if (shop) {
      const { _original_access_token, _original_cn_access_token, ...rest } = values
      if (values.access_token === _original_access_token) delete rest.access_token
      if (values.cn_access_token === _original_cn_access_token) delete rest.cn_access_token
      onOk(rest)
    } else {
      onOk(values)
    }
  }

  return (
    <Modal
      title={shop ? '编辑店铺' : '添加店铺'}
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
        <Form.Item label="店铺名称" name="shop_name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="地区" name="region" rules={[{ required: true }]}>
          <Select>
            <Select.Option value="us">US（美国）</Select.Option>
            <Select.Option value="eu">EU（欧洲）</Select.Option>
            <Select.Option value="global">GLOBAL（全球）</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="Access Token" name="access_token" rules={[{ required: !shop }]}>
          <Input.Password />
        </Form.Item>
        <Form.Item label="CN 区域配置" name="cn_access_token">
          <Input.Password />
        </Form.Item>
        <Form.Item label="经营主体" name="entity">
          <Input />
        </Form.Item>
        <Form.Item label="负责人" name="default_manager">
          <Input />
        </Form.Item>
        <Form.Item label="备注" name="description">
          <Input.TextArea rows={3} />
        </Form.Item>
        {shop && (
          <Form.Item label="启用状态" name="is_active" valuePropName="checked">
            <Switch />
          </Form.Item>
        )}
      </Form>
    </Modal>
  )
}

export default ShopModal

