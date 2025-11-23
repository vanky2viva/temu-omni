/**
 * ChatKit API 服务
 */
import axios from 'axios'
import { ChatKitSession, DashboardCommand } from '@/types/chatkit'

// 使用配置好的 axios 实例（包含认证拦截器）
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 - 添加认证 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const chatkitApi = {
  /**
   * 创建 ChatKit 会话
   */
  createSession: async (shopId?: number, shopIds?: number[]): Promise<ChatKitSession> => {
    try {
      console.log('[chatkitApi] 创建会话请求:', { shopId, shopIds })
      const response = await api.post<ChatKitSession>('/chatkit/session', {
        shop_id: shopId,
        shop_ids: shopIds,
      })
      console.log('[chatkitApi] 会话创建响应:', response)
      // axios 响应拦截器返回的是 response，所以需要访问 response.data
      return response.data || response
    } catch (error: any) {
      console.error('[chatkitApi] 会话创建失败:', error)
      throw error
    }
  },

  /**
   * 获取会话信息
   */
  getSession: async (sessionId: string) => {
    const response = await api.get(`/chatkit/session/${sessionId}`)
    return response.data
  },

  /**
   * 发送消息（使用现有的 forggpt API）
   */
  sendMessage: async (
    message: string,
    sessionId: string,
    shopIds?: number[],
    dateRange?: { start: string; end: string },
    stream: boolean = true
  ) => {
    const response = await api.post(
      '/forggpt/chat',
      {
        message,
        session_id: sessionId,
        shop_ids: shopIds,
        date_range: dateRange,
        stream,
        history: [], // TODO: 从本地存储或状态中获取历史
      },
      {
        responseType: stream ? 'stream' : 'json',
      }
    )
    return response
  },
}

