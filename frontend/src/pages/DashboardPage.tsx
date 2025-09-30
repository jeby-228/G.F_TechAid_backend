import React, { useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Spin } from 'antd';
import {
  TeamOutlined,
  ExclamationCircleOutlined,
  ShoppingOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/store';
import { fetchTasks } from '@/store/slices/taskSlice';
import { fetchNeeds } from '@/store/slices/needSlice';
import { fetchSupplyStations } from '@/store/slices/supplySlice';
import { UserRole, TaskStatus, NeedStatus } from '@/types';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
  const { tasks, isLoading: tasksLoading } = useSelector((state: RootState) => state.tasks);
  const { needs, isLoading: needsLoading } = useSelector((state: RootState) => state.needs);
  const { stations, isLoading: suppliesLoading } = useSelector((state: RootState) => state.supplies);

  useEffect(() => {
    // 載入儀表板數據
    dispatch(fetchTasks({ page: 1, size: 100 }));
    dispatch(fetchNeeds({ page: 1, size: 100 }));
    dispatch(fetchSupplyStations());
  }, [dispatch]);

  const getWelcomeMessage = () => {
    const roleMessages = {
      [UserRole.ADMIN]: '系統管理員',
      [UserRole.VICTIM]: '受災戶',
      [UserRole.VOLUNTEER]: '志工',
      [UserRole.OFFICIAL_ORG]: '正式組織負責人',
      [UserRole.UNOFFICIAL_ORG]: '非正式組織負責人',
      [UserRole.SUPPLY_MANAGER]: '物資站點管理者',
    };
    
    return `歡迎回來，${roleMessages[user?.role as UserRole] || '用戶'}`;
  };

  const getStatistics = () => {
    const availableTasks = tasks.filter(task => task.status === TaskStatus.AVAILABLE).length;
    const openNeeds = needs.filter(need => need.status === NeedStatus.OPEN).length;
    const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED).length;
    const activeStations = stations.filter(station => station.isActive).length;

    return {
      availableTasks,
      openNeeds,
      completedTasks,
      activeStations,
    };
  };

  const stats = getStatistics();
  const isLoading = tasksLoading || needsLoading || suppliesLoading;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>{getWelcomeMessage()}</Title>
      
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="可用任務"
              value={stats.availableTasks}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待處理需求"
              value={stats.openNeeds}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成任務"
              value={stats.completedTasks}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活躍物資站點"
              value={stats.activeStations}
              prefix={<ShoppingOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 根據用戶角色顯示不同的快速操作 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {user?.role === UserRole.VICTIM && (
          <Col xs={24} lg={12}>
            <Card title="快速操作" size="small">
              <p>• 發布新的救援需求</p>
              <p>• 查看我的需求狀態</p>
              <p>• 尋找附近的避難所</p>
            </Card>
          </Col>
        )}
        
        {user?.role === UserRole.VOLUNTEER && (
          <Col xs={24} lg={12}>
            <Card title="快速操作" size="small">
              <p>• 認領可用的任務</p>
              <p>• 查看我的任務進度</p>
              <p>• 預訂物資進行配送</p>
            </Card>
          </Col>
        )}
        
        {[UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG].includes(user?.role as UserRole) && (
          <Col xs={24} lg={12}>
            <Card title="快速操作" size="small">
              <p>• 發布新的志工任務</p>
              <p>• 管理組織任務</p>
              <p>• 查看救災統計</p>
            </Card>
          </Col>
        )}
        
        {user?.role === UserRole.SUPPLY_MANAGER && (
          <Col xs={24} lg={12}>
            <Card title="快速操作" size="small">
              <p>• 更新物資庫存</p>
              <p>• 處理物資預訂</p>
              <p>• 管理站點資訊</p>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default DashboardPage;