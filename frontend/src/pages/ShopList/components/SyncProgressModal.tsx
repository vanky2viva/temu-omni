import React from 'react'
import { Modal, Progress, Descriptions, Card, Typography, Button } from 'antd'
import type { SyncProgress } from '../types'

const { Text } = Typography

interface SyncProgressModalProps {
  visible: boolean
  onCancel: () => void
  progress: SyncProgress | null
  logs: any[]
}

const SyncProgressModal: React.FC<SyncProgressModalProps> = ({
  visible,
  onCancel,
  progress,
  logs,
}) => {
  if (!progress) return null

  const isRunning = progress.status === 'running'

  return (
    <Modal
      title="同步进度"
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="close" onClick={onCancel}>
          {isRunning ? '后台运行' : '关闭'}
        </Button>
      ]}
      closable={!isRunning}
      maskClosable={!isRunning}
      destroyOnClose
    >
      <Progress
        percent={progress.progress || 0}
        status={progress.status === 'error' ? 'exception' : isRunning ? 'active' : 'success'}
      />
      <div style={{ marginTop: 16 }}>
        <p><strong>当前状态：</strong>{progress.current_step || '准备中...'}</p>
        {isRunning && progress.time_info && (
          <div style={{ background: '#e6f7ff', padding: 12, borderRadius: 4, marginTop: 12 }}>
            <p>处理速度：{progress.time_info.processing_speed?.toFixed(1)} 订单/秒</p>
            <p>进度：{progress.time_info.processed_count} / {progress.time_info.total_count}</p>
          </div>
        )}
        <Card title="同步日志" size="small" style={{ marginTop: 16 }}>
          <div style={{ maxHeight: 200, overflow: 'auto', background: '#1e1e1e', color: '#d4d4d4', padding: 8, fontSize: 12 }}>
            {logs.map((log, i) => (
              <div key={i}>[{new Date(log.timestamp).toLocaleTimeString()}] {log.message}</div>
            ))}
          </div>
        </Card>
      </div>
    </Modal>
  )
}

export default SyncProgressModal

