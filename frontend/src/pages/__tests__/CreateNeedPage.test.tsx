import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import CreateNeedPage from '../CreateNeedPage';
import { UserRole, NeedType } from '@/types';
import * as api from '@/services/api';

// Mock the API client
jest.mock('@/services/api');
const mockedApi = api as jest.Mocked<typeof api>;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock LocationPicker component
jest.mock('@/components/LocationPicker', () => {
  return function MockLocationPicker({ onLocationSelect }: any) {
    return (
      <div data-testid="location-picker">
        <button
          onClick={() => onLocationSelect({
            address: '測試地址',
            coordinates: { lat: 23.9739, lng: 121.6015 },
            details: '測試位置'
          })}
        >
          選擇位置
        </button>
      </div>
    );
  };
});

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: jest.fn()
};
Object.defineProperty(global.navigator, 'geolocation', {
  value: mockGeolocation,
  writable: true
});

// Mock user data
const mockUser = {
  id: '1',
  name: '測試用戶',
  email: 'test@example.com',
  phone: '0912345678',
  role: UserRole.VICTIM,
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

describe('CreateNeedPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders create need form', () => {
    renderWithProviders(<CreateNeedPage />);
    
    expect(screen.getByText('發布需求')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('簡短描述您的需求')).toBeInTheDocument();
    expect(screen.getByText('選擇需求類型')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('請詳細說明您需要什麼協助，包括數量、規格等具體資訊')).toBeInTheDocument();
  });

  test('shows need type options', () => {
    renderWithProviders(<CreateNeedPage />);
    
    // Click on need type select
    fireEvent.click(screen.getByText('選擇需求類型'));
    
    expect(screen.getByText('食物需求')).toBeInTheDocument();
    expect(screen.getByText('醫療需求')).toBeInTheDocument();
    expect(screen.getByText('住宿需求')).toBeInTheDocument();
    expect(screen.getByText('衣物需求')).toBeInTheDocument();
    expect(screen.getByText('救援需求')).toBeInTheDocument();
    expect(screen.getByText('清理需求')).toBeInTheDocument();
  });

  test('shows urgency level options', () => {
    renderWithProviders(<CreateNeedPage />);
    
    // The urgency level select should have default value
    expect(screen.getByDisplayValue('1')).toBeInTheDocument();
  });

  test('handles location selection', () => {
    renderWithProviders(<CreateNeedPage />);
    
    // Click the mock location picker button
    fireEvent.click(screen.getByText('選擇位置'));
    
    expect(screen.getByText('已選擇位置：')).toBeInTheDocument();
    expect(screen.getByText('測試地址')).toBeInTheDocument();
  });

  test('handles current location request', () => {
    const mockGetCurrentPosition = jest.fn((success) => {
      success({
        coords: {
          latitude: 23.9739,
          longitude: 121.6015
        }
      });
    });
    mockGeolocation.getCurrentPosition = mockGetCurrentPosition;
    
    renderWithProviders(<CreateNeedPage />);
    
    fireEvent.click(screen.getByText('使用當前位置'));
    
    expect(mockGetCurrentPosition).toHaveBeenCalled();
  });

  test('handles form submission successfully', async () => {
    mockedApi.apiClient.post = jest.fn().mockResolvedValue({ data: {} });
    
    renderWithProviders(<CreateNeedPage />);
    
    // Fill form
    fireEvent.change(screen.getByPlaceholderText('簡短描述您的需求'), {
      target: { value: '需要食物' }
    });
    
    fireEvent.change(screen.getByPlaceholderText('請詳細說明您需要什麼協助，包括數量、規格等具體資訊'), {
      target: { value: '需要白米和水' }
    });
    
    // Select need type
    fireEvent.click(screen.getByText('選擇需求類型'));
    fireEvent.click(screen.getByText('食物需求'));
    
    // Select location
    fireEvent.click(screen.getByText('選擇位置'));
    
    // Submit form
    fireEvent.click(screen.getByText('發布需求'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalledWith('/needs', expect.objectContaining({
        title: '需要食物',
        description: '需要白米和水',
        needType: NeedType.FOOD,
        reporterId: '1'
      }));
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/needs');
  });

  test('shows error when location not selected', async () => {
    renderWithProviders(<CreateNeedPage />);
    
    // Fill form without selecting location
    fireEvent.change(screen.getByPlaceholderText('簡短描述您的需求'), {
      target: { value: '需要食物' }
    });
    
    fireEvent.change(screen.getByPlaceholderText('請詳細說明您需要什麼協助，包括數量、規格等具體資訊'), {
      target: { value: '需要白米和水' }
    });
    
    // Select need type
    fireEvent.click(screen.getByText('選擇需求類型'));
    fireEvent.click(screen.getByText('食物需求'));
    
    // Submit form without location
    fireEvent.click(screen.getByText('發布需求'));
    
    // Should not call API
    expect(mockedApi.apiClient.post).not.toHaveBeenCalled();
  });

  test('handles form submission error', async () => {
    mockedApi.apiClient.post = jest.fn().mockRejectedValue(new Error('Submit failed'));
    
    renderWithProviders(<CreateNeedPage />);
    
    // Fill form
    fireEvent.change(screen.getByPlaceholderText('簡短描述您的需求'), {
      target: { value: '需要食物' }
    });
    
    fireEvent.change(screen.getByPlaceholderText('請詳細說明您需要什麼協助，包括數量、規格等具體資訊'), {
      target: { value: '需要白米和水' }
    });
    
    // Select need type
    fireEvent.click(screen.getByText('選擇需求類型'));
    fireEvent.click(screen.getByText('食物需求'));
    
    // Select location
    fireEvent.click(screen.getByText('選擇位置'));
    
    // Submit form
    fireEvent.click(screen.getByText('發布需求'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalled();
    });
  });

  test('navigates back to needs list on cancel', () => {
    renderWithProviders(<CreateNeedPage />);
    
    fireEvent.click(screen.getByText('取消'));
    
    expect(mockNavigate).toHaveBeenCalledWith('/needs');
  });

  test('shows user contact info', () => {
    renderWithProviders(<CreateNeedPage />);
    
    expect(screen.getByText('預設使用您的註冊資訊：0912345678')).toBeInTheDocument();
  });
});