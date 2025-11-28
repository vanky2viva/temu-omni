import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { App as AntdApp, Spin } from 'antd'
import MainLayout from './layouts/MainLayout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const ShopList = lazy(() => import('./pages/ShopList'))
const OrderList = lazy(() => import('./pages/OrderList'))
const ProductList = lazy(() => import('./pages/ProductList'))
const Logistics = lazy(() => import('./pages/Logistics'))
const Finance = lazy(() => import('./pages/Finance'))
const SalesStatistics = lazy(() => import('./pages/SalesStatistics'))
const FrogGPT = lazy(() => import('./pages/FrogGPT/FrogGPTV2'))

function App() {
  return (
    <AntdApp>
      <BrowserRouter>
        <Suspense
          fallback={
            <div style={{ width: '100%', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Spin size="large" />
            </div>
          }
        >
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="shops" element={<ShopList />} />
              <Route path="orders" element={<OrderList />} />
              <Route path="products" element={<ProductList />} />
              <Route path="logistics" element={<Logistics />} />
              <Route path="finance" element={<Finance />} />
              <Route path="statistics" element={<SalesStatistics />} />
              <Route path="frog-gpt" element={<FrogGPT />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AntdApp>
  )
}

export default App
