import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Need, NeedStatus, PaginatedResponse } from '@/types';
import { needService } from '@/services/needService';

interface NeedState {
  needs: Need[];
  currentNeed: Need | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}

const initialState: NeedState = {
  needs: [],
  currentNeed: null,
  isLoading: false,
  error: null,
  pagination: {
    total: 0,
    page: 1,
    size: 10,
    pages: 0,
  },
};

export const fetchNeeds = createAsyncThunk(
  'needs/fetchNeeds',
  async (params: { page?: number; size?: number; status?: NeedStatus }, { rejectWithValue }) => {
    try {
      const response = await needService.getNeeds(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '獲取需求列表失敗');
    }
  }
);

export const createNeed = createAsyncThunk(
  'needs/createNeed',
  async (needData: Partial<Need>, { rejectWithValue }) => {
    try {
      const response = await needService.createNeed(needData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '創建需求失敗');
    }
  }
);

const needSlice = createSlice({
  name: 'needs',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNeeds.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchNeeds.fulfilled, (state, action) => {
        state.isLoading = false;
        const response = action.payload as PaginatedResponse<Need>;
        state.needs = response.items;
        state.pagination = {
          total: response.total,
          page: response.page,
          size: response.size,
          pages: response.pages,
        };
      })
      .addCase(fetchNeeds.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(createNeed.fulfilled, (state, action) => {
        state.needs.unshift(action.payload);
      });
  },
});

export const { clearError } = needSlice.actions;
export default needSlice.reducer;