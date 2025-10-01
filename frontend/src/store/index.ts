import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import taskSlice from './slices/taskSlice';
import needSlice from './slices/needSlice';
import supplySlice from './slices/supplySlice';
import notificationSlice from './slices/notificationSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    tasks: taskSlice,
    needs: needSlice,
    supplies: supplySlice,
    notifications: notificationSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;