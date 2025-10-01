import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Typography,
  Select,
  Input,
  Space,
  Tag,
  Row,
  Col,
  Avatar,
  Divider,
  message,
  Empty,
  Spin,
  Badge
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EnvironmentOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { Task, TaskType, TaskStatus, UserRole } from '@/types';
import { apiClient } from '@/services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<TaskType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all');
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);

  const taskTypeOptions = [
    { value: 'all', label: '全部類型' },
    { value: TaskType.CLEANUP, label: '清理工作', icon: '🧹' },
    { value: TaskType.RESCUE, label: '救援任務', icon: '🚨' },
    { value: TaskType.SUPPLY_DELIVERY, label: '物資配送', icon: '📦' },
    { value: TaskType.MEDICAL_AID, label: '醫療協助', icon: '🏥' },
    { value: TaskType.SHELTER_SUPPORT, label: '避難所支援', icon: '🏠' }
  ];

  const statusOptions = [
    { value: 'all', label: '全部狀態' },
    { value: TaskStatus.PENDING, label: '待審核', color: 'orange' },
    { value: TaskStatus.AVAILABLE, label: '可認領', color: 'green' },
    { value: TaskStatus.CLAIMED, label: '已認領', color: 'blue' },
    { value: TaskStatus.IN_PROGRESS, label: '執行中', color: 'cyan' },
    { value: TaskStatus.COMPLETED, label: '已完成', color: 'default' },
    { value: TaskStatus.CANCELLED, label: '已取消', color: 'red' }
  ];

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<Task[]>('/tasks');
      setTasks(response.data);
    } catch (error) {
      message.error('載入任務列表失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimTask = async (taskId: string) => {
    try {
      await apiClient.post(`/tasks/${taskId}/claim`);
      message.success('任務認領成功');
      fetchTasks(); // Refresh the list
    } catch (error) {
      message.error('認領失敗，請重試');
    }
  };

  const getPriorityColor = (level: number) => {
    const colors = ['default', 'blue', 'orange', 'red', 'red'];
    return colors[level - 1] || 'default';
  };

  const getPriorityText = (level: number) => {
    const texts = ['一般', '重要', '緊急', '非常緊急', '危急'];
    return texts[level - 1] || '一般';
  };

  const canClaimTask = (task: Task) => {
    return user && 
           task.status === TaskStatus.AVAILABLE && 
           task.creatorId !== user.id &&
           [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER].includes(user.role);
  };

  const canCreateTask = () => {
    return user && [UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER, UserRole.ADMIN].includes(user.role);
  };

  const isTaskExpired = (task: Task) => {
    return task.deadline && new Date(task.deadline) < new Date();
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchText.toLowerCase()) ||
                         task.description.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = filterType === 'all' || task.taskType === filterType;
    const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>任務列表</Title>
            <Text type="secondary">查看和認領志工任務</Text>
          </Col>
          <Col>
            {canCreateTask() && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => navigate('/tasks/create')}
                size="large"
              >
                發布任務
              </Button>
            )}
          </Col>
        </Row>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={24} sm={8}>
            <Search
              placeholder="搜尋任務標題或描述"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={8}>
            <Select
              value={filterType}
              onChange={setFilterType}
              style={{ width: '100%' }}
              placeholder="選擇任務類型"
            >
              {taskTypeOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  <Space>
                    {option.icon && <span>{option.icon}</span>}
                    <span>{option.label}</span>
                  </Space>
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={8}>
            <Select
              value={filterStatus}
              onChange={setFilterStatus}
              style={{ width: '100%' }}
              placeholder="選擇狀態"
            >
              {statusOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.color ? (
                    <Tag color={option.color}>{option.label}</Tag>
                  ) : (
                    option.label
                  )}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {filteredTasks.length === 0 ? (
          <Empty
            description="暫無任務資料"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            grid={{
              gutter: 16,
              xs: 1,
              sm: 1,
              md: 2,
              lg: 2,
              xl: 3,
              xxl: 3,
            }}
            dataSource={filteredTasks}
            renderItem={(task) => (
              <List.Item>
                <Badge.Ribbon 
                  text={isTaskExpired(task) ? "已過期" : undefined}
                  color="red"
                  style={{ display: isTaskExpired(task) ? 'block' : 'none' }}
                >
                  <Card
                    hoverable
                    actions={[
                      <Button
                        type="link"
                        onClick={() => navigate(`/tasks/${task.id}`)}
                      >
                        查看詳情
                      </Button>,
                      ...(canClaimTask(task) ? [
                        <Button
                          type="primary"
                          onClick={() => handleClaimTask(task.id)}
                          disabled={isTaskExpired(task)}
                        >
                          認領任務
                        </Button>
                      ] : [])
                    ]}
                  >
                    <Card.Meta
                      avatar={
                        <Avatar
                          style={{ backgroundColor: '#52c41a' }}
                          icon={<TeamOutlined />}
                        />
                      }
                      title={
                        <Space direction="vertical" size={4}>
                          <div>{task.title}</div>
                          <Space size={8}>
                            <Tag color={getPriorityColor(task.priorityLevel)}>
                              優先級: {getPriorityText(task.priorityLevel)}
                            </Tag>
                            <Tag color={statusOptions.find(s => s.value === task.status)?.color}>
                              {statusOptions.find(s => s.value === task.status)?.label}
                            </Tag>
                          </Space>
                        </Space>
                      }
                      description={
                        <div>
                          <Text ellipsis={{ tooltip: task.description }}>
                            {task.description}
                          </Text>
                          <Divider style={{ margin: '12px 0' }} />
                          <Space direction="vertical" size={4}>
                            <Space size={4}>
                              <TeamOutlined style={{ color: '#666' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                需要 {task.requiredVolunteers} 名志工
                              </Text>
                            </Space>
                            <Space size={4}>
                              <EnvironmentOutlined style={{ color: '#666' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {task.locationData.address}
                              </Text>
                            </Space>
                            {task.deadline && (
                              <Space size={4}>
                                <CalendarOutlined style={{ color: isTaskExpired(task) ? '#ff4d4f' : '#666' }} />
                                <Text 
                                  type={isTaskExpired(task) ? 'danger' : 'secondary'} 
                                  style={{ fontSize: '12px' }}
                                >
                                  截止: {new Date(task.deadline).toLocaleDateString('zh-TW')}
                                </Text>
                              </Space>
                            )}
                            <Space size={4}>
                              <ClockCircleOutlined style={{ color: '#666' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                發布: {new Date(task.createdAt).toLocaleDateString('zh-TW')}
                              </Text>
                            </Space>
                          </Space>
                        </div>
                      }
                    />
                  </Card>
                </Badge.Ribbon>
              </List.Item>
            )}
          />
        )}
      </Spin>
    </div>
  );
};

export default TasksPage;