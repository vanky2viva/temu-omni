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
    api.get(`/sync/shops/${shopId}/progress`, { timeout: 60000 }), // 60秒超时（同步任务可能较长）
  getSyncLogs: (shopId: number, limit: number = 100) => 
    api.get(`/sync/shops/${shopId}/logs?limit=${limit}`, { timeout: 30000 }), // 30秒超时
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
  getStatusStatistics: (params?: any) => api.get('/orders/statistics/status', { params }),
  // 批量操作API
  batchExport: (orderIds: number[], format: 'csv' | 'excel') => 
    api.post('/orders/batch/export', { order_ids: orderIds, format }, { responseType: 'blob' }),
  batchTags: (orderIds: number[], tagName: string, action: 'add' | 'remove') =>
    api.post('/orders/batch/tags', { order_ids: orderIds, tag_name: tagName, action }),
  batchNotes: (orderIds: number[], noteContent: string) =>
    api.post('/orders/batch/notes', { order_ids: orderIds, note_content: noteContent }),
  batchStatus: (orderIds: number[], status: string) =>
    api.post('/orders/batch/status', { order_ids: orderIds, status }),
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
  getSkuSalesRanking: (params?: any) => api.get('/analytics/sku-sales-ranking', { params }),
  getManagerSales: (params?: any) => api.get('/analytics/manager-sales', { params }),
  getDelayRate: (params?: any) => api.get('/analytics/delay-rate', { params }),
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

// 用户视图API
export const userViewsApi = {
  // 获取用户视图列表
  getViews: (viewType?: string) => api.get('/user-views/', { params: { view_type: viewType } }),
  
  // 获取指定视图
  getView: (viewId: number) => api.get(`/user-views/${viewId}`),
  
  // 创建视图
  createView: (data: {
    name: string
    view_type?: string
    description?: string
    filters?: any
    visible_columns?: string[]
    column_order?: string[]
    column_widths?: Record<string, number>
    group_by?: string
    is_default?: boolean
    is_public?: boolean
  }) => api.post('/user-views/', data),
  
  // 更新视图
  updateView: (viewId: number, data: {
    name?: string
    description?: string
    filters?: any
    visible_columns?: string[]
    column_order?: string[]
    column_widths?: Record<string, number>
    group_by?: string
    is_default?: boolean
    is_public?: boolean
  }) => api.put(`/user-views/${viewId}`, data),
  
  // 删除视图
  deleteView: (viewId: number) => api.delete(`/user-views/${viewId}`),
  
  // 获取默认视图
  getDefaultView: (viewType: string) => api.get(`/user-views/default/${viewType}`),
}

// FrogGPT AI API
export const frogGptApi = {
  // 发送聊天消息
  chat: (data: {
    messages: Array<{ role: string; content: string }>
    model?: string
    temperature?: number
    max_tokens?: number
    include_system_data?: boolean
    data_summary_days?: number
    shop_id?: number
  }) => api.post('/frog-gpt/chat', data),
  
  // 发送流式聊天消息
  chatStream: async function* (data: {
    messages: Array<{ role: string; content: string }>
    model?: string
    temperature?: number
    max_tokens?: number
    include_system_data?: boolean
    data_summary_days?: number
    shop_id?: number
  }) {
    const token = localStorage.getItem('token')
    const response = await fetch(`${api.defaults.baseURL}/frog-gpt/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('响应体不可读')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        while (true) {
          const lineEnd = buffer.indexOf('\n')
          if (lineEnd === -1) break

          const line = buffer.slice(0, lineEnd).trim()
          buffer = buffer.slice(lineEnd + 1)

          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') return

            try {
              const parsed = JSON.parse(data)
              yield parsed
            } catch (e) {
              // 忽略无效的 JSON
            }
          }
        }
      }
    } finally {
      reader.cancel()
    }
  },
  
  // 发送带文件的聊天消息
  chatWithFiles: (formData: FormData) => 
    api.post('/frog-gpt/chat/with-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2分钟超时
    }),
  
  // 获取可用模型列表
  getModels: () => api.get('/frog-gpt/models'),
  
  // 获取数据摘要
  getDataSummary: (days?: number) => 
    api.get('/frog-gpt/data-summary', { params: { days } }),
  
  // 获取OpenRouter API配置
  getApiConfig: () => api.get('/frog-gpt/api-config'),
  
  // 获取完整的OpenRouter API key
  getFullApiKey: () => api.get('/frog-gpt/api-config/full'),
  
  // 获取所有AI提供商的完整API key
  getAllProvidersApiKeys: () => api.get('/frog-gpt/api-config/all-providers'),
  
  // 更新OpenRouter API配置
  updateApiConfig: (apiKey: string) => 
    api.put('/frog-gpt/api-config', { api_key: apiKey }),
  
  // 更新所有供应商的API Key
  updateAllProvidersApiKeys: (keys: { openrouter?: string; openai?: string; anthropic?: string; gemini?: string }) =>
    api.put('/frog-gpt/api-config/all-providers', keys),
  
  // 验证API Key是否有效
  verifyApiKey: (provider: string = 'openrouter') =>
    api.get('/frog-gpt/api-config/verify', { params: { provider } }),
  // 测试连接，验证是否能正确获得回复
  testConnection: (model?: string) =>
    api.post('/frog-gpt/test-connection', { model }),
}

// 系统AI配置API
export const systemApi = {
  // 获取AI配置
  getAiConfig: () => api.get('/system/ai-config/'),
  
  // 更新AI配置
  updateAiConfig: (config: any) => api.put('/system/ai-config/', config),
}

export default api

