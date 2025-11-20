import axios from 'axios'

// 创建统一的API实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
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
    return response.data
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

export interface OverviewStatistics {
  total_orders: number;
  total_gmv: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
}

export interface DailyStatistics {
  date: string;
  order_count: number;
  gmv: number;
  cost: number;
  profit: number;
}

export interface MonthlyStatistics {
  month: string;
  order_count: number;
  gmv: number;
  cost: number;
  profit: number;
}

/**
 * 统计数据API
 */
export const statisticsApi = {
  /**
   * 获取总览统计数据
   */
  getOverview: (params?: {
    shop_ids?: number[];
    start_date?: string;
    end_date?: string;
    status?: string;
  }): Promise<OverviewStatistics> => {
    return api.get('/statistics/overview/', { params })
  },

  /**
   * 获取每日统计数据
   */
  getDaily: (params?: {
    shop_ids?: number[];
    start_date?: string;
    end_date?: string;
    days?: number;
  }): Promise<DailyStatistics[]> => {
    return api.get('/statistics/daily/', { params })
  },

  /**
   * 获取每月统计数据
   */
  getMonthly: (params?: {
    shop_ids?: number[];
    months?: number;
  }): Promise<MonthlyStatistics[]> => {
    return api.get('/statistics/monthly/', { params })
  },
}

