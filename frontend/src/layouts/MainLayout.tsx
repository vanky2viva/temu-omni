import { useEffect, useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Switch, theme, Dropdown, Button, Avatar } from 'antd'
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
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

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
    label: '销量统计',
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
  const [isDark, setIsDark] = useState<boolean>(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'light') return false
    if (saved === 'dark') return true
    return true
  })
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('theme-dark', 'theme-light')
    root.classList.add(isDark ? 'theme-dark' : 'theme-light')
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  const user = JSON.parse(localStorage.getItem('user') || '{}')

  return (
    <ConfigProvider theme={{ algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm }}>
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
            background: isDark ? '#161b22' : '#ffffff',
            border: isDark ? '1px solid #30363d' : '1px solid #f0f0f0',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isDark ? '#58a6ff' : '#1677ff',
            fontSize: collapsed ? '12px' : '14px',
            fontWeight: 'bold',
            letterSpacing: '0.5px',
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {collapsed ? 'LSO' : 'Luffy Store Omni'}
        </div>
        <Menu
          theme={isDark ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s', background: 'transparent' }}>
        <Header className="site-header" style={{ padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ 
            fontSize: '16px', 
            fontWeight: 'bold',
            color: isDark ? '#c9d1d9' : '#1f2328',
            letterSpacing: '1px',
            fontFamily: 'JetBrains Mono, monospace',
          }}>
            {'> 多店铺管理系统_'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ color: isDark ? '#9aa0a6' : '#6b7280', fontSize: 12 }}>主题</span>
            <Switch
              checkedChildren="暗"
              unCheckedChildren="亮"
              checked={isDark}
              onChange={setIsDark}
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar size="small" icon={<UserOutlined />} />
                <span style={{ color: isDark ? '#c9d1d9' : '#1f2328' }}>
                  {user.username || '用户'}
                </span>
              </Button>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 16px' }}>
          <div className="site-content" style={{ padding: 24, minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
    </ConfigProvider>
  )
}

export default MainLayout

