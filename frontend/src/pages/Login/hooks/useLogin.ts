import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import axios from 'axios'

export function useLogin() {
  const [loading, setLoading] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const onLogin = async (values: any) => {
    setLoading(true)
    try {
      const formData = new URLSearchParams()
      formData.append('username', values.username)
      formData.append('password', values.password)
      const response = await axios.post('/api/auth/login', formData)
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))
      message.success('登录成功')
      navigate('/dashboard')
    } catch (error: any) {
      message.error('登录失败')
    } finally {
      setLoading(false)
    }
  }

  return { loading, isMobile, onLogin }
}

