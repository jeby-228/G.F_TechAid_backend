import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import App from './App';
import authSlice from './store/slices/authSlice';
import taskSlice from './store/slices/taskSlice';
import needSlice from './store/slices/needSlice';
import supplySlice from './store/slices/supplySlice';
import notificationSlice from './store/slices/notificationSlice';

// Mock store for testing
const mockStore = configureStore({
  reducer: {
    auth: authSlice,
    tasks: taskSlice,
    needs: needSlice,
    supplies: supplySlice,
    notifications: notificationSlice,
  },
});

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  createBrowserRouter: () => ({
    routes: [],
  }),
  RouterProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

test('renders without crashing', () => {
  render(
    <Provider store={mockStore}>
      <App />
    </Provider>
  );
  
  // The app should render without throwing an error
  expect(document.querySelector('.App')).toBeInTheDocument();
});