# 前端集成指南 - 多店铺支持

**目标**: 在前端添加店铺选择功能，支持多店铺数据切换

---

## 📋 需要修改的文件

### 1. 创建店铺Store（状态管理）

**文件**: `frontend/src/stores/shopStore.ts`（新建）

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Shop {
  id: number;
  shop_id: string;
  shop_name: string;
  region: 'us' | 'eu' | 'global';
  environment: 'sandbox' | 'production';
  is_active: boolean;
  last_sync_at?: string;
}

interface ShopStore {
  shops: Shop[];
  currentShopId: number | null;
  currentShop: Shop | null;
  
  // Actions
  setShops: (shops: Shop[]) => void;
  setCurrentShop: (shopId: number) => void;
  fetchShops: () => Promise<void>;
  syncShopData: (shopId: number) => Promise<void>;
}

export const useShopStore = create<ShopStore>()(
  persist(
    (set, get) => ({
      shops: [],
      currentShopId: null,
      currentShop: null,
      
      setShops: (shops) => set({ shops }),
      
      setCurrentShop: (shopId) => {
        const shop = get().shops.find(s => s.id === shopId);
        set({ currentShopId: shopId, currentShop: shop || null });
      },
      
      fetchShops: async () => {
        try {
          const response = await fetch('/api/shops');
          const shops = await response.json();
          set({ shops });
          
          // 如果没有选中的店铺，自动选择第一个
          if (!get().currentShopId && shops.length > 0) {
            get().setCurrentShop(shops[0].id);
          }
        } catch (error) {
          console.error('获取店铺列表失败:', error);
        }
      },
      
      syncShopData: async (shopId) => {
        try {
          const response = await fetch(`/api/sync/shops/${shopId}/all`, {
            method: 'POST'
          });
          const result = await response.json();
          return result;
        } catch (error) {
          console.error('同步数据失败:', error);
          throw error;
        }
      }
    }),
    {
      name: 'shop-storage',
      partialState: (state) => ({
        currentShopId: state.currentShopId
      })
    }
  )
);
```

---

### 2. 创建店铺选择器组件

**文件**: `frontend/src/components/ShopSelector.tsx`（新建）

```typescript
import React from 'react';
import { Select, Tag, Space } from 'antd';
import { ShopOutlined, EnvironmentOutlined } from '@ant-design/icons';
import { useShopStore } from '../stores/shopStore';

const ShopSelector: React.FC = () => {
  const { shops, currentShopId, setCurrentShop } = useShopStore();
  
  const getEnvironmentColor = (env: string) => {
    return env === 'sandbox' ? 'orange' : 'green';
  };
  
  const getEnvironmentText = (env: string) => {
    return env === 'sandbox' ? '沙盒' : '生产';
  };
  
  return (
    <Select
      value={currentShopId}
      onChange={setCurrentShop}
      style={{ minWidth: 250 }}
      placeholder="选择店铺"
      optionLabelProp="label"
    >
      {shops.map(shop => (
        <Select.Option 
          key={shop.id} 
          value={shop.id}
          label={
            <Space>
              <ShopOutlined />
              {shop.shop_name}
            </Space>
          }
        >
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Space>
              <ShopOutlined />
              <span>{shop.shop_name}</span>
            </Space>
            <Space size={4}>
              <Tag color={getEnvironmentColor(shop.environment)}>
                {getEnvironmentText(shop.environment)}
              </Tag>
              <Tag icon={<EnvironmentOutlined />}>
                {shop.region.toUpperCase()}
              </Tag>
              {!shop.is_active && (
                <Tag color="red">已禁用</Tag>
              )}
            </Space>
          </Space>
        </Select.Option>
      ))}
    </Select>
  );
};

export default ShopSelector;
```

---

### 3. 创建同步按钮组件

**文件**: `frontend/src/components/SyncButton.tsx`（新建）

```typescript
import React, { useState } from 'react';
import { Button, message, Modal } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { useShopStore } from '../stores/shopStore';

interface SyncButtonProps {
  onSyncComplete?: () => void;
}

