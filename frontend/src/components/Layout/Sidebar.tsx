import React from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  ExclamationCircleOutlined,
  ShoppingOutlined,
  HomeOutlined,
  SoundOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { UserRole } from '@/types';

const { Sider } = Layout;

interface SidebarProps {
  collapsed: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useSelector((state: RootState) => state.auth);

  const getMenuItems = () => {
    const baseItems = [
      {
        key: '/dashboard',
        icon: <DashboardOutlined />,
        label: '儀表板',
      },
    ];

    // 根據用戶角色顯示不同的菜單項目
    if (user?.role === UserRole.VICTIM) {
      baseItems.push(
        {
          key: '/needs',
          icon: <ExclamationCircleOutlined />,
          label: '我的需求',
        },
        {
          key: '/tasks',
          icon: <TeamOutlined />,
          label: '可用任務',
        }
      );
    } else if (user?.role === UserRole.VOLUNTEER) {
      baseItems.push(
        {
          key: '/tasks',
          icon: <TeamOutlined />,
          label: '任務列表',
        },
        {
          key: '/needs',
          icon: <ExclamationCircleOutlined />,
          label: '需求列表',
        }
      );
    } else if ([UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG].includes(user?.role as UserRole)) {
      baseItems.push(
        {
          key: '/tasks',
          icon: <TeamOutlined />,
          label: '任務管理',
        },
        {
          key: '/needs',
          icon: <ExclamationCircleOutlined />,
          label: '需求列表',
        }
      );
    } else if (user?.role === UserRole.SUPPLY_MANAGER) {
      baseItems.push(
        {
          key: '/supplies',
          icon: <ShoppingOutlined />,
          label: '物資管理',
        },
        {
          key: '/tasks',
          icon: <TeamOutlined />,
          label: '任務列表',
        }
      );
    }

    // 所有用戶都可以看到的項目
    baseItems.push(
      {
        key: '/supplies',
        icon: <ShoppingOutlined />,
        label: '物資站點',
      },
      {
        key: '/shelters',
        icon: <HomeOutlined />,
        label: '避難所資訊',
      },
      {
        key: '/announcements',
        icon: <SoundOutlined />,
        label: '系統公告',
      }
    );

    // 管理員專用項目
    if (user?.role === UserRole.ADMIN) {
      baseItems.push({
        key: '/admin',
        icon: <UserOutlined />,
        label: '系統管理',
        children: [
          {
            key: '/admin/users',
            label: '用戶管理',
          },
          {
            key: '/admin/organizations',
            label: '組織審核',
          },
          {
            key: '/admin/reports',
            label: '系統報表',
          },
        ],
      });
    }

    return baseItems;
  };

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider 
      trigger={null} 
      collapsible 
      collapsed={collapsed}
      style={{
        background: '#fff',
        boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ 
        height: '64px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        borderBottom: '1px solid #f0f0f0'
      }}>
        {!collapsed && (
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
            光復e互助
          </span>
        )}
      </div>
      
      <Menu
        theme="light"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={getMenuItems()}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      />
    </Sider>
  );
};