import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import axios from 'axios'

interface ProtectedRouteProps {
  children: React.ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      
      if (!token) {
        setIsAuthenticated(false)
        setLoading(false)
        return
      }

      try {
        // 验证token是否有效
        await axios.get('/api/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setIsAuthenticated(true)
      } catch (error) {
        // token无效，清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setIsAuthenticated(false)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
      }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute

