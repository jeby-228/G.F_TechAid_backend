import { apiClient } from './api';
import { User, LoginCredentials, RegisterData, ApiResponse } from '@/types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<ApiResponse<{ user: User; token: string }>> {
    return apiClient.post('/auth/login', credentials);
  },

  async register(userData: RegisterData): Promise<ApiResponse<User>> {
    return apiClient.post('/auth/register', userData);
  },

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return apiClient.get('/auth/me');
  },

  async updateProfile(profileData: Partial<User>): Promise<ApiResponse<User>> {
    return apiClient.put('/auth/profile', profileData);
  },

  async changePassword(data: { currentPassword: string; newPassword: string }): Promise<ApiResponse<void>> {
    return apiClient.post('/auth/change-password', data);
  },

  async logout(): Promise<ApiResponse<void>> {
    return apiClient.post('/auth/logout');
  },
};