import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import TasksPage from '../TasksPage';
import { UserRole, TaskType, TaskStatus } from '@/types';
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

// Mock tasks data
const mockTasks = [
  {
    id: '1',
    creatorId: '2',
    title: '清理工作',
    description: '清理災區垃圾',
    taskType: TaskType.CLEANUP,
    status: TaskStatus.AVAILABLE,
    locationData: {
      address: '花蓮縣光復鄉',
      coordinates: { lat: 23.9739, lng: 121.6015 }
    },
    requiredVolunteers: 5,
    priorityLevel: 2,
    deadline: '2023-12-31T23:59:59Z',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z'
  },
  {
    id: '2',
    creatorId: '3',
    title: '物資配送',
    description: '配送救援物資',
    taskType: TaskType.SUPPLY_DELIVERY,
    status: TaskStatus.CLAIMED,
    locationData: {
      address: '花蓮縣光復鄉中正路',
      coordinates: { lat: 23.9740, lng: 121.6016 }
    },
    requiredVolunteers: 3,
    priorityLevel: 4,
    deadline: '2023-01-01T00:00:00Z', // Expired
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

describe('TasksPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: mockTasks });
  });

  test('renders tasks page with title', async () => {
    renderWithProviders(<TasksPage />);
    
    expect(screen.getByText('任務列表')).toBeInTheDocument();
    expect(screen.getByText('查看和認領志工任務')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(mockedApi.apiClient.get).toHaveBeenCalledWith('/tasks');
    });
  });

  test('shows create task button for official organization', () => {
    const officialOrgUser = { ...mockUser, role: UserRole.OFFICIAL_ORG };
    renderWithProviders(<TasksPage />, officialOrgUser);
    
    expect(screen.getByText('發布任務')).toBeInTheDocument();
  });

  test('does not show create task button for volunteers', () => {
    renderWithProviders(<TasksPage />);
    
    expect(screen.queryByText('發布任務')).not.toBeInTheDocument();
  });

  test('displays tasks list after loading', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
      expect(screen.getByText('物資配送')).toBeInTheDocument();
    });
  });

  test('shows task details correctly', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
      expect(screen.getByText('清理災區垃圾')).toBeInTheDocument();
      expect(screen.getByText('需要 5 名志工')).toBeInTheDocument();
      expect(screen.getByText('花蓮縣光復鄉')).toBeInTheDocument();
      expect(screen.getByText('優先級: 重要')).toBeInTheDocument();
      expect(screen.getByText('可認領')).toBeInTheDocument();
    });
  });

  test('shows expired task with ribbon', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('已過期')).toBeInTheDocument();
    });
  });

  test('filters tasks by search text', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
      expect(screen.getByText('物資配送')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('搜尋任務標題或描述');
    fireEvent.change(searchInput, { target: { value: '清理' } });
    
    expect(screen.getByText('清理工作')).toBeInTheDocument();
    expect(screen.queryByText('物資配送')).not.toBeInTheDocument();
  });

  test('filters tasks by type', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
      expect(screen.getByText('物資配送')).toBeInTheDocument();
    });
    
    // Click on type filter
    const typeFilter = screen.getAllByText('全部類型')[0];
    fireEvent.click(typeFilter);
    
    // Select cleanup type
    fireEvent.click(screen.getByText('清理工作'));
    
    expect(screen.getByText('清理工作')).toBeInTheDocument();
    expect(screen.queryByText('物資配送')).not.toBeInTheDocument();
  });

  test('filters tasks by status', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
      expect(screen.getByText('物資配送')).toBeInTheDocument();
    });
    
    // Click on status filter
    const statusFilter = screen.getAllByText('全部狀態')[0];
    fireEvent.click(statusFilter);
    
    // Select available status
    fireEvent.click(screen.getByText('可認領'));
    
    expect(screen.getByText('清理工作')).toBeInTheDocument();
    expect(screen.queryByText('物資配送')).not.toBeInTheDocument();
  });

  test('shows claim button for claimable tasks', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
    });
    
    expect(screen.getByText('認領任務')).toBeInTheDocument();
  });

  test('does not show claim button for own tasks', async () => {
    const ownTask = {
      ...mockTasks[0],
      creatorId: '1' // Same as current user
    };
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: [ownTask] });
    
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('清理工作')).toBeInTheDocument();
    });
    
    expect(screen.queryByText('認領任務')).not.toBeInTheDocument();
  });

  test('disables claim button for expired tasks', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('物資配送')).toBeInTheDocument();
    });
    
    // The expired task should not have a claim button or it should be disabled
    const claimButtons = screen.queryAllByText('認領任務');
    expect(claimButtons.length).toBe(1); // Only one claimable task
  });

  test('handles task claiming successfully', async () => {
    mockedApi.apiClient.post = jest.fn().mockResolvedValue({ data: {} });
    
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('認領任務')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('認領任務'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalledWith('/tasks/1/claim');
    });
  });

  test('handles task claiming error', async () => {
    mockedApi.apiClient.post = jest.fn().mockRejectedValue(new Error('Claim failed'));
    
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('認領任務')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('認領任務'));
    
    await waitFor(() => {
      expect(mockedApi.apiClient.post).toHaveBeenCalled();
    });
  });

  test('navigates to task details on view details click', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getAllByText('查看詳情')[0]).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getAllByText('查看詳情')[0]);
    
    expect(mockNavigate).toHaveBeenCalledWith('/tasks/1');
  });

  test('navigates to create task page on create button click', () => {
    const officialOrgUser = { ...mockUser, role: UserRole.OFFICIAL_ORG };
    renderWithProviders(<TasksPage />, officialOrgUser);
    
    fireEvent.click(screen.getByText('發布任務'));
    
    expect(mockNavigate).toHaveBeenCalledWith('/tasks/create');
  });

  test('shows empty state when no tasks', async () => {
    mockedApi.apiClient.get = jest.fn().mockResolvedValue({ data: [] });
    
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText('暫無任務資料')).toBeInTheDocument();
    });
  });

  test('handles API error', async () => {
    mockedApi.apiClient.get = jest.fn().mockRejectedValue(new Error('API Error'));
    
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(mockedApi.apiClient.get).toHaveBeenCalled();
    });
  });

  test('shows deadline information', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/截止:/)).toBeInTheDocument();
    });
  });

  test('shows creation date', async () => {
    renderWithProviders(<TasksPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/發布:/)).toBeInTheDocument();
    });
  });
});