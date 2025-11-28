# 数据获取优化方案

## 一、当前问题分析

### 1.1 重复的数据获取

#### 前端重复调用
| 页面 | 使用的API | 数据内容 | 重复情况 |
|------|----------|---------|---------|
| Dashboard | `statisticsApi.getOverview()` | 总订单数、GMV、利润 | 与 Finance、OrderList 重复 |
| Dashboard | `statisticsApi.getDaily()` | 每日趋势数据 | 与 Statistics、FrogGPT 重复 |
| Dashboard | `analyticsApi.getSalesOverview()` | 销量总览 | 与 SalesStatistics、Finance 重复 |
| Statistics | `statisticsApi.getDaily()` | 每日统计 | 与 Dashboard、FrogGPT 重复 |
| Statistics | `statisticsApi.getWeekly()` | 每周统计 | 独立 |
| Statistics | `statisticsApi.getMonthly()` | 每月统计 | 独立 |
| FrogGPT | `frogGptApi.getDataSummary()` | 数据摘要（GMV、订单、利润） | 与 Dashboard 重复 |
| FrogGPT | `statisticsApi.getDaily()` | 每日趋势 | 与 Dashboard、Statistics 重复 |
| FrogGPT | `analyticsApi.getSkuSalesRanking()` | SKU排行 | 与 SalesStatistics 重复 |
| SalesStatistics | `analyticsApi.getSalesOverview()` | 销量总览 | 与 Dashboard、Finance 重复 |
| SalesStatistics | `analyticsApi.getSkuSalesRanking()` | SKU排行 | 与 FrogGPT 重复 |
| Finance | `analyticsApi.getSalesOverview()` | 销量总览 | 与 Dashboard、SalesStatistics 重复 |
| Finance | `statisticsApi.getOverview()` | 总览统计 | 与 Dashboard 重复 |

### 1.2 后端重复计算

#### 相同数据在不同端点重复计算
1. **订单总览统计** (`total_orders`, `total_gmv`, `total_profit`, `delay_rate`)
   - `/statistics/overview/` - 使用 `StatisticsService.get_order_statistics()`
   - `/frog-gpt/data-summary` - 使用 `UnifiedStatisticsService.calculate_order_statistics()`
   - `/analytics/sales-overview` - 内部也计算类似数据

2. **每日趋势数据** (`daily_trends`)
   - `/statistics/daily/` - 使用 `StatisticsService.get_daily_statistics()`
   - `/analytics/sales-overview` - 返回 `daily_trends`
   - `/frog-gpt/data-summary` - 不直接返回，但AI需要

3. **SKU排行数据**
   - `/analytics/sku-sales-ranking` - 使用 `UnifiedStatisticsService.get_sku_statistics()`
   - `/frog-gpt/data-summary` - 返回 `top_skus`（前10）

### 1.3 缓存使用情况

#### 后端缓存
- `StatisticsService.get_order_statistics_cached()` - 使用 Redis 缓存，TTL=300秒（5分钟）
- `UnifiedStatisticsService` - 未使用缓存
- `analyticsApi` - 部分使用缓存（`refresh_cache` 参数）

#### 前端缓存
- React Query 默认缓存，但各页面使用不同的 `queryKey`，导致无法共享缓存

## 二、优化方案

### 2.1 统一数据端点设计

#### 核心数据端点
```
/api/statistics/unified/
  GET /overview?shop_ids=&start_date=&end_date=&days=
    - 返回：订单总览（订单数、GMV、利润、延误率等）
  
  GET /daily?shop_ids=&start_date=&end_date=&days=
    - 返回：每日趋势数据
  
  GET /sku-ranking?shop_ids=&start_date=&end_date=&limit=
    - 返回：SKU销售排行
  
  GET /manager-ranking?shop_ids=&start_date=&end_date=&limit=
    - 返回：负责人业绩排行
  
  GET /summary?shop_ids=&days=
    - 返回：综合数据摘要（包含 overview、top_skus、top_managers）
```

#### 兼容性处理
- 保留现有端点，但内部调用统一端点
- 逐步迁移各页面到统一端点

### 2.2 后端缓存优化

#### 缓存策略
```python
# 缓存键设计
cache_key = f"stats:unified:{endpoint}:{hash(params)}"

# 缓存层级
1. L1: 内存缓存（Python dict，TTL=60秒）- 高频访问
2. L2: Redis缓存（TTL=300秒）- 中频访问
3. L3: 数据库查询 - 低频访问

# 缓存失效
- 时间失效：TTL到期
- 主动失效：订单数据更新时，清除相关缓存
```

#### 实现位置
- `UnifiedStatisticsService` 添加缓存装饰器
- 使用 `functools.lru_cache` + Redis 双重缓存

### 2.3 前端缓存优化

#### React Query 配置
```typescript
// 统一 queryKey 格式
const queryKeys = {
  statistics: {
    overview: (params) => ['statistics', 'overview', params],
    daily: (params) => ['statistics', 'daily', params],
    skuRanking: (params) => ['statistics', 'sku-ranking', params],
    summary: (params) => ['statistics', 'summary', params],
  }
}

// 共享缓存配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分钟
      gcTime: 10 * 60 * 1000, // 10分钟（原 cacheTime）
      refetchOnWindowFocus: false,
    },
  },
})
```

#### 数据共享 Hook
```typescript
// hooks/useStatistics.ts
export const useStatisticsOverview = (params) => {
  return useQuery({
    queryKey: queryKeys.statistics.overview(params),
    queryFn: () => statisticsApi.getUnifiedOverview(params),
    staleTime: 5 * 60 * 1000,
  })
}
```

### 2.4 性能优化措施

#### 1. 批量查询
- 合并多个小查询为一个大查询
- 使用 GraphQL 风格的数据获取（可选）

#### 2. 增量更新
- 只获取变化的数据
- 使用 WebSocket 推送数据更新（可选）

#### 3. 数据预取
- 在用户可能访问的页面预取数据
- 使用 React Query 的 `prefetchQuery`

#### 4. 懒加载
- 非关键数据延迟加载
- 使用 `enabled` 选项控制查询时机

## 三、实施计划

### 阶段一：后端统一端点（1-2天）
1. 创建 `/api/statistics/unified/` 端点
2. 实现统一的数据获取逻辑
3. 添加缓存层
4. 保留现有端点，内部调用统一端点

### 阶段二：前端统一调用（2-3天）
1. 创建统一的数据获取 Hook
2. 更新各页面使用统一 Hook
3. 统一 queryKey 格式
4. 测试数据一致性

### 阶段三：性能优化（1-2天）
1. 优化缓存策略
2. 添加数据预取
3. 监控性能指标
4. 优化慢查询

### 阶段四：清理和文档（1天）
1. 移除重复代码
2. 更新 API 文档
3. 添加性能监控

## 四、预期效果

### 性能提升
- 减少重复计算：预计减少 50-70% 的数据库查询
- 缓存命中率：预计达到 80%+
- 响应时间：预计减少 30-50%

### 代码质量
- 代码复用率提升
- 维护成本降低
- 数据一致性保证

### 用户体验
- 页面加载速度提升
- 数据更新更及时
- 减少不必要的网络请求

## 五、注意事项

1. **向后兼容**：保留现有 API 端点，避免破坏现有功能
2. **数据一致性**：确保统一端点返回的数据与现有端点一致
3. **缓存失效**：订单数据更新时，及时清除相关缓存
4. **错误处理**：统一错误处理逻辑
5. **监控告警**：添加性能监控和告警机制

