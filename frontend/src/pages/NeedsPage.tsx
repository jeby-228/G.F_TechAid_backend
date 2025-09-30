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
  Spin
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EnvironmentOutlined,
  ClockCircleOutlined,
  UserOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { Need, NeedType, NeedStatus, UserRole } from '@/types';
import { apiClient } from '@/services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const NeedsPage: React.FC = () => {
  const [needs, setNeeds] = useState<Need[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<NeedType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<NeedStatus | 'all'>('all');
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);

  const needTypeOptions = [
    { value: 'all', label: '全部類型' },
    { value: NeedType.FOOD, label: '食物需求', icon: '🍚' },
    { value: NeedType.MEDICAL, label: '醫療需求', icon: '🏥' },
    { value: NeedType.SHELTER, label: '住宿需求', icon: '🏠' },
    { value: NeedType.CLOTHING, label: '衣物需求', icon: '👕' },
    { value: NeedType.RESCUE, label: '救援需求', icon: '🚨' },
    { value: NeedType.CLEANUP, label: '清理需求', icon: '🧹' }
  ];

  const statusOptions = [
    { value: 'all', label: '全部狀態' },
    { value: NeedStatus.OPEN, label: '待處理', color: 'orange' },
    { value: NeedStatus.ASSIGNED, label: '已分配', color: 'blue' },
    { value: NeedStatus.IN_PROGRESS, label: '處理中', color: 'cyan' },
    { value: NeedStatus.RESOLVED, label: '已解決', color: 'green' },
    { value: NeedStatus.CLOSED, label: '已關閉', color: 'default' }
  ];

  useEffect(() => {
    fetchNeeds();
  }, []);

  const fetchNeeds = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<Need[]>('/needs');
      setNeeds(response.data);
    } catch (error) {
      message.error('載入需求列表失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimNeed = async (needId: string) => {
    try {
      await apiClient.post(`/needs/${needId}/claim`);
      message.success('需求認領成功');
      fetchNeeds(); // Refresh the list
    } catch (error) {
      message.error('認領失敗，請重試');
    }
  };

  const getUrgencyColor = (level: number) => {
    const colors = ['default', 'blue', 'orange', 'red', 'red'];
    return colors[level - 1] || 'default';
  };

  const getUrgencyText = (level: number) => {
    const texts = ['一般', '重要', '緊急', '非常緊急', '危急'];
    return texts[level - 1] || '一般';
  };

  const canClaimNeed = (need: Need) => {
    return user && 
           need.status === NeedStatus.OPEN && 
           need.reporterId !== user.id &&
           [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER].includes(user.role);
  };

  const canCreateNeed = () => {
    return user && [UserRole.VICTIM, UserRole.ADMIN].includes(user.role);
  };

  const filteredNeeds = needs.filter(need => {
    const matchesSearch = need.title.toLowerCase().includes(searchText.toLowerCase()) ||
                         need.description.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = filterType === 'all' || need.needType === filterType;
    const matchesStatus = filterStatus === 'all' || need.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>需求列表</Title>
            <Text type="secondary">查看和認領救災需求</Text>
          </Col>
          <Col>
            {canCreateNeed() && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => navigate('/needs/create')}
                size="large"
              >
                發布需求
              </Button>
            )}
          </Col>
        </Row>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={24} sm={8}>
            <Search
              placeholder="搜尋需求標題或描述"
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
              placeholder="選擇需求類型"
            >
              {needTypeOptions.map(option => (
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
        {filteredNeeds.length === 0 ? (
          <Empty
            description="暫無需求資料"
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
            dataSource={filteredNeeds}
            renderItem={(need) => (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    <Button
                      type="link"
                      onClick={() => navigate(`/needs/${need.id}`)}
                    >
                      查看詳情
                    </Button>,
                    ...(canClaimNeed(need) ? [
                      <Button
                        type="primary"
                        onClick={() => handleClaimNeed(need.id)}
                      >
                        認領需求
                      </Button>
                    ] : [])
                  ]}
                >
                  <Card.Meta
                    avatar={
                      <Avatar
                        style={{ backgroundColor: '#1890ff' }}
                        icon={<UserOutlined />}
                      />
                    }
                    title={
                      <Space direction="vertical" size={4}>
                        <div>{need.title}</div>
                        <Space size={8}>
                          <Tag color={getUrgencyColor(need.urgencyLevel)}>
                            <ExclamationCircleOutlined />
                            {getUrgencyText(need.urgencyLevel)}
                          </Tag>
                          <Tag color={statusOptions.find(s => s.value === need.status)?.color}>
                            {statusOptions.find(s => s.value === need.status)?.label}
                          </Tag>
                        </Space>
                      </Space>
                    }
                    description={
                      <div>
                        <Text ellipsis={{ tooltip: need.description }}>
                          {need.description}
                        </Text>
                        <Divider style={{ margin: '12px 0' }} />
                        <Space direction="vertical" size={4}>
                          <Space size={4}>
                            <EnvironmentOutlined style={{ color: '#666' }} />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {need.locationData.address}
                            </Text>
                          </Space>
                          <Space size={4}>
                            <ClockCircleOutlined style={{ color: '#666' }} />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {new Date(need.createdAt).toLocaleDateString('zh-TW')}
                            </Text>
                          </Space>
                        </Space>
                      </div>
                    }
                  />
                </Card>
              </List.Item>
            )}
          />
        )}
      </Spin>
    </div>
  );
};

export default NeedsPage;