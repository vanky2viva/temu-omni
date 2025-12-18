import React from 'react'
import { Modal } from 'antd'
import UnifiedTable from '@/components/Table'
import { useProductList } from './hooks/useProductList'
import ProductFilters from './components/ProductFilters'
import { createProductTableColumns } from './components/ProductTableColumns'
import CostModal from './components/CostModal'

const ProductList: React.FC = () => {
  const {
    filters,
    setFilters,
    shops,
    products,
    isLoading,
    isCostModalOpen,
    setIsCostModalOpen,
    selectedProduct,
    managerOptions,
    categoryOptions,
    isEditingSupplyPrice,
    setIsEditingSupplyPrice,
    editingSupplyPrice,
    setEditingSupplyPrice,
    isEditingCostPrice,
    setIsEditingCostPrice,
    editingCostPrice,
    setEditingCostPrice,
    createCostMutation,
    updateManagerMutation,
    updateCostPriceMutation,
    updateSupplyPriceMutation,
    clearProductsMutation,
    queryClient,
  } = useProductList()

  const handleClearProducts = () => {
    Modal.confirm({
      title: '确认清理商品数据',
      content: filters.shopId 
        ? `确定要清理当前店铺的所有商品数据吗？此操作不可恢复！`
        : '确定要清理所有店铺的商品数据吗？此操作不可恢复！',
      okText: '确认',
      okType: 'danger',
      onOk: () => clearProductsMutation.mutate(filters.shopId),
    })
  }

  const columns = createProductTableColumns({
    shops,
    managerOptions,
    onUpdateManager: (id, manager) => updateManagerMutation.mutate({ id, manager }),
    isEditingSupplyPrice,
    setIsEditingSupplyPrice,
    editingSupplyPrice,
    setEditingSupplyPrice,
    onSaveSupplyPrice: (id, price) => updateSupplyPriceMutation.mutate({ id, current_price: price }),
    isSupplyPriceLoading: updateSupplyPriceMutation.isPending,
    isEditingCostPrice,
    setIsEditingCostPrice,
    editingCostPrice,
    setEditingCostPrice,
    onSaveCostPrice: (id, price) => updateCostPriceMutation.mutate({ id, cost_price: price }),
    isCostPriceLoading: updateCostPriceMutation.isPending,
  })

  return (
    <div className="product-list-container">
      <ProductFilters
        filters={filters}
        setFilters={setFilters}
        shops={shops}
        managerOptions={managerOptions}
        categoryOptions={categoryOptions}
        onClearProducts={handleClearProducts}
        isClearing={clearProductsMutation.isPending}
        onSearch={() => queryClient.invalidateQueries({ queryKey: ['products'] })}
      />

      <UnifiedTable
        variant="default"
        columns={columns}
        dataSource={products}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1400 }}
      />

      {selectedProduct && (
        <CostModal
          visible={isCostModalOpen}
          productName={selectedProduct.product_name}
          loading={createCostMutation.isPending}
          onOk={(values) => createCostMutation.mutate(values)}
          onCancel={() => setIsCostModalOpen(false)}
        />
      )}
    </div>
  )
}

export default ProductList

