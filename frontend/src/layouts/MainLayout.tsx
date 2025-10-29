import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  ShopOutlined,
  ShoppingOutlined,
  ProductOutlined,
  BarChartOutlined,
  TableOutlined,
  FundOutlined,
  CrownOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider } = Layout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表板',
  },
  {
    key: '/shops',
    icon: <ShopOutlined />,
    label: '店铺管理',
  },
  {
    key: '/orders',
    icon: <ShoppingOutlined />,
    label: '订单管理',
  },
  {
    key: '/products',
    icon: <ProductOutlined />,
    label: '商品管理',
  },
  {
    key: '/statistics',
    icon: <BarChartOutlined />,
    label: '数据统计',
  },
  {
    key: '/gmv-table',
    icon: <TableOutlined />,
    label: 'GMV表格',
  },
  {
    key: '/sku-analysis',
    icon: <FundOutlined />,
    label: 'SKU分析',
  },
  {
    key: '/hot-seller',
    icon: <CrownOutlined />,
    label: '爆单榜',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
]

function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 48,
            margin: 16,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8))',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? '14px' : '18px',
            fontWeight: 'bold',
            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.5)',
            backdropFilter: 'blur(10px)',
            letterSpacing: '1px',
          }}
        >
          {collapsed ? '🚀' : '🚀 Luffy Store'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s', background: 'transparent' }}>
        <Header className="site-header" style={{ padding: '0 32px' }}>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            letterSpacing: '1px',
          }}>
            ✨ 多店铺管理系统
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 16px' }}>
          <div className="site-content" style={{ padding: 24, minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout

