import { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'

interface StateOrderData {
  state: string  // 州名称或州代码
  count: number   // 订单数量
}

interface StateHeatmapProps {
  data: StateOrderData[]
  height?: number
}

// 美国各州名称到代码的映射
const stateNameToCode: Record<string, string> = {
  'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
  'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
  'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
  'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
  'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
  'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
  'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
  'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
  'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
  'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
  'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
  'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
  'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC'
}

// 州代码到名称的映射
const stateCodeToName: Record<string, string> = {
  'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
  'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
  'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
  'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
  'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
  'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
  'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
  'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
  'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
  'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
  'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
  'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
  'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

function StateHeatmap({ data, height = 500 }: StateHeatmapProps) {
  const [mapLoaded, setMapLoaded] = useState(false)
  const [mapLoadFailed, setMapLoadFailed] = useState(false)

  // 规范化州代码，将名称或代码统一为代码
  const normalizedData = useMemo(() => {
    const stateCountMap: Record<string, number> = {}
    
    data.forEach(item => {
      let stateCode = ''
      
      // 尝试匹配州代码（2个大写字母）
      if (/^[A-Z]{2}$/.test(item.state.trim())) {
        stateCode = item.state.trim().toUpperCase()
      } 
      // 尝试匹配州名称
      else {
        const code = stateNameToCode[item.state] || stateNameToCode[item.state.trim()]
        stateCode = code || item.state.trim().toUpperCase()
      }
      
      if (stateCode && stateCodeToName[stateCode]) {
        stateCountMap[stateCode] = (stateCountMap[stateCode] || 0) + item.count
      }
    })
    
    return Object.entries(stateCountMap).map(([code, count]) => ({
      name: code,  // 使用州代码作为名称，与地图注册时的名称匹配
      value: count,
      code,
      fullName: stateCodeToName[code] || code  // 保存州全名用于显示
    }))
  }, [data])

  // 加载并注册美国地图数据
  useEffect(() => {
    if (echarts.getMap('USA')) {
      setMapLoaded(true)
      return
    }

    // 使用在线资源加载美国各州地图 GeoJSON
    fetch('https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json')
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to load map data')
        }
        return res.json()
      })
      .then(geoJson => {
        // 处理 GeoJSON，确保州名称映射正确
        if (geoJson.features) {
          geoJson.features = geoJson.features.map((feature: any) => {
            const stateName = feature.properties?.name || 
                            feature.properties?.NAME || 
                            feature.properties?.NAME_1 ||
                            feature.properties?.state ||
                            feature.properties?.STATE
            
            let stateCode = stateNameToCode[stateName]
            
            if (!stateCode && stateName) {
              stateCode = Object.keys(stateCodeToName).find(
                code => stateCodeToName[code].toLowerCase() === stateName.toLowerCase()
              )
            }
            
            if (stateCode) {
              return {
                ...feature,
                properties: {
                  ...feature.properties,
                  name: stateCode,
                  fullName: stateName,
                }
              }
            }
            
            if (/^[A-Z]{2}$/.test(stateName)) {
              return {
                ...feature,
                properties: {
                  ...feature.properties,
                  name: stateName.toUpperCase(),
                  fullName: stateCodeToName[stateName.toUpperCase()] || stateName,
                }
              }
            }
            
            return feature
          })
        }
        
        echarts.registerMap('USA', geoJson)
        setMapLoaded(true)
      })
      .catch(() => {
        console.warn('无法加载美国地图数据，将使用柱状图展示')
        setMapLoadFailed(true)
      })
  }, [])

  const maxValue = useMemo(() => {
    if (normalizedData.length === 0) return 1
    return Math.max(...normalizedData.map(d => d.value))
  }, [normalizedData])

  // 创建地图配置选项
  const option = useMemo(() => {
    return {
      title: {
        text: '订单接收地区分布热力图',
        left: 'center',
        textStyle: {
          color: '#c9d1d9',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const fullName = params.data?.fullName || stateCodeToName[params.name] || params.name
          return `${fullName} (${params.name})<br/>订单数量: ${params.value || 0}`
        },
      },
      visualMap: {
        min: 0,
        max: maxValue,
        left: 'left',
        top: 'bottom',
        text: ['高', '低'],
        calculable: true,
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        },
        textStyle: {
          color: '#c9d1d9',
        },
      },
      series: [
        {
          name: '订单数量',
          type: 'map',
          map: 'USA',
          roam: true,
          emphasis: {
            label: {
              show: true,
            },
          },
          data: normalizedData,
          label: {
            show: true,
            fontSize: 10,
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 1,
          },
        },
      ],
    }
  }, [normalizedData, maxValue])

  // 备选方案：使用柱状图展示各州订单数量
  const barOption = useMemo(() => ({
    title: {
      text: '订单接收地区分布（按州统计）',
      left: 'center',
      textStyle: {
        color: '#c9d1d9',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: normalizedData.map(d => d.code),
      axisLabel: {
        rotate: 45,
        color: '#c9d1d9',
      },
    },
    yAxis: {
      type: 'value',
      name: '订单数量',
      axisLabel: {
        color: '#c9d1d9',
      },
    },
    visualMap: {
      min: 0,
      max: maxValue,
      dimension: 1,
      orient: 'vertical',
      right: 10,
      top: 'center',
      text: ['高', '低'],
      calculable: true,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      },
      textStyle: {
        color: '#c9d1d9',
      },
    },
    series: [
      {
        name: '订单数量',
        type: 'bar',
        data: normalizedData.map(d => ({
          value: d.value,
          name: d.name,
          code: d.code,
        })),
      },
    ],
  }), [normalizedData, maxValue])

  // 如果地图数据还未加载，显示加载中
  if (!mapLoaded && !mapLoadFailed) {
    return (
      <div style={{ 
        height: `${height}px`, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#8b949e'
      }}>
        正在加载地图数据...
      </div>
    )
  }

  // 如果地图已加载，显示地图
  if (mapLoaded && echarts.getMap('USA')) {
    return (
      <ReactECharts
        option={option}
        style={{ height: `${height}px`, width: '100%' }}
        notMerge={true}
      />
    )
  }

  // 如果地图加载失败或无法使用地图，使用柱状图作为备选方案
  return (
    <ReactECharts
      option={barOption}
      style={{ height: `${height}px`, width: '100%' }}
      notMerge={true}
    />
  )
}

export default StateHeatmap

