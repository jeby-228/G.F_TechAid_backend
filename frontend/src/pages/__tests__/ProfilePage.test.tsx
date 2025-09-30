import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import ProfilePage from '../ProfilePage';
import { UserRole } from '@/types';
import * as api from '@/services/api';

// Mock the API client
jest.mock('@/services/api');
const mockedApi = api as jest.Mocked<typeof api>;

// Mock user data
const mockUser = {
  id: '1',
  name: '測試用戶',
  email: 'test@example.com',
  phone: '0912345678',
  role: UserRole.VOLUNTEER,
  isApproved: true,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z'
};

// Create mock store
const createMockStore = (user = mockUser) => {
  return configureStore({
    reducer: {
      auth: (state = { user, isLoading: false, error: null }) => state
    }
  });
};

const renderWithProviders = (component: React.ReactElement, user = mockUser) => {
  const store = createMockStore(user);
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};

describe('ProfilePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders user profile information', () => {
    renderWithProviders(<ProfilePage />);
    
    expect(screen.getByText('測試用戶')).toBeInTheDocument();
    expect(screen.getByText('一般志工')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('0912345678')).toBeInTheDocument();
  });

  test('shows edit button and allows editing', () => {
    renderWithProviders(<ProfilePage />);
    
    const editButton = screen.getByText('編輯資料');
    expect(editButton).toBeInTheDocument();
    
    fireEvent.click(editButton);
    
    expect(screen.getByText('儲存')).toBeInTheDocument();
    expect(screen.getByText('取消')).toBeInTheDocument();
  });

  test('shows approval status for unofficial organization', () => {
    const unofficialOrgUser = {
      ...mockUser,
      role: UserRole.UNOFFICIAL_ORG,
      isApproved: false
    };
    
    renderWithProviders(<ProfilePage />, unofficialOrgUser);
    
    expect(screen.getByText('待審核')).toBeInTheDocument();
  });

  test('handles profile update successfully', async () => {
    mockedApi.apiClient.put = jest.fn().mockResolvedValue({ data: {} });
    
    renderWithProviders(<ProfilePage />);
    
    // Click edit button
    fireEvent.click(screen.getByText('編輯資料'));
    
    // Change name
    const nameInput = screen.getByDisplayValue('測試用戶');
    fireEvent.change(nameInput, { target: { value: '新名稱' } });
    
    // Save changes
    fireEvent.click(screen.getByText('儲存'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.put).toHaveBeenCalledWith('/users/1', expect.any(Object));
    });
  });

  test('handles profile update error', async () => {
    mockedApi.apiClient.put = jest.fn().mockRejectedValue(new Error('Update failed'));
    
    renderWithProviders(<ProfilePage />);
    
    // Click edit button
    fireEvent.click(screen.getByText('編輯資料'));
    
    // Save changes
    fireEvent.click(screen.getByText('儲存'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.put).toHaveBeenCalled();
    });
  });

  test('cancels editing and resets form', () => {
    renderWithProviders(<ProfilePage />);
    
    // Click edit button
    fireEvent.click(screen.getByText('編輯資料'));
    
    // Change name
    const nameInput = screen.getByDisplayValue('測試用戶');
    fireEvent.change(nameInput, { target: { value: '新名稱' } });
    
    // Cancel editing
    fireEvent.click(screen.getByText('取消'));
    
    // Should be back to view mode
    expect(screen.getByText('編輯資料')).toBeInTheDocument();
    expect(screen.getByDisplayValue('測試用戶')).toBeInTheDocument();
  });

  test('disables email field during editing', () => {
    renderWithProviders(<ProfilePage />);
    
    // Click edit button
    fireEvent.click(screen.getByText('編輯資料'));
    
    const emailInput = screen.getByDisplayValue('test@example.com');
    expect(emailInput).toBeDisabled();
  });

  test('disables role field during editing', () => {
    renderWithProviders(<ProfilePage />);
    
    // Click edit button
    fireEvent.click(screen.getByText('編輯資料'));
    
    // Role select should be disabled
    const roleSelect = screen.getByDisplayValue('volunteer');
    expect(roleSelect).toBeDisabled();
  });
});