import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
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
    if (error.response) {
      // 处理HTTP错误
      console.error('API Error:', error.response.data)
    }
    return Promise.reject(error)
  }
)

// 店铺API
export const shopApi = {
  getShops: () => api.get('/shops/'),
  getShop: (id: number) => api.get(`/shops/${id}/`),
  createShop: (data: any) => api.post('/shops/', data),
  updateShop: (id: number, data: any) => api.put(`/shops/${id}/`, data),
  deleteShop: (id: number) => api.delete(`/shops/${id}/`),
}

// 订单API
export const orderApi = {
  getOrders: (params?: any) => api.get('/orders/', { params }),
  getOrder: (id: number) => api.get(`/orders/${id}/`),
  createOrder: (data: any) => api.post('/orders/', data),
  updateOrder: (id: number, data: any) => api.put(`/orders/${id}/`, data),
  deleteOrder: (id: number) => api.delete(`/orders/${id}/`),
}

// 商品API
export const productApi = {
  getProducts: (params?: any) => api.get('/products/', { params }),
  getProduct: (id: number) => api.get(`/products/${id}/`),
  createProduct: (data: any) => api.post('/products/', data),
  updateProduct: (id: number, data: any) => api.put(`/products/${id}/`, data),
  deleteProduct: (id: number) => api.delete(`/products/${id}/`),
  getProductCosts: (id: number) => api.get(`/products/${id}/costs/`),
  createProductCost: (data: any) => api.post('/products/costs/', data),
}

// 统计API
export const statisticsApi = {
  getOverview: (params?: any) => api.get('/statistics/overview/', { params }),
  getDaily: (params?: any) => api.get('/statistics/daily/', { params }),
  getWeekly: (params?: any) => api.get('/statistics/weekly/', { params }),
  getMonthly: (params?: any) => api.get('/statistics/monthly/', { params }),
  getShopComparison: (params?: any) => api.get('/statistics/shops/comparison/', { params }),
  getTrend: (params?: any) => api.get('/statistics/trend/', { params }),
}

export default api

