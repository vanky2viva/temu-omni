import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加token到请求头
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
    if (error.response) {
      // 处理401未授权错误，跳转到登录页
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      // 处理HTTP错误
      console.error('API Error:', error.response.data)
    }
    return Promise.reject(error)
  }
)

// 店铺API
export const shopApi = {
  getShops: () => api.get('/shops/'),
  getShop: (id: number) => api.get(`/shops/${id}`),
  createShop: (data: any) => api.post('/shops/', data),
  updateShop: (id: number, data: any) => api.put(`/shops/${id}`, data),
  deleteShop: (id: number) => api.delete(`/shops/${id}`),
  authorizeShop: (id: number, accessToken: string, shopId?: string) =>
    api.post(`/shops/${id}/authorize`, { access_token: accessToken, shop_id: shopId }),
}

// 数据同步API（增加超时时间到5分钟）
export const syncApi = {
  syncShopAll: (shopId: number, fullSync: boolean = true) => 
    api.post(`/sync/shops/${shopId}/all?full_sync=${fullSync}`, {}, { timeout: 300000 }),
  syncShopOrders: (shopId: number, fullSync: boolean = true) => 
    api.post(`/sync/shops/${shopId}/orders?full_sync=${fullSync}`, {}, { timeout: 300000 }),
  syncShopProducts: (shopId: number, fullSync: boolean = true) => 
    api.post(`/sync/shops/${shopId}/products?full_sync=${fullSync}`, {}, { timeout: 180000 }),
  getSyncStatus: (shopId: number) => 
    api.get(`/sync/shops/${shopId}/status`),
  getSyncProgress: (shopId: number) => 
    api.get(`/sync/shops/${shopId}/progress`, { timeout: 5000 }), // 5秒超时，避免请求卡住
  verifyToken: (shopId: number) => 
    api.post(`/sync/shops/${shopId}/verify-token`),
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
  getProduct: (id: number) => api.get(`/products/${id}`),
  createProduct: (data: any) => api.post('/products/', data),
  updateProduct: (id: number, data: any) => api.put(`/products/${id}`, data),
  deleteProduct: (id: number) => api.delete(`/products/${id}`),
  getProductCosts: (id: number) => api.get(`/products/${id}/costs`),
  createProductCost: (data: any) => api.post('/products/costs/', data),
  updateProductCost: (id: number, data: { cost_price: number; currency?: string }) => 
    api.put(`/products/${id}/cost`, data),
  clearProducts: (shopId?: number) => api.delete('/products/', { params: { shop_id: shopId } }),
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

// 分析API
export const analyticsApi = {
  getPaymentCollection: (params?: any) => api.get('/analytics/payment-collection', { params }),
  getSalesOverview: (params?: any) => api.get('/analytics/sales-overview', { params }),
}

// 数据导入API
export const importApi = {
  // 导入订单数据（Excel文件）
  importOrders: (shopId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/import/shops/${shopId}/orders`, formData, { timeout: 120000 })
  },
  // 导入活动数据（Excel文件）
  importActivities: (shopId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/import/shops/${shopId}/activities`, formData, { timeout: 120000 })
  },
  // 导入商品数据（Excel文件）
  importProducts: (shopId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/import/shops/${shopId}/products`, formData, { timeout: 120000 })
  },
  // 从在线表格导入订单数据
  importOrdersFromUrl: (shopId: number, url: string, password?: string) => 
    api.post(`/import/shops/${shopId}/orders/from-url`, { url, password }, { timeout: 120000 }),
  // 从在线表格导入活动数据
  importActivitiesFromUrl: (shopId: number, url: string, password?: string) => 
    api.post(`/import/shops/${shopId}/activities/from-url`, { url, password }, { timeout: 120000 }),
  // 从在线表格导入商品数据
  importProductsFromUrl: (shopId: number, url: string, password?: string) => 
    api.post(`/import/shops/${shopId}/products/from-url`, { url, password }, { timeout: 120000 }),
  // 获取导入历史
  getImportHistory: (shopId: number, params?: { skip?: number; limit?: number; import_type?: string }) =>
    api.get(`/import/shops/${shopId}/history`, { params }),
  // 获取导入详情
  getImportDetail: (shopId: number, importId: number) =>
    api.get(`/import/shops/${shopId}/history/${importId}`),
}

// ForgGPT API
export const forggptApi = {
  // 发送消息（普通响应）
  chat: (data: {
    message: string
    session_id?: string
    shop_ids?: number[]
    date_range?: { start: string; end: string }
    stream?: boolean
    history?: Array<{ role: string; content: string }>
  }) => api.post('/forggpt/chat', data, { timeout: 60000 }),
  
  // 获取对话历史
  getHistory: (sessionId: string) => api.get(`/forggpt/history/${sessionId}`),
  
  // 上传文件
  uploadFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/forggpt/upload', formData, { timeout: 120000 })
  },
}

// AI配置API
export const aiConfigApi = {
  // 获取AI配置
  getConfig: () => api.get('/system/ai-config/'),
  
  // 更新AI配置
  updateConfig: (data: {
    provider: string
    deepseek_api_key?: string
    deepseek_base_url?: string
    deepseek_model?: string
    openai_api_key?: string
    openai_base_url?: string
    openai_model?: string
    timeout_seconds?: number
    cache_enabled?: boolean
    cache_ttl_days?: number
    daily_limit?: number
  }) => api.put('/system/ai-config/', data),
}

export default api

