import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './index.css'
import './utils/clearCacheHelper'

// 配置dayjs为中文
dayjs.locale('zh-cn')

// 创建React Query客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 0, // 默认禁用缓存，总是获取最新数据
      cacheTime: 0, // 禁用缓存时间
    },
  },
})

// 将 queryClient 挂载到 window 对象，方便清理缓存
if (typeof window !== 'undefined') {
  (window as any).queryClient = queryClient
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <App />
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)

