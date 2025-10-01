import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { SupplyStation, InventoryItem, SupplyReservation } from '@/types';
import { supplyService } from '@/services/supplyService';

interface SupplyState {
  stations: SupplyStation[];
  inventory: InventoryItem[];
  reservations: SupplyReservation[];
  isLoading: boolean;
  error: string | null;
}

const initialState: SupplyState = {
  stations: [],
  inventory: [],
  reservations: [],
  isLoading: false,
  error: null,
};

export const fetchSupplyStations = createAsyncThunk(
  'supplies/fetchStations',
  async (_, { rejectWithValue }) => {
    try {
      const response = await supplyService.getSupplyStations();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '獲取物資站點失敗');
    }
  }
);

export const fetchInventory = createAsyncThunk(
  'supplies/fetchInventory',
  async (stationId: string, { rejectWithValue }) => {
    try {
      const response = await supplyService.getInventory(stationId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '獲取庫存資訊失敗');
    }
  }
);

export const createReservation = createAsyncThunk(
  'supplies/createReservation',
  async (reservationData: Partial<SupplyReservation>, { rejectWithValue }) => {
    try {
      const response = await supplyService.createReservation(reservationData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '創建預訂失敗');
    }
  }
);

const supplySlice = createSlice({
  name: 'supplies',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSupplyStations.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchSupplyStations.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stations = action.payload;
      })
      .addCase(fetchSupplyStations.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchInventory.fulfilled, (state, action) => {
        state.inventory = action.payload;
      })
      .addCase(createReservation.fulfilled, (state, action) => {
        state.reservations.unshift(action.payload);
      });
  },
});

export const { clearError } = supplySlice.actions;
export default supplySlice.reducer;