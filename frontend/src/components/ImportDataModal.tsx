import React, { useState } from 'react'
import { Modal, Upload, Tabs, Button, message, Space, Typography, Alert, Input, Radio } from 'antd'
import { InboxOutlined, FileExcelOutlined, LinkOutlined, GlobalOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { importApi } from '@/services/api'

const { Dragger } = Upload
const { TabPane } = Tabs
const { Text, Paragraph } = Typography

interface ImportDataModalProps {
  visible: boolean
  shopId: number
  shopName: string
  onClose: () => void
}

const ImportDataModal: React.FC<ImportDataModalProps> = ({
  visible,
  shopId,
  shopName,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('orders')  // 默认为订单
  const [importMode, setImportMode] = useState<'file' | 'url'>('file')
  const [fileList, setFileList] = useState<any[]>([])
  const [onlineUrl, setOnlineUrl] = useState('')
  const [password, setPassword] = useState('')
  const queryClient = useQueryClient()

  // 订单导入（文件）
  const importOrdersMutation = useMutation({
    mutationFn: (file: File) => importApi.importOrders(shopId, file),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('订单数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  // 订单导入（在线表格）
  const importOrdersFromUrlMutation = useMutation({
    mutationFn: ({ url, password }: { url: string; password?: string }) => 
      importApi.importOrdersFromUrl(shopId, url, password),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('订单数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  // 活动导入（文件）
  const importActivitiesMutation = useMutation({
    mutationFn: (file: File) => importApi.importActivities(shopId, file),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('活动数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  // 商品导入（文件）
  const importProductsMutation = useMutation({
    mutationFn: (file: File) => importApi.importProducts(shopId, file),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('商品数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  // 活动导入（在线表格）
  const importActivitiesFromUrlMutation = useMutation({
    mutationFn: ({ url, password }: { url: string; password?: string }) => 
      importApi.importActivitiesFromUrl(shopId, url, password),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('活动数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  // 商品导入（在线表格）
  const importProductsFromUrlMutation = useMutation({
    mutationFn: ({ url, password }: { url: string; password?: string }) => 
      importApi.importProductsFromUrl(shopId, url, password),
    onSuccess: (response: any) => {
      message.destroy('import')
      const data = response?.data || response
      showSuccessModal('商品数据', data)
      setFileList([])
      setOnlineUrl('')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
    },
    onError: (error: any) => {
      handleError(error)
    },
  })

  const showSuccessModal = (dataType: string, data: any) => {
    Modal.success({
      title: '✅ 导入成功',
      content: (
        <div>
          <p>{dataType}已成功导入！</p>
          <div style={{ marginTop: 12, padding: 12, background: '#f6f8fa', borderRadius: 4 }}>
            <p style={{ fontWeight: 'bold', marginBottom: 8 }}>导入统计：</p>
            <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
              <li>总行数: <strong>{data.total_rows}</strong></li>
              <li>成功: <strong style={{ color: '#52c41a' }}>{data.success_rows}</strong></li>
              {data.failed_rows > 0 && (
                <li>失败: <strong style={{ color: '#ff4d4f' }}>{data.failed_rows}</strong></li>
              )}
              {data.skipped_rows > 0 && (
                <li>跳过: <strong style={{ color: '#faad14' }}>{data.skipped_rows}</strong></li>
              )}
            </ul>
          </div>
        </div>
      ),
    })
  }

  const handleError = (error: any) => {
    message.destroy('import')
    const errorMsg = error?.response?.data?.detail || error?.message || '导入失败'
    message.error(errorMsg)
    Modal.error({
      title: '❌ 导入失败',
      content: errorMsg,
    })
  }

  const handleUpload = async () => {
    if (importMode === 'file') {
      // 多文件导入
      if (fileList.length === 0) {
        message.warning('请先选择文件')
        return
      }

      // 提取所有文件
      const files: File[] = []
      for (const fileItem of fileList) {
        const file = fileItem.originFileObj || fileItem
        if (file && file instanceof File) {
          files.push(file)
        }
      }

      if (files.length === 0) {
        message.error('没有有效的文件，请重新选择')
        return
      }

      message.loading({ 
        content: `正在导入 ${files.length} 个文件...`, 
        key: 'import', 
        duration: 0 
      })

      // 依次导入每个文件
      let totalSuccess = 0
      let totalFailed = 0
      let totalSkipped = 0
      let totalRows = 0

      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        try {
          message.loading({ 
            content: `正在导入文件 ${i + 1}/${files.length}: ${file.name}...`, 
            key: 'import', 
            duration: 0 
          })

          let result
          if (activeTab === 'orders') {
            result = await importApi.importOrders(shopId, file)
          } else if (activeTab === 'activities') {
            result = await importApi.importActivities(shopId, file)
          } else if (activeTab === 'products') {
            result = await importApi.importProducts(shopId, file)
          } else {
            continue
          }

          const data = result?.data || result
          if (data) {
            totalSuccess += data.success_rows || 0
            totalFailed += data.failed_rows || 0
            totalSkipped += data.skipped_rows || 0
            totalRows += data.total_rows || 0
          }
        } catch (error: any) {
          totalFailed++
          console.error(`文件 ${file.name} 导入失败:`, error)
          message.error(`文件 "${file.name}" 导入失败: ${error?.response?.data?.detail || error?.message || '未知错误'}`)
        }
      }

      message.destroy('import')

      // 显示汇总结果
      const dataType = activeTab === 'orders' ? '订单数据' : 
                       activeTab === 'activities' ? '活动数据' : '商品数据'
      
      Modal.success({
        title: `✅ ${files.length} 个文件导入完成`,
        content: (
          <div>
            <p>{dataType}已全部导入完成！</p>
            <div style={{ marginTop: 12, padding: 12, background: '#f6f8fa', borderRadius: 4 }}>
              <p style={{ fontWeight: 'bold', marginBottom: 8 }}>汇总统计：</p>
              <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
                <li>文件数量: <strong>{files.length}</strong></li>
                <li>总行数: <strong>{totalRows}</strong></li>
                <li>成功: <strong style={{ color: '#52c41a' }}>{totalSuccess}</strong></li>
                {totalFailed > 0 && (
                  <li>失败: <strong style={{ color: '#ff4d4f' }}>{totalFailed}</strong></li>
                )}
                {totalSkipped > 0 && (
                  <li>跳过: <strong style={{ color: '#faad14' }}>{totalSkipped}</strong></li>
                )}
              </ul>
            </div>
          </div>
        ),
      })

      // 刷新数据
      setFileList([])
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      queryClient.invalidateQueries({ queryKey: ['statistics'] })
      queryClient.invalidateQueries({ queryKey: ['sales-overview'] })
      queryClient.invalidateQueries({ queryKey: ['sku-sales-ranking'] })
    } else {
      // 在线表格导入
      if (!onlineUrl.trim()) {
        message.warning('请输入在线表格链接')
        return
      }

      // 验证URL格式
      if (!onlineUrl.includes('feishu.cn/sheets/')) {
        message.error('请输入有效的飞书表格链接')
        return
      }

      message.loading({ content: '正在从在线表格导入数据...', key: 'import', duration: 0 })

      if (activeTab === 'orders') {
        importOrdersFromUrlMutation.mutate({ url: onlineUrl, password: password || undefined })
      } else if (activeTab === 'activities') {
        importActivitiesFromUrlMutation.mutate({ url: onlineUrl, password: password || undefined })
      } else if (activeTab === 'products') {
        importProductsFromUrlMutation.mutate({ url: onlineUrl, password: password || undefined })
      }
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,  // 支持多文件上传
    fileList,
    accept: '.xlsx,.xls',
    beforeUpload: (file, fileList) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.type === 'application/vnd.ms-excel' ||
        file.name.endsWith('.xlsx') ||
        file.name.endsWith('.xls')
      
      if (!isExcel) {
        message.error(`文件 "${file.name}" 不是 Excel 文件！`)
        return Upload.LIST_IGNORE
      }

      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error(`文件 "${file.name}" 大小超过 10MB！`)
        return Upload.LIST_IGNORE
      }

      // 构建符合 UploadFile 格式的对象
      const uploadFile = {
        uid: `${Date.now()}-${Math.random()}`,
        name: file.name,
        status: 'done' as const,
        originFileObj: file,
      }
      
      // 添加到文件列表（支持多文件）
      setFileList((prev) => {
        // 检查是否已存在同名文件
        const exists = prev.some(f => f.name === file.name)
        if (exists) {
          message.warning(`文件 "${file.name}" 已存在，已跳过`)
          return prev
        }
        return [...prev, uploadFile]
      })
      return false // 阻止自动上传
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid))
    },
  }

  const handleClose = () => {
    setFileList([])
    setOnlineUrl('')
    setPassword('')
    setImportMode('file')
    setActiveTab('orders')
    onClose()
  }

  const isLoading = 
    importOrdersMutation.isPending ||
    importOrdersFromUrlMutation.isPending ||
    importActivitiesMutation.isPending || 
    importProductsMutation.isPending ||
    importActivitiesFromUrlMutation.isPending ||
    importProductsFromUrlMutation.isPending

  const canSubmit = importMode === 'file' ? fileList.length > 0 : onlineUrl.trim().length > 0

  return (
    <Modal
      title={`导入数据 - ${shopName}`}
      open={visible}
      onCancel={handleClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={isLoading}
          onClick={handleUpload}
          disabled={!canSubmit}
        >
          开始导入
        </Button>,
      ]}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <FileExcelOutlined />
              订单列表
            </span>
          }
          key="orders"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              message="导入说明"
              description={
                <div>
                  <Paragraph style={{ marginBottom: 8 }}>
                    请上传或提供<strong>「订单导出」</strong>数据。
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    • 必需列：订单编号、商品名称、数量、单价、订单金额、下单时间
                    <br />
                    • 重复的订单会自动跳过（根据订单编号）
                  </Text>
                </div>
              }
              type="info"
              showIcon
            />

            {/* 导入方式选择 */}
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>导入方式：</Text>
              <Radio.Group value={importMode} onChange={(e) => setImportMode(e.target.value)}>
                <Radio.Button value="file">
                  <FileExcelOutlined /> Excel文件
                </Radio.Button>
                <Radio.Button value="url">
                  <GlobalOutlined /> 在线表格
                </Radio.Button>
              </Radio.Group>
            </div>

            {/* 根据选择的方式显示不同的输入 */}
            {importMode === 'file' ? (
              <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持同时上传多个 .xlsx 和 .xls 格式文件，单个文件大小不超过 10MB
                </p>
                {fileList.length > 0 && (
                  <div style={{ marginTop: 12, padding: 8, background: '#f0f0f0', borderRadius: 4 }}>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 'bold' }}>
                      已选择 {fileList.length} 个文件：
                    </p>
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: 20, fontSize: 12 }}>
                      {fileList.map((file) => (
                        <li key={file.uid}>{file.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Dragger>
            ) : (
              <div>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  <LinkOutlined /> 在线表格链接：
                </Text>
                <Input.TextArea
                  rows={3}
                  value={onlineUrl}
                  onChange={(e) => setOnlineUrl(e.target.value)}
                  placeholder="粘贴飞书表格链接，例如：&#10;https://mcnkufobiqbi.feishu.cn/sheets/W3FwsqMtRhkOwQtmfhWcGjvrn1d"
                  style={{ marginBottom: 12 }}
                />
                
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  🔒 访问密码（可选）：
                </Text>
                <Input.Password
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="如果表格设置了密码保护，请输入密码"
                  style={{ marginBottom: 12 }}
                  allowClear
                />
                
                <Alert
                  message="安全提示"
                  description={
                    <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
                      <li>🔐 订单数据建议使用密码保护</li>
                      <li>✅ 实时同步：数据更新后无需重新上传</li>
                      <li>👥 团队协作：多人可以共同维护数据</li>
                      <li>📝 密码不会被存储，仅用于本次导入</li>
                    </ul>
                  }
                  type="info"
                  showIcon
                  style={{ fontSize: 12 }}
                />
              </div>
            )}
          </Space>
        </TabPane>

        <TabPane
          tab={
            <span>
              <FileExcelOutlined />
              活动列表
            </span>
          }
          key="activities"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              message="导入说明"
              description={
                <div>
                  <Paragraph style={{ marginBottom: 8 }}>
                    请上传或提供<strong>「活动商品明细」</strong>数据。
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    • 支持的列：商品信息、SPU ID、活动站点、活动销量、活动 GMV、活动商品曝光用户数等
                    <br />
                    • 重复的活动会自动跳过
                  </Text>
                </div>
              }
              type="info"
              showIcon
            />

            {/* 导入方式选择 */}
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>导入方式：</Text>
              <Radio.Group value={importMode} onChange={(e) => setImportMode(e.target.value)}>
                <Radio.Button value="file">
                  <FileExcelOutlined /> Excel文件
                </Radio.Button>
                <Radio.Button value="url">
                  <GlobalOutlined /> 在线表格
                </Radio.Button>
              </Radio.Group>
            </div>

            {/* 根据选择的方式显示不同的输入 */}
            {importMode === 'file' ? (
              <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持同时上传多个 .xlsx 和 .xls 格式文件，单个文件大小不超过 10MB
                </p>
                {fileList.length > 0 && (
                  <div style={{ marginTop: 12, padding: 8, background: '#f0f0f0', borderRadius: 4 }}>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 'bold' }}>
                      已选择 {fileList.length} 个文件：
                    </p>
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: 20, fontSize: 12 }}>
                      {fileList.map((file) => (
                        <li key={file.uid}>{file.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Dragger>
            ) : (
              <div>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  <LinkOutlined /> 在线表格链接：
                </Text>
                <Input.TextArea
                  rows={3}
                  value={onlineUrl}
                  onChange={(e) => setOnlineUrl(e.target.value)}
                  placeholder="粘贴飞书表格链接，例如：&#10;https://xxx.feishu.cn/sheets/Xd3SsrVlEhNoBXtawvlcryWVnJc?sheet=HPLHTM"
                  style={{ marginBottom: 12 }}
                />
                
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  🔒 访问密码（可选）：
                </Text>
                <Input.Password
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="如果表格设置了密码保护，请输入密码"
                  style={{ marginBottom: 12 }}
                  allowClear
                />
                
                <Alert
                  message="安全提示"
                  description={
                    <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
                      <li>🔐 推荐使用密码保护表格，保障数据安全</li>
                      <li>✅ 实时同步：数据更新后无需重新上传</li>
                      <li>👥 团队协作：多人可以共同维护数据</li>
                      <li>📝 密码不会被存储，仅用于本次导入</li>
                    </ul>
                  }
                  type="info"
                  showIcon
                  style={{ fontSize: 12 }}
                />
              </div>
            )}
          </Space>
        </TabPane>

        <TabPane
          tab={
            <span>
              <FileExcelOutlined />
              商品基础信息
            </span>
          }
          key="products"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              message="导入说明"
              description={
                <div>
                  <Paragraph style={{ marginBottom: 8 }}>
                    请上传或提供<strong>「商品基础信息」</strong>数据。
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    • 支持的列：商品名称、SKU ID、SPU ID、申报价格、类目、状态等
                    <br />
                    • 已存在的商品会更新价格信息
                  </Text>
                </div>
              }
              type="info"
              showIcon
            />

            {/* 导入方式选择 */}
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>导入方式：</Text>
              <Radio.Group value={importMode} onChange={(e) => setImportMode(e.target.value)}>
                <Radio.Button value="file">
                  <FileExcelOutlined /> Excel文件
                </Radio.Button>
                <Radio.Button value="url">
                  <GlobalOutlined /> 在线表格
                </Radio.Button>
              </Radio.Group>
            </div>

            {/* 根据选择的方式显示不同的输入 */}
            {importMode === 'file' ? (
              <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持同时上传多个 .xlsx 和 .xls 格式文件，单个文件大小不超过 10MB
                </p>
                {fileList.length > 0 && (
                  <div style={{ marginTop: 12, padding: 8, background: '#f0f0f0', borderRadius: 4 }}>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 'bold' }}>
                      已选择 {fileList.length} 个文件：
                    </p>
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: 20, fontSize: 12 }}>
                      {fileList.map((file) => (
                        <li key={file.uid}>{file.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Dragger>
            ) : (
              <div>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  <LinkOutlined /> 在线表格链接：
                </Text>
                <Input.TextArea
                  rows={3}
                  value={onlineUrl}
                  onChange={(e) => setOnlineUrl(e.target.value)}
                  placeholder="粘贴飞书表格链接，例如：&#10;https://xxx.feishu.cn/sheets/Xd3SsrVlEhNoBXtawvlcryWVnJc?sheet=HPLHTM"
                  style={{ marginBottom: 12 }}
                />
                
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  🔒 访问密码（可选）：
                </Text>
                <Input.Password
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="如果表格设置了密码保护，请输入密码"
                  style={{ marginBottom: 12 }}
                  allowClear
                />
                
                <Alert
                  message="安全提示"
                  description={
                    <ul style={{ fontSize: 12, margin: 0, paddingLeft: 20 }}>
                      <li>🔐 推荐使用密码保护表格，保障数据安全</li>
                      <li>✅ 实时同步：数据更新后无需重新上传</li>
                      <li>👥 团队协作：多人可以共同维护数据</li>
                      <li>📝 密码不会被存储，仅用于本次导入</li>
                    </ul>
                  }
                  type="info"
                  showIcon
                  style={{ fontSize: 12 }}
                />
              </div>
            )}
          </Space>
        </TabPane>
      </Tabs>
    </Modal>
  )
}

export default ImportDataModal
