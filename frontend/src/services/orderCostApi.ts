/**
 * 订单成本计算API服务
 */
import { api } from './api';

export interface CalculateCostRequest {
  shop_id?: number;
  order_ids?: number[];
  force_recalculate?: boolean;
}

export interface CalculateCostResponse {
  total: number;
  success: number;
  failed: number;
  skipped: number;
  message: string;
}

export interface DailyCollectionForecast {
  date: string;
  order_count: number;
  total_amount: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
}

/**
 * 计算订单成本和利润
 */
export const calculateOrderCosts = async (
  request: CalculateCostRequest
): Promise<CalculateCostResponse> => {
  return api.post('/order-costs/calculate', request);
};

/**
 * 获取每日预估回款数据
 */
export const getDailyCollectionForecast = async (params?: {
  shop_id?: number;
  start_date?: string;
  end_date?: string;
}): Promise<DailyCollectionForecast[]> => {
  return api.get('/order-costs/daily-forecast', { params });
};

