import { apiClient } from './api';
import { Task, TaskStatus, PaginatedResponse, ApiResponse } from '@/types';

export const taskService = {
  async getTasks(params: { 
    page?: number; 
    size?: number; 
    status?: TaskStatus;
    taskType?: string;
  }): Promise<ApiResponse<PaginatedResponse<Task>>> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.taskType) queryParams.append('task_type', params.taskType);
    
    return apiClient.get(`/tasks?${queryParams.toString()}`);
  },

  async getTaskById(taskId: string): Promise<ApiResponse<Task>> {
    return apiClient.get(`/tasks/${taskId}`);
  },

  async createTask(taskData: Partial<Task>): Promise<ApiResponse<Task>> {
    return apiClient.post('/tasks', taskData);
  },

  async updateTask(taskId: string, taskData: Partial<Task>): Promise<ApiResponse<Task>> {
    return apiClient.put(`/tasks/${taskId}`, taskData);
  },

  async deleteTask(taskId: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/tasks/${taskId}`);
  },

  async claimTask(taskId: string): Promise<ApiResponse<Task>> {
    return apiClient.post(`/tasks/${taskId}/claim`);
  },

  async updateTaskStatus(taskId: string, status: TaskStatus): Promise<ApiResponse<Task>> {
    return apiClient.patch(`/tasks/${taskId}/status`, { status });
  },

  async getMyTasks(): Promise<ApiResponse<Task[]>> {
    return apiClient.get('/tasks/my-tasks');
  },

  async getTaskHistory(userId?: string): Promise<ApiResponse<Task[]>> {
    const url = userId ? `/tasks/history/${userId}` : '/tasks/history';
    return apiClient.get(url);
  },
};