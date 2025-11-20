/**
 * 前端缓存清理辅助工具
 * 在浏览器控制台执行 clearAllCache() 可以清理所有缓存
 */

export function clearAllCache() {
  try {
    // 保存必要的设置
    const theme = localStorage.getItem('theme')
    const token = localStorage.getItem('token')
    const user = localStorage.getItem('user')
    
    // 清理所有存储
    localStorage.clear()
    sessionStorage.clear()
    
    // 恢复必要的设置
    if (theme) localStorage.setItem('theme', theme)
    if (token) localStorage.setItem('token', token)
    if (user) localStorage.setItem('user', user)
    
    // 清理 React Query 缓存
    if (typeof window !== 'undefined' && (window as any).queryClient) {
      (window as any).queryClient.clear()
    }
    
    console.log('✅ 前端缓存已清理（已保留登录信息和主题设置）')
    console.log('请刷新页面以查看最新数据')
    
    return true
  } catch (error) {
    console.error('清理缓存失败:', error)
    return false
  }
}

// 挂载到 window 对象，方便在控制台调用
if (typeof window !== 'undefined') {
  (window as any).clearAllCache = clearAllCache
}