const SyncButton: React.FC<SyncButtonProps> = ({ onSyncComplete }) => {
  const [syncing, setSyncing] = useState(false);
  const { currentShopId, currentShop } = useShopStore();
  
  const handleSync = async () => {
    if (!currentShopId) {
      message.warning('请先选择店铺');
      return;
    }
    
    Modal.confirm({
      title: '确认同步',
      content: `确定要同步店铺"${currentShop?.shop_name}"的数据吗？这可能需要几分钟。`,
      okText: '确认同步',
      cancelText: '取消',
      onOk: async () => {
        setSyncing(true);
        const hide = message.loading('正在同步数据...', 0);
        
        try {
          const response = await fetch(`/api/sync/shops/${currentShopId}/all`, {
            method: 'POST'
          });
          const result = await response.json();
          
          if (result.success) {
            const orders = result.data?.results?.orders?.total || 0;
            message.success(`同步成功！共同步 ${orders} 个订单`);
            onSyncComplete?.();
          } else {
            message.error('同步失败：' + result.message);
          }
        } catch (error) {
          message.error('同步失败：' + error.message);
        } finally {
          hide();
          setSyncing(false);
        }
      }
    });
  };
  
  return (
    <Button
      type="primary"
      icon={<SyncOutlined spin={syncing} />}
      onClick={handleSync}
      loading={syncing}
      disabled={!currentShopId}
    >
      同步数据
    </Button>
  );
};

export default SyncButton;
```

---

### 4. 创建环境指示器组件

**文件**: `frontend/src/components/EnvironmentBadge.tsx`（新建）

```typescript
import React from 'react';
import { Alert } from 'antd';
import { useShopStore } from '../stores/shopStore';

const EnvironmentBadge: React.FC = () => {
  const { currentShop } = useShopStore();
  
  if (!currentShop || currentShop.environment !== 'sandbox') {
    return null;
  }
  
  return (
    <Alert
      message="沙盒环境"
      description="当前使用的是测试数据，不影响真实业务。数据仅用于演示和开发调试。"
      type="warning"
      showIcon
      closable
      style={{ marginBottom: 16 }}
    />
  );
};

export default EnvironmentBadge;
```

---

### 5. 更新主布局

**文件**: `frontend/src/layouts/MainLayout.tsx`

```typescript
// 在文件顶部导入
import ShopSelector from '../components/ShopSelector';
import SyncButton from '../components/SyncButton';
import { useShopStore } from '../stores/shopStore';

// 在组件内部
function MainLayout() {
  const { fetchShops } = useShopStore();
  
  // 组件加载时获取店铺列表
  useEffect(() => {
    fetchShops();
  }, []);
  
  return (
    <Layout>
      <Header>
        {/* 在Header中添加店铺选择器和同步按钮 */}
        <Space>
          <ShopSelector />
          <SyncButton onSyncComplete={() => {
            // 同步完成后刷新数据
            window.location.reload(); // 或使用 queryClient.invalidateQueries()
          }} />
        </Space>
      </Header>
      
      {/* ... 其他内容 */}
    </Layout>
  );
}
```

---

### 6. 更新API请求（添加shop_id参数）

**方法1: 使用axios拦截器（推荐）**

**文件**: `frontend/src/services/api.ts`

```typescript
import axios from 'axios';
import { useShopStore } from '../stores/shopStore';

const api = axios.create({
  baseURL: '/api'
});

// 请求拦截器：自动添加 shop_id
api.interceptors.request.use((config) => {
  const { currentShopId } = useShopStore.getState();
  
  if (currentShopId) {
    // 如果是GET请求，添加到query参数
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        shop_id: currentShopId
      };
    }
  }
  
  return config;
});

export default api;
```

**方法2: 更新每个API调用**

```typescript
// 修改前
const fetchOrders = async () => {
  const response = await fetch('/api/orders');
  return response.json();
};

// 修改后
const fetchOrders = async (shopId: number) => {
  const response = await fetch(`/api/orders?shop_id=${shopId}`);
  return response.json();
};

// 使用
const { currentShopId } = useShopStore();
const orders = await fetchOrders(currentShopId);
```

---

### 7. 更新页面组件

**示例**: `frontend/src/pages/OrderList.tsx`

```typescript
import React, { useEffect } from 'react';
import { useShopStore } from '../stores/shopStore';
import EnvironmentBadge from '../components/EnvironmentBadge';

