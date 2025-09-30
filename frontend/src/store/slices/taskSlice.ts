import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Task, TaskStatus, PaginatedResponse } from '@/types';
import { taskService } from '@/services/taskService';

interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}

const initialState: TaskState = {
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,
  pagination: {
    total: 0,
    page: 1,
    size: 10,
    pages: 0,
  },
};

// 異步 actions
export const fetchTasks = createAsyncThunk(
  'tasks/fetchTasks',
  async (params: { page?: number; size?: number; status?: TaskStatus }, { rejectWithValue }) => {
    try {
      const response = await taskService.getTasks(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '獲取任務列表失敗');
    }
  }
);

export const fetchTaskById = createAsyncThunk(
  'tasks/fetchTaskById',
  async (taskId: string, { rejectWithValue }) => {
    try {
      const response = await taskService.getTaskById(taskId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '獲取任務詳情失敗');
    }
  }
);

export const createTask = createAsyncThunk(
  'tasks/createTask',
  async (taskData: Partial<Task>, { rejectWithValue }) => {
    try {
      const response = await taskService.createTask(taskData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '創建任務失敗');
    }
  }
);

export const claimTask = createAsyncThunk(
  'tasks/claimTask',
  async (taskId: string, { rejectWithValue }) => {
    try {
      const response = await taskService.claimTask(taskId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '認領任務失敗');
    }
  }
);

export const updateTaskStatus = createAsyncThunk(
  'tasks/updateTaskStatus',
  async ({ taskId, status }: { taskId: string; status: TaskStatus }, { rejectWithValue }) => {
    try {
      const response = await taskService.updateTaskStatus(taskId, status);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '更新任務狀態失敗');
    }
  }
);

const taskSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentTask: (state, action: PayloadAction<Task | null>) => {
      state.currentTask = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch tasks
      .addCase(fetchTasks.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.isLoading = false;
        const response = action.payload as PaginatedResponse<Task>;
        state.tasks = response.items;
        state.pagination = {
          total: response.total,
          page: response.page,
          size: response.size,
          pages: response.pages,
        };
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch task by ID
      .addCase(fetchTaskById.fulfilled, (state, action) => {
        state.currentTask = action.payload;
      })
      // Create task
      .addCase(createTask.fulfilled, (state, action) => {
        state.tasks.unshift(action.payload);
      })
      // Claim task
      .addCase(claimTask.fulfilled, (state, action) => {
        const index = state.tasks.findIndex(task => task.id === action.payload.id);
        if (index !== -1) {
          state.tasks[index] = action.payload;
        }
        if (state.currentTask?.id === action.payload.id) {
          state.currentTask = action.payload;
        }
      })
      // Update task status
      .addCase(updateTaskStatus.fulfilled, (state, action) => {
        const index = state.tasks.findIndex(task => task.id === action.payload.id);
        if (index !== -1) {
          state.tasks[index] = action.payload;
        }
        if (state.currentTask?.id === action.payload.id) {
          state.currentTask = action.payload;
        }
      });
  },
});

export const { clearError, setCurrentTask } = taskSlice.actions;
export default taskSlice.reducer;