import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, Form, Input, Button, message, Alert, Space } from 'antd'
import { SaveOutlined, ApiOutlined } from '@ant-design/icons'
import axios from 'axios'

function SystemSettings() {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取应用配置
  const { data: appConfig, isLoading } = useQuery({
    queryKey: ['app-config'],
    queryFn: async () => {
      const response = await axios.get('/api/system/app-config/')
      return response.data
    },
  })

  // 更新应用配置
  const updateMutation = useMutation({
    mutationFn: async (values: any) => {
      const response = await axios.put('/api/system/app-config/', values)
      return response.data
    },
    onSuccess: () => {
      message.success('应用配置保存成功')
      queryClient.invalidateQueries({ queryKey: ['app-config'] })
    },
    onError: () => {
      message.error('应用配置保存失败')
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      updateMutation.mutate(values)
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  // 设置表单初始值
  if (appConfig && !form.getFieldValue('app_key')) {
    form.setFieldsValue({
      app_key: appConfig.app_key || '',
    })
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统设置</h2>

      <Card 
        title={
          <Space>
            <ApiOutlined />
            <span>Temu应用配置</span>
          </Space>
        }
        loading={isLoading}
      >
        <Alert
          message="应用级配置说明"
          description={
            <div>
              <p>App Key和App Secret是应用级别的凭证，一个应用可以管理多个店铺。</p>
              <p>请在Temu开放平台（<a href="https://agentpartner.temu.com/" target="_blank" rel="noopener noreferrer">https://agentpartner.temu.com/</a>）申请应用后，将凭证填写在此处。</p>
              <p>配置后，在添加店铺时只需要填写该店铺的Access Token即可。</p>
            </div>
          }
          type="info"
          style={{ marginBottom: 24 }}
        />

        <Form
          form={form}
          layout="vertical"
          style={{ maxWidth: 600 }}
        >
          <Form.Item
            label="App Key"
            name="app_key"
            rules={[{ required: true, message: '请输入App Key' }]}
            extra="从Temu开放平台获取的应用Key"
          >
            <Input 
              placeholder="输入App Key" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="App Secret"
            name="app_secret"
            rules={[
              { required: !appConfig?.has_app_secret, message: '请输入App Secret' }
            ]}
            extra={
              appConfig?.has_app_secret 
                ? "已配置App Secret，如需修改请重新输入" 
                : "从Temu开放平台获取的应用Secret，请妥善保管"
            }
          >
            <Input.Password 
              placeholder={appConfig?.has_app_secret ? "留空表示不修改" : "输入App Secret"}
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              size="large"
              icon={<SaveOutlined />}
              onClick={handleSubmit}
              loading={updateMutation.isPending}
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>

        <div style={{
          marginTop: 24,
          padding: 16,
          background: '#f0f2f5',
          borderRadius: 4
        }}>
          <h4>配置状态</h4>
          <p>
            App Key: {appConfig?.app_key ? `已配置 (${appConfig.app_key})` : '未配置'}
          </p>
          <p>
            App Secret: {appConfig?.has_app_secret ? '已配置 ✅' : '未配置 ⚠️'}
          </p>
        </div>
      </Card>
    </div>
  )
}

export default SystemSettings

