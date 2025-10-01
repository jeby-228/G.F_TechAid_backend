import { apiClient } from './api';
import { SupplyStation, InventoryItem, SupplyReservation, ApiResponse } from '@/types';

export const supplyService = {
  async getSupplyStations(): Promise<ApiResponse<SupplyStation[]>> {
    return apiClient.get('/supplies/stations');
  },

  async getSupplyStationById(stationId: string): Promise<ApiResponse<SupplyStation>> {
    return apiClient.get(`/supplies/stations/${stationId}`);
  },

  async createSupplyStation(stationData: Partial<SupplyStation>): Promise<ApiResponse<SupplyStation>> {
    return apiClient.post('/supplies/stations', stationData);
  },

  async updateSupplyStation(stationId: string, stationData: Partial<SupplyStation>): Promise<ApiResponse<SupplyStation>> {
    return apiClient.put(`/supplies/stations/${stationId}`, stationData);
  },

  async getInventory(stationId: string): Promise<ApiResponse<InventoryItem[]>> {
    return apiClient.get(`/supplies/stations/${stationId}/inventory`);
  },

  async updateInventory(stationId: string, items: InventoryItem[]): Promise<ApiResponse<InventoryItem[]>> {
    return apiClient.put(`/supplies/stations/${stationId}/inventory`, { items });
  },

  async createReservation(reservationData: Partial<SupplyReservation>): Promise<ApiResponse<SupplyReservation>> {
    return apiClient.post('/supplies/reservations', reservationData);
  },

  async getReservations(): Promise<ApiResponse<SupplyReservation[]>> {
    return apiClient.get('/supplies/reservations');
  },

  async updateReservationStatus(reservationId: string, status: string): Promise<ApiResponse<SupplyReservation>> {
    return apiClient.patch(`/supplies/reservations/${reservationId}/status`, { status });
  },

  async confirmPickup(reservationId: string): Promise<ApiResponse<SupplyReservation>> {
    return apiClient.post(`/supplies/reservations/${reservationId}/pickup`);
  },

  async confirmDelivery(reservationId: string): Promise<ApiResponse<SupplyReservation>> {
    return apiClient.post(`/supplies/reservations/${reservationId}/delivery`);
  },
};