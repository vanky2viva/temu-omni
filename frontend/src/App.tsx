import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import ShopList from './pages/ShopList'
import OrderList from './pages/OrderList'
import ProductList from './pages/ProductList'
import Logistics from './pages/Logistics'
import Finance from './pages/Finance'
import Statistics from './pages/Statistics'
import GmvTable from './pages/GmvTable'
import SkuAnalysis from './pages/SkuAnalysis'
import HotSellerPage from './pages/HotSellerPage'
import SystemSettings from './pages/SystemSettings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="shops" element={<ShopList />} />
          <Route path="orders" element={<OrderList />} />
          <Route path="products" element={<ProductList />} />
          <Route path="logistics" element={<Logistics />} />
          <Route path="finance" element={<Finance />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="gmv-table" element={<GmvTable />} />
          <Route path="sku-analysis" element={<SkuAnalysis />} />
          <Route path="hot-seller" element={<HotSellerPage />} />
          <Route path="settings" element={<SystemSettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

