/**清理前端缓存工具*/
export function clearAllCache() {
  // 清理 localStorage
  localStorage.clear()
  
  // 清理 sessionStorage
  sessionStorage.clear()
  
  // 清理 React Query 缓存（如果可用）
  if (window.queryClient) {
    window.queryClient.clear()
  }
  
  console.log('✅ 前端缓存已清理')
}

// 在页面加载时自动清理旧数据缓存
if (typeof window !== 'undefined') {
  // 检查是否需要清理缓存（可以通过版本号或时间戳控制）
  const lastClearTime = localStorage.getItem('lastCacheClear')
  const now = Date.now()
  
  // 如果超过1小时未清理，自动清理
  if (!lastClearTime || (now - parseInt(lastClearTime)) > 3600000) {
    // 只清理数据缓存，保留主题设置
    const theme = localStorage.getItem('theme')
    const token = localStorage.getItem('token')
    const user = localStorage.getItem('user')
    
    localStorage.clear()
    sessionStorage.clear()
    
    // 恢复必要的设置
    if (theme) localStorage.setItem('theme', theme)
    if (token) localStorage.setItem('token', token)
    if (user) localStorage.setItem('user', user)
    
    localStorage.setItem('lastCacheClear', now.toString())
  }
}



