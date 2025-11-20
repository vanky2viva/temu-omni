/**
 * 订单成本计算API服务
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

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
  const token = localStorage.getItem('token');
  const response = await axios.post(
    `${API_BASE_URL}/order-costs/calculate`,
    request,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return response.data;
};

/**
 * 获取每日预估回款数据
 */
export const getDailyCollectionForecast = async (params?: {
  shop_id?: number;
  start_date?: string;
  end_date?: string;
}): Promise<DailyCollectionForecast[]> => {
  const token = localStorage.getItem('token');
  const response = await axios.get(
    `${API_BASE_URL}/order-costs/daily-forecast`,
    {
      params,
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  return response.data;
};

