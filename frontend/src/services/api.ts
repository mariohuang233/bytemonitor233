/**
 * API服务
 */
import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API请求失败:', error);
    return Promise.reject(error);
  }
);

export interface SpongeItem {
  _id: string;
  sheet_name: string;
  type_name: string;
  title: string;
  sub_title?: string;
  description?: string;
  requirement?: string;
  采摘时间?: string;
  publish_time?: string;
  code?: string;
  job_id?: string;
  job_category?: string;
  job_function?: string;
  city_list?: string;
  location?: any;
  department?: any;
  min_salary?: number;
  max_salary?: number;
  degree?: string;
  experience?: string;
  pc_job_url?: string;
  wap_job_url?: string;
  is_new?: boolean;
  is_viewed?: boolean;
  [key: string]: any;
}

export interface ListResponse {
  items: SpongeItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface StatsData {
  total: number;
  today_new: number;
  week_new: number;
  type_distribution: {
    [key: string]: number;
  };
  daily_trend: Array<{
    date: string;
    count: number;
  }>;
}

// 获取清单列表
export const getItems = async (params: {
  type?: string;
  page?: number;
  limit?: number;
  search?: string;
  is_new?: boolean;
}): Promise<{ success: boolean; data: ListResponse }> => {
  return api.get('/items', { params });
};

// 获取单个详情
export const getItemById = async (id: string): Promise<{ success: boolean; data: SpongeItem }> => {
  return api.get(`/items/${id}`);
};

// 获取统计数据
export const getStats = async (): Promise<{ success: boolean; data: StatsData }> => {
  return api.get('/stats');
};

// 触发同步
export const triggerSync = async (): Promise<{ success: boolean; message: string }> => {
  return api.post('/sync');
};

// 获取同步状态
export const getSyncStatus = async (): Promise<{
  success: boolean;
  data: {
    running: boolean;
    message: string;
    progress: number;
  };
}> => {
  return api.get('/sync/status');
};

// 获取同步日志
export const getSyncLogs = async (): Promise<{ success: boolean; data: any[] }> => {
  return api.get('/sync-logs');
};

export default api;

