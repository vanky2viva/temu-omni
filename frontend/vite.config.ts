import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 粗粒度拆包，降低单包体积
        manualChunks: {
          react: ['react', 'react-dom'],
          antd: ['antd', '@ant-design/icons', '@ant-design/x'],
          echarts: ['echarts', 'echarts-for-react'],
          vendor: ['@tanstack/react-query', 'axios', 'dayjs'],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || (process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000'),
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
      },
    },
  },
})
