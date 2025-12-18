/**
 * 统一统计数据获取 Hook
 * 
 * 提供统一的数据获取接口，避免重复计算和请求
 * 使用统一的 queryKey 格式，实现缓存共享
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { statisticsApi } from '@/services/api'

// 统一 queryKey 生成器
export const statisticsQueryKeys = {
  overview: (params?: any) => ['statistics', 'unified', 'overview', params],
  daily: (params?: any) => ['statistics', 'unified', 'daily', params],
  skuRanking: (params?: any) => ['statistics', 'unified', 'sku-ranking', params],
  managerRanking: (params?: any) => ['statistics', 'unified', 'manager-ranking', params],
  summary: (params?: any) => ['statistics', 'unified', 'summary', params],
}

// 统一配置
const DEFAULT_STALE_TIME = 5 * 60 * 1000 // 5分钟
const DEFAULT_GC_TIME = 10 * 60 * 1000 // 10分钟

export interface OverviewParams {
  shop_ids?: number[]
  start_date?: string
  end_date?: string
  days?: number
  use_cache?: boolean
}

export interface DailyParams {
  shop_ids?: number[]
  start_date?: string
  end_date?: string
  days?: number
  use_cache?: boolean
}

export interface SkuRankingParams {
  shop_ids?: number[]
  start_date?: string
  end_date?: string
  days?: number
  limit?: number
  use_cache?: boolean
}

export interface ManagerRankingParams {
  shop_ids?: number[]
  start_date?: string
  end_date?: string
  days?: number
  limit?: number
  use_cache?: boolean
}

export interface SummaryParams {
  shop_ids?: number[]
  days?: number
  use_cache?: boolean
}

/**
 * 获取订单总览统计
 */
export const useStatisticsOverview = (
  params?: OverviewParams,
  options?: Omit<UseQueryOptions<any, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: statisticsQueryKeys.overview(params),
    queryFn: () => statisticsApi.getUnifiedOverview(params),
    staleTime: DEFAULT_STALE_TIME,
    gcTime: DEFAULT_GC_TIME,
    ...options,
  })
}

/**
 * 获取每日统计数据
 */
export const useStatisticsDaily = (
  params?: DailyParams,
  options?: Omit<UseQueryOptions<any, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: statisticsQueryKeys.daily(params),
    queryFn: () => statisticsApi.getUnifiedDaily(params),
    staleTime: DEFAULT_STALE_TIME,
    gcTime: DEFAULT_GC_TIME,
    ...options,
  })
}

/**
 * 获取SKU销售排行
 */
export const useStatisticsSkuRanking = (
  params?: SkuRankingParams,
  options?: Omit<UseQueryOptions<any, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: statisticsQueryKeys.skuRanking(params),
    queryFn: () => statisticsApi.getUnifiedSkuRanking(params),
    staleTime: DEFAULT_STALE_TIME,
    gcTime: DEFAULT_GC_TIME,
    ...options,
  })
}

/**
 * 获取负责人业绩排行
 */
export const useStatisticsManagerRanking = (
  params?: ManagerRankingParams,
  options?: Omit<UseQueryOptions<any, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: statisticsQueryKeys.managerRanking(params),
    queryFn: () => statisticsApi.getUnifiedManagerRanking(params),
    staleTime: DEFAULT_STALE_TIME,
    gcTime: DEFAULT_GC_TIME,
    ...options,
  })
}

/**
 * 获取综合数据摘要
 */
export const useStatisticsSummary = (
  params?: SummaryParams,
  options?: Omit<UseQueryOptions<any, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: statisticsQueryKeys.summary(params),
    queryFn: () => statisticsApi.getUnifiedSummary(params),
    staleTime: DEFAULT_STALE_TIME,
    gcTime: DEFAULT_GC_TIME,
    ...options,
  })
}












