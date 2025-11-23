import { useEffect, useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { ConfigProvider, Layout, Menu, Switch, theme, Dropdown, Button, Avatar, Drawer } from 'antd'
import {
  DashboardOutlined,
  ShopOutlined,
  ShoppingOutlined,
  ProductOutlined,
  BarChartOutlined,
  CarOutlined,
  WalletOutlined,
  LogoutOutlined,
  UserOutlined,
  RobotOutlined,
  MenuOutlined,
  GlobalOutlined,
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
    label: '订单列表',
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
    key: '/forggpt',
    icon: <RobotOutlined />,
    label: 'ForgGPT',
  },
]

function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
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

  // 检测是否为移动设备
  useEffect(() => {
    const checkMobile = () => {
      const isMobileWidth = window.innerWidth < 768
      setIsMobile(isMobileWidth)
      // 移动端默认收起侧边栏，桌面端默认展开
      setCollapsed(isMobileWidth)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('theme-dark', 'theme-light')
    root.classList.add(isDark ? 'theme-dark' : 'theme-light')
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
    // 移动端点击菜单后关闭抽屉
    if (isMobile) {
      setMobileMenuOpen(false)
    }
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

  const user = (() => {
    try {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : { username: '用户' }
    } catch {
      return { username: '用户' }
    }
  })()

  // 侧边栏菜单组件
  const menuComponent = (
    <>
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
          fontSize: collapsed && !isMobile ? '12px' : '14px',
          fontWeight: 'bold',
          letterSpacing: '0.5px',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        {collapsed && !isMobile ? 'LSO' : 'Luffy Store Omni'}
      </div>
      <Menu
        theme={isDark ? 'dark' : 'light'}
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </>
  )

  return (
    <ConfigProvider theme={{ algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm }}>
      <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          breakpoint="lg"
          collapsedWidth={isMobile ? 0 : 80}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
            zIndex: 100,
          }}
        >
          {menuComponent}
        </Sider>
      )}

      {/* 移动端抽屉菜单 */}
      {isMobile && (
        <Drawer
          title={
            <div style={{ 
              color: isDark ? '#c9d1d9' : '#1f2328',
              fontSize: '14px',
              fontWeight: 'bold',
              fontFamily: 'JetBrains Mono, monospace',
            }}>
              Luffy Store Omni
            </div>
          }
          placement="left"
          closable={true}
          onClose={() => setMobileMenuOpen(false)}
          open={mobileMenuOpen}
          bodyStyle={{ padding: 0 }}
          width={250}
        >
          {menuComponent}
        </Drawer>
      )}

      <Layout 
        style={{ 
          marginLeft: isMobile ? 0 : (collapsed ? 80 : 200), 
          transition: 'all 0.2s', 
          background: 'transparent' 
        }}
      >
        <Header 
          className="site-header" 
          style={{ 
            padding: isMobile ? '0 16px' : '0 32px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 99,
            height: isMobile ? 56 : 64,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* 移动端菜单按钮 */}
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileMenuOpen(true)}
                style={{
                  color: isDark ? '#c9d1d9' : '#1f2328',
                  fontSize: '18px',
                }}
              />
            )}
            <div style={{ 
              fontSize: isMobile ? '14px' : '16px', 
              fontWeight: 'bold',
              color: isDark ? '#c9d1d9' : '#1f2328',
              letterSpacing: '1px',
              fontFamily: 'JetBrains Mono, monospace',
              display: isMobile ? 'none' : 'block',
            }}>
              {'> 多店铺管理系统_'}
            </div>
            {isMobile && (
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 'bold',
                color: isDark ? '#c9d1d9' : '#1f2328',
                letterSpacing: '0.5px',
                fontFamily: 'JetBrains Mono, monospace',
              }}>
                管理系统
              </div>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? 8 : 12 }}>
            {!isMobile && (
              <span style={{ color: isDark ? '#9aa0a6' : '#6b7280', fontSize: 12 }}>主题</span>
            )}
            <Switch
              checkedChildren="暗"
              unCheckedChildren="亮"
              checked={isDark}
              onChange={setIsDark}
              size={isMobile ? 'small' : 'default'}
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button 
                type="text" 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: isMobile ? 4 : 8,
                  padding: isMobile ? '4px 8px' : undefined,
                }}
              >
                <Avatar size={isMobile ? 'small' : 'small'} icon={<UserOutlined />} />
                {!isMobile && (
                  <span style={{ color: isDark ? '#c9d1d9' : '#1f2328' }}>
                    {user.username || '用户'}
                  </span>
                )}
              </Button>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: isMobile ? '16px 8px 8px' : '24px 16px 16px' }}>
          <div 
            className="site-content" 
            style={{ 
              padding: isMobile ? 12 : 24, 
              minHeight: 360 
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
    </ConfigProvider>
  )
}

export default MainLayout

