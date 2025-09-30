import { apiClient } from './api';
import { Notification, ApiResponse } from '@/types';

export const notificationService = {
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    return apiClient.get('/notifications');
  },

  async markAsRead(notificationId: string): Promise<ApiResponse<Notification>> {
    return apiClient.patch(`/notifications/${notificationId}/read`);
  },

  async markAllAsRead(): Promise<ApiResponse<void>> {
    return apiClient.post('/notifications/mark-all-read');
  },

  async deleteNotification(notificationId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/notifications/${notificationId}`);
  },

  async getUnreadCount(): Promise<ApiResponse<{ count: number }>> {
    return apiClient.get('/notifications/unread-count');
  },
};