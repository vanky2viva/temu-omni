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
  CarOutlined,
  WalletOutlined,
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
    key: '/logistics',
    icon: <CarOutlined />,
    label: '物流管理',
  },
  {
    key: '/finance',
    icon: <WalletOutlined />,
    label: '财务管理',
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
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#58a6ff',
            fontSize: collapsed ? '12px' : '14px',
            fontWeight: 'bold',
            letterSpacing: '0.5px',
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {collapsed ? 'LSO' : 'Luffy Store Omni'}
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
            fontSize: '16px', 
            fontWeight: 'bold',
            color: '#c9d1d9',
            letterSpacing: '1px',
            fontFamily: 'JetBrains Mono, monospace',
          }}>
            > 多店铺管理系统_
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

