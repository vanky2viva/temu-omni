import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography

interface LoginForm {
  username: string
  password: string
}

function Login() {
  const [loading, setLoading] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const navigate = useNavigate()

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const onFinish = async (values: LoginForm) => {
    setLoading(true)
    try {
      const formData = new URLSearchParams()
      formData.append('username', values.username)
      formData.append('password', values.password)

      const response = await axios.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      const { access_token, user } = response.data

      // 保存token和用户信息
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      message.success('登录成功')
      navigate('/dashboard')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '登录失败，请检查用户名和密码'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '16px',
    }}>
      <Card 
        style={{ 
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ fontSize: isMobile ? '24px' : '32px' }}>
            Temu-Omni
          </Title>
          <Text type="secondary" style={{ fontSize: isMobile ? '12px' : '14px' }}>
            多店铺管理系统
          </Text>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名或邮箱' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名或邮箱"
              style={{ fontSize: '16px' }} // 防止iOS自动缩放
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              style={{ fontSize: '16px' }} // 防止iOS自动缩放
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading}
              size="large"
              style={{
                height: isMobile ? '44px' : '48px',
                fontSize: '16px',
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login

