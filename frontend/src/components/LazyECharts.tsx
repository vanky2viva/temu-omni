import { lazy, Suspense, useEffect, useState } from 'react'
import { Spin } from 'antd'
import type { EChartsReactProps } from 'echarts-for-react'

const LazyEChartsCore = lazy(async () => {
  const mod = await import('echarts-for-react')
  return { default: mod.default }
})

export default function LazyECharts(props: EChartsReactProps) {
  const [echartsLib, setEchartsLib] = useState<any>(null)

  useEffect(() => {
    let mounted = true
    import('echarts').then((lib) => {
      if (mounted) setEchartsLib(lib)
    })
    return () => {
      mounted = false
    }
  }, [])

  const fallback = (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: props.style?.height || 200 }}>
      <Spin />
    </div>
  )

  if (!echartsLib) {
    return fallback
  }

  return (
    <Suspense fallback={fallback}>
      <LazyEChartsCore {...props} echarts={echartsLib} />
    </Suspense>
  )
}
