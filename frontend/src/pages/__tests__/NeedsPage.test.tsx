import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import NeedsPage from '../NeedsPage';
import { UserRole, NeedType, NeedStatus } from '@/types';
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

// Mock needs data
const mockNeeds = [
  {
    id: '1',
    reporterId: '2',
    title: '需要食物',
    description: '需要白米和水',
    needType: NeedType.FOOD,
    status: NeedStatus.OPEN,
    locationData: {
      address: '花蓮縣光復鄉',
      coordinates: { lat: 23.9739, lng: 121.6015 }
    },
    requirements: '白米 5公斤',
    urgencyLevel: 3,
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z'
  },
  {
    id: '2',
    reporterId: '3',
    title: '醫療協助',
    description: '需要急救包',
    needType: NeedType.MEDICAL,
    status: NeedStatus.ASSIGNED,
    locationData: {
      address: '花蓮縣光復鄉中正路',
      coordinates: { lat: 23.9740, lng: 121.6016 }
    },
    requirements: '急救包 1個',
    urgencyLevel: 5,
    createdAt: '2023-01-02T00:00:00Z',
    updatedAt: '2023-01-02T00:00:00Z'
  }
];

// Mock user data
const mockUser = {
  id: '1',
  name: '測試志工',
  email: 'volunteer@example.com',
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

describe('NeedsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: mockNeeds });
  });

  test('renders needs page with title', async () => {
    renderWithProviders(<NeedsPage />);
    
    expect(screen.getByText('需求列表')).toBeInTheDocument();
    expect(screen.getByText('查看和認領救災需求')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(mockedApi.apiClient.get).toHaveBeenCalledWith('/needs');
    });
  });

  test('shows create need button for victims', () => {
    const victimUser = { ...mockUser, role: UserRole.VICTIM };
    renderWithProviders(<NeedsPage />, victimUser);
    
    expect(screen.getByText('發布需求')).toBeInTheDocument();
  });

  test('does not show create need button for volunteers', () => {
    renderWithProviders(<NeedsPage />);
    
    expect(screen.queryByText('發布需求')).not.toBeInTheDocument();
  });

  test('displays needs list after loading', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
      expect(screen.getByText('醫療協助')).toBeInTheDocument();
    });
  });

  test('shows need details correctly', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
      expect(screen.getByText('需要白米和水')).toBeInTheDocument();
      expect(screen.getByText('花蓮縣光復鄉')).toBeInTheDocument();
      expect(screen.getByText('緊急')).toBeInTheDocument();
      expect(screen.getByText('待處理')).toBeInTheDocument();
    });
  });

  test('filters needs by search text', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
      expect(screen.getByText('醫療協助')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('搜尋需求標題或描述');
    fireEvent.change(searchInput, { target: { value: '食物' } });
    
    expect(screen.getByText('需要食物')).toBeInTheDocument();
    expect(screen.queryByText('醫療協助')).not.toBeInTheDocument();
  });

  test('filters needs by type', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
      expect(screen.getByText('醫療協助')).toBeInTheDocument();
    });
    
    // Click on type filter
    const typeFilter = screen.getAllByText('全部類型')[0];
    fireEvent.click(typeFilter);
    
    // Select medical type
    fireEvent.click(screen.getByText('醫療需求'));
    
    expect(screen.queryByText('需要食物')).not.toBeInTheDocument();
    expect(screen.getByText('醫療協助')).toBeInTheDocument();
  });

  test('filters needs by status', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
      expect(screen.getByText('醫療協助')).toBeInTheDocument();
    });
    
    // Click on status filter
    const statusFilter = screen.getAllByText('全部狀態')[0];
    fireEvent.click(statusFilter);
    
    // Select open status
    fireEvent.click(screen.getByText('待處理'));
    
    expect(screen.getByText('需要食物')).toBeInTheDocument();
    expect(screen.queryByText('醫療協助')).not.toBeInTheDocument();
  });

  test('shows claim button for claimable needs', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
    });
    
    expect(screen.getByText('認領需求')).toBeInTheDocument();
  });

  test('does not show claim button for own needs', async () => {
    const ownNeed = {
      ...mockNeeds[0],
      reporterId: '1' // Same as current user
    };
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: [ownNeed] });
    
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('需要食物')).toBeInTheDocument();
    });
    
    expect(screen.queryByText('認領需求')).not.toBeInTheDocument();
  });

  test('handles need claiming successfully', async () => {
    mockedApi.apiClient.post = jest.fn().mockResolvedValue({ data: {} });
    
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('認領需求')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('認領需求'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalledWith('/needs/1/claim');
    });
  });

  test('handles need claiming error', async () => {
    mockedApi.apiClient.post = jest.fn().mockRejectedValue(new Error('Claim failed'));
    
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('認領需求')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('認領需求'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalled();
    });
  });

  test('navigates to need details on view details click', async () => {
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getAllByText('查看詳情')[0]).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getAllByText('查看詳情')[0]);
    
    expect(mockNavigate).toHaveBeenCalledWith('/needs/1');
  });

  test('navigates to create need page on create button click', () => {
    const victimUser = { ...mockUser, role: UserRole.VICTIM };
    renderWithProviders(<NeedsPage />, victimUser);
    
    fireEvent.click(screen.getByText('發布需求'));
    
    expect(mockNavigate).toHaveBeenCalledWith('/needs/create');
  });

  test('shows empty state when no needs', async () => {
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: [] });
    
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('暫無需求資料')).toBeInTheDocument();
    });
  });

  test('handles API error', async () => {
    mockedApi.apiClient.get = jest.fn().mockRejectedValue(new Error('API Error'));
    
    renderWithProviders(<NeedsPage />);
    
    await waitFor(() => {
      expect(mockedApi.apiClient.get).toHaveBeenCalled();
    });
  });
});