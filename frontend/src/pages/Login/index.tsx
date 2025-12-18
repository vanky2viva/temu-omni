import React from 'react'
import { Form, Input, Button, Card, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useLogin } from './hooks/useLogin'

const { Title, Text } = Typography

const Login: React.FC = () => {
  const { loading, isMobile, onLogin } = useLogin()

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <Card style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2}>Temu-Omni</Title>
          <Text type="secondary">多店铺管理系统</Text>
        </div>
        <Form onFinish={onLogin} size="large">
          <Form.Item name="username" rules={[{ required: true }]}><Input prefix={<UserOutlined />} placeholder="用户名" /></Form.Item>
          <Form.Item name="password" rules={[{ required: true }]}><Input.Password prefix={<LockOutlined />} placeholder="密码" /></Form.Item>
          <Button type="primary" htmlType="submit" block loading={loading}>登录</Button>
        </Form>
      </Card>
    </div>
  )
}

export default Login