function OrderList() {
  const { currentShopId, currentShop } = useShopStore();
  const [orders, setOrders] = useState([]);
  
  useEffect(() => {
    if (currentShopId) {
      fetchOrders();
    }
  }, [currentShopId]); // 当店铺切换时重新获取数据
  
  const fetchOrders = async () => {
    const response = await fetch(`/api/orders?shop_id=${currentShopId}`);
    const data = await response.json();
    setOrders(data);
  };
  
  return (
    <div>
      <EnvironmentBadge /> {/* 显示环境提示 */}
      
      <div>
        <h2>订单列表 - {currentShop?.shop_name}</h2>
        {/* ... 订单列表内容 */}
      </div>
    </div>
  );
}
```

---

## 🎨 UI建议

### 1. 在Header中的布局

```tsx
<Header>
  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
    {/* 左侧：Logo */}
    <div>
      <Logo />
    </div>
    
    {/* 中间：店铺选择器 */}
    <div>
      <ShopSelector />
    </div>
    
    {/* 右侧：同步按钮和其他操作 */}
    <Space>
      <SyncButton />
      <UserMenu />
    </Space>
  </Space>
</Header>
```

### 2. 环境标识样式

```typescript
// 沙盒环境：橙色警告
<Tag color="orange" icon={<ExperimentOutlined />}>
  沙盒环境
</Tag>

// 生产环境：绿色正常
<Tag color="green" icon={<CheckCircleOutlined />}>
  生产环境
</Tag>
```

### 3. 店铺切换确认

```typescript
const handleShopChange = (shopId: number) => {
  const shop = shops.find(s => s.id === shopId);
  
  if (shop.environment === 'production') {
    Modal.confirm({
      title: '切换到生产环境',
      content: '您正在切换到生产环境，将显示真实业务数据。',
      okText: '确认切换',
      onOk: () => setCurrentShop(shopId)
    });
  } else {
    setCurrentShop(shopId);
  }
};
```

---

## 📊 数据流图

```
用户选择店铺
    ↓
更新 currentShopId (Store)
    ↓
触发 useEffect (依赖 currentShopId)
    ↓
发起API请求 (带 shop_id 参数)
    ↓
后端筛选该店铺的数据
    ↓
返回数据并更新界面
```

---

## ✅ 检查清单

### 必须完成

- [ ] 创建 `shopStore.ts`
- [ ] 创建 `ShopSelector.tsx`
- [ ] 创建 `SyncButton.tsx`
- [ ] 更新 `MainLayout.tsx`（添加店铺选择器）
- [ ] 更新所有数据请求（添加 `shop_id` 参数）

### 推荐完成

- [ ] 创建 `EnvironmentBadge.tsx`
- [ ] 添加店铺切换确认
- [ ] 添加同步进度提示
- [ ] 添加同步状态显示
- [ ] 实现数据缓存（避免重复请求）

### 可选完成

- [ ] 添加店铺管理页面
- [ ] 实现多店铺数据对比
- [ ] 添加数据导出功能
- [ ] 实现自动同步定时器

---

## 🚀 快速开始

### 步骤 1: 安装依赖（如果需要）

```bash
cd frontend
npm install zustand
```

### 步骤 2: 创建必要的文件

```bash
# 创建店铺相关目录
mkdir -p src/stores
mkdir -p src/components

# 复制本文档中的代码到对应文件
```

### 步骤 3: 测试店铺切换

1. 启动前端: `npm run dev`
2. 查看店铺选择器是否显示
3. 尝试切换店铺
4. 查看数据是否正确更新

---

## 🐛 常见问题

### Q1: 店铺选择器不显示？
**A**: 检查 `fetchShops()` 是否在 `MainLayout` 中调用

### Q2: 切换店铺后数据没变？
**A**: 确保 `useEffect` 依赖项包含 `currentShopId`

### Q3: 同步按钮无反应？
**A**: 检查后端是否启动，API端点是否正确

### Q4: 如何清除选中的店铺？
**A**: 使用 `localStorage.removeItem('shop-storage')`

---

## 📚 相关资源

- **后端集成文档**: `INTEGRATION_GUIDE.md`
- **API测试指南**: `QUICKSTART_API.md`
- **完整报告**: `API_INTEGRATION_COMPLETE.md`

---

**前端集成指南** | 更新于 2025-10-30

