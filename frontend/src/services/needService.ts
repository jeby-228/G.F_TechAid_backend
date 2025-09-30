import { apiClient } from './api';
import { Need, NeedStatus, PaginatedResponse, ApiResponse } from '@/types';

export const needService = {
  async getNeeds(params: { 
    page?: number; 
    size?: number; 
    status?: NeedStatus;
    needType?: string;
  }): Promise<ApiResponse<PaginatedResponse<Need>>> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.needType) queryParams.append('need_type', params.needType);
    
    return apiClient.get(`/needs?${queryParams.toString()}`);
  },

  async getNeedById(needId: string): Promise<ApiResponse<Need>> {
    return apiClient.get(`/needs/${needId}`);
  },

  async createNeed(needData: Partial<Need>): Promise<ApiResponse<Need>> {
    return apiClient.post('/needs', needData);
  },

  async updateNeed(needId: string, needData: Partial<Need>): Promise<ApiResponse<Need>> {
    return apiClient.put(`/needs/${needId}`, needData);
  },

  async deleteNeed(needId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/needs/${needId}`);
  },

  async assignNeed(needId: string, userId: string): Promise<ApiResponse<Need>> {
    return apiClient.post(`/needs/${needId}/assign`, { userId });
  },

  async updateNeedStatus(needId: string, status: NeedStatus): Promise<ApiResponse<Need>> {
    return apiClient.patch(`/needs/${needId}/status`, { status });
  },

  async getMyNeeds(): Promise<ApiResponse<Need[]>> {
    return apiClient.get('/needs/my-needs');
  },
};