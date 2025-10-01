import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { UserRole } from '@/types';

// Pages
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import TasksPage from '@/pages/TasksPage';
import TaskDetailPage from '@/pages/TaskDetailPage';
import CreateTaskPage from '@/pages/CreateTaskPage';
import NeedsPage from '@/pages/NeedsPage';
import NeedDetailPage from '@/pages/NeedDetailPage';
import CreateNeedPage from '@/pages/CreateNeedPage';
import SuppliesPage from '@/pages/SuppliesPage';
import SupplyStationPage from '@/pages/SupplyStationPage';
import NotificationsPage from '@/pages/NotificationsPage';
import ProfilePage from '@/pages/ProfilePage';
import SheltersPage from '@/pages/SheltersPage';
import AnnouncementsPage from '@/pages/AnnouncementsPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'tasks',
        element: <TasksPage />,
      },
      {
        path: 'tasks/:id',
        element: <TaskDetailPage />,
      },
      {
        path: 'tasks/create',
        element: (
          <ProtectedRoute allowedRoles={[UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER]}>
            <CreateTaskPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'needs',
        element: <NeedsPage />,
      },
      {
        path: 'needs/:id',
        element: <NeedDetailPage />,
      },
      {
        path: 'needs/create',
        element: (
          <ProtectedRoute allowedRoles={[UserRole.VICTIM]}>
            <CreateNeedPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'supplies',
        element: <SuppliesPage />,
      },
      {
        path: 'supplies/stations/:id',
        element: <SupplyStationPage />,
      },
      {
        path: 'shelters',
        element: <SheltersPage />,
      },
      {
        path: 'announcements',
        element: <AnnouncementsPage />,
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
    ],
  },
]);