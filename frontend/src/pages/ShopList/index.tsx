import React from 'react'
import { Button } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import UnifiedTable from '@/components/Table'
import { useShopList } from './hooks/useShopList'
import { createShopTableColumns } from './components/ShopTableColumns'
import ShopModal from './components/ShopModal'
import SyncProgressModal from './components/SyncProgressModal'
import AuthModal from './components/AuthModal'
import ImportDataModal from '@/components/ImportDataModal'

const ShopList: React.FC = () => {
  const {
    shops,
    isLoading,
    isModalOpen,
    setIsModalOpen,
    editingShop,
    setEditingShop,
    isImportModalOpen,
    setIsImportModalOpen,
    importingShop,
    setImportingShop,
    syncingShopId,
    syncProgress,
    syncProgressModalVisible,
    setSyncProgressModalVisible,
    syncLogs,
    authModalShop,
    setAuthModalShop,
    createMutation,
    updateMutation,
    deleteMutation,
    syncMutation,
    authorizeMutation,
    modal,
  } = useShopList()

  const columns = createShopTableColumns({
    onSync: (shop) => {
      modal.confirm({
        title: '同步店铺数据',
        content: `确定要同步店铺 ${shop.shop_name} 的数据吗？`,
        onOk: () => syncMutation.mutate({ shopId: shop.id, fullSync: true }),
      })
    },
    onAuth: (shop) => setAuthModalShop(shop),
    onImport: (shop) => {
      setImportingShop(shop)
      setIsImportModalOpen(true)
    },
    onEdit: (shop) => {
      setEditingShop(shop)
      setIsModalOpen(true)
    },
    onDelete: (id) => {
      modal.confirm({
        title: '确认删除',
        content: '确定要删除这个店铺吗？此操作将同时删除相关的所有订单和商品数据。',
        okType: 'danger',
        onOk: () => deleteMutation.mutate(id),
      })
    },
    syncingShopId,
    isSyncing: syncMutation.isPending,
  })

  return (
    <div className="shop-list-container">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>店铺管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingShop(null)
            setIsModalOpen(true)
          }}
        >
          添加店铺
        </Button>
      </div>

      <UnifiedTable
        variant="default"
        columns={columns}
        dataSource={Array.isArray(shops) ? shops : []}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        pagination={{
          pageSize: 50,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      <ShopModal
        visible={isModalOpen}
        shop={editingShop}
        loading={createMutation.isPending || updateMutation.isPending}
        onOk={(values) => {
          if (editingShop) updateMutation.mutate({ id: editingShop.id, data: values })
          else createMutation.mutate(values)
        }}
        onCancel={() => setIsModalOpen(false)}
      />

      <SyncProgressModal
        visible={syncProgressModalVisible}
        progress={syncProgress}
        logs={syncLogs}
        onCancel={() => setSyncProgressModalVisible(false)}
      />

      {authModalShop && (
        <AuthModal
          visible={!!authModalShop}
          shopName={authModalShop.shop_name}
          loading={authorizeMutation.isPending}
          onOk={(values) => authorizeMutation.mutate({ id: authModalShop.id, ...values })}
          onCancel={() => setAuthModalShop(null)}
        />
      )}

      {importingShop && (
        <ImportDataModal
          visible={isImportModalOpen}
          shopId={importingShop.id}
          shopName={importingShop.shop_name}
          onClose={() => setIsImportModalOpen(false)}
        />
      )}
    </div>
  )
}

export default ShopList

