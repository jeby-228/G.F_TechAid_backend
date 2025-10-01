import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Select,
  message,
  Row,
  Col,
  InputNumber,
  Space,
  Tag,
  DatePicker,
  Alert
} from 'antd';
import {
  EnvironmentOutlined,
  TeamOutlined,
  SaveOutlined,
  ArrowLeftOutlined,
  CalendarOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { TaskType, LocationData, UserRole } from '@/types';
import { apiClient } from '@/services/api';
import LocationPicker from '@/components/LocationPicker';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface TaskFormData {
  title: string;
  description: string;
  taskType: TaskType;
  requiredVolunteers: number;
  priorityLevel: number;
  deadline?: string;
  requiredSkills?: string[];
  locationData: LocationData;
}

const CreateTaskPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);

  const taskTypeOptions = [
    { value: TaskType.CLEANUP, label: '清理工作', icon: '🧹', description: '災後清理、垃圾清運等工作' },
    { value: TaskType.RESCUE, label: '救援任務', icon: '🚨', description: '人員搜救、緊急救援' },
    { value: TaskType.SUPPLY_DELIVERY, label: '物資配送', icon: '📦', description: '物資運送、分發工作' },
    { value: TaskType.MEDICAL_AID, label: '醫療協助', icon: '🏥', description: '醫療救護、健康檢查' },
    { value: TaskType.SHELTER_SUPPORT, label: '避難所支援', icon: '🏠', description: '避難所管理、服務工作' }
  ];

  const priorityLevels = [
    { value: 1, label: '一般', color: 'default' },
    { value: 2, label: '重要', color: 'blue' },
    { value: 3, label: '緊急', color: 'orange' },
    { value: 4, label: '非常緊急', color: 'red' },
    { value: 5, label: '危急', color: 'red' }
  ];

  const skillOptions = [
    '醫療急救', '重型機械操作', '電工技能', '水電維修', 
    '翻譯能力', '心理輔導', '烹飪技能', '駕駛執照',
    '搜救經驗', '建築技能', '資訊技術', '物流管理'
  ];

  const handleSubmit = async (values: TaskFormData) => {
    if (!selectedLocation) {
      message.error('請選擇任務位置');
      return;
    }

    setLoading(true);
    try {
      const taskData = {
        ...values,
        locationData: selectedLocation,
        creatorId: user?.id,
        deadline: values.deadline ? dayjs(values.deadline).toISOString() : undefined
      };

      await apiClient.post('/tasks', taskData);
      
      if (user?.role === UserRole.UNOFFICIAL_ORG) {
        message.success('任務已提交，等待管理員審核');
      } else {
        message.success('任務發布成功');
      }
      
      navigate('/tasks');
    } catch (error) {
      message.error('發布失敗，請重試');
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (location: LocationData) => {
    setSelectedLocation(location);
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          
          const locationData: LocationData = {
            address: '當前位置',
            coordinates: coords,
            details: 'GPS定位'
          };
          
          setSelectedLocation(locationData);
          message.success('已獲取當前位置');
        },
        (error) => {
          message.error('無法獲取位置，請手動選擇');
        }
      );
    } else {
      message.error('瀏覽器不支援定位功能');
    }
  };

  const isUnofficialOrg = user?.role === UserRole.UNOFFICIAL_ORG;

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/tasks')}
          style={{ marginBottom: 16 }}
        >
          返回任務列表
        </Button>
        <Title level={2}>發布任務</Title>
        <Text type="secondary">創建志工任務，招募志工協助救災工作</Text>
      </div>

      {isUnofficialOrg && (
        <Alert
          message="審核提醒"
          description="作為非正式組織，您發布的任務需要經過管理員審核後才會公開顯示。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            requiredVolunteers: 1,
            priorityLevel: 1
          }}
        >
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="title"
                label="任務標題"
                rules={[{ required: true, message: '請輸入任務標題' }]}
              >
                <Input placeholder="簡短描述任務內容" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="taskType"
                label="任務類型"
                rules={[{ required: true, message: '請選擇任務類型' }]}
              >
                <Select placeholder="選擇任務類型">
                  {taskTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      <Space>
                        <span>{option.icon}</span>
                        <div>
                          <div>{option.label}</div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {option.description}
                          </Text>
                        </div>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="詳細描述"
            rules={[{ required: true, message: '請詳細描述任務內容' }]}
          >
            <TextArea
              rows={4}
              placeholder="請詳細說明任務內容、工作要求、注意事項等"
            />
          </Form.Item>

          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Form.Item
                name="requiredVolunteers"
                label="需要志工人數"
                rules={[{ required: true, message: '請輸入需要的志工人數' }]}
              >
                <InputNumber
                  min={1}
                  max={100}
                  style={{ width: '100%' }}
                  placeholder="人數"
                  addonBefore={<TeamOutlined />}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="priorityLevel"
                label="優先級"
                rules={[{ required: true, message: '請選擇優先級' }]}
              >
                <Select>
                  {priorityLevels.map(level => (
                    <Option key={level.value} value={level.value}>
                      <Tag color={level.color}>
                        <ExclamationCircleOutlined />
                        {level.label}
                      </Tag>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="deadline"
                label="截止時間"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="選擇截止時間"
                  showTime
                  disabledDate={(current) => current && current < dayjs().startOf('day')}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="requiredSkills"
            label="所需技能（選填）"
          >
            <Select
              mode="multiple"
              placeholder="選擇所需的專業技能或資格"
              style={{ width: '100%' }}
            >
              {skillOptions.map(skill => (
                <Option key={skill} value={skill}>
                  {skill}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="任務位置"
            required
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Button
                  icon={<EnvironmentOutlined />}
                  onClick={getCurrentLocation}
                >
                  使用當前位置
                </Button>
                <Text type="secondary">或在地圖上點選位置</Text>
              </Space>
              
              {selectedLocation && (
                <div style={{ padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
                  <Text strong>已選擇位置：</Text>
                  <div>{selectedLocation.address}</div>
                  {selectedLocation.details && (
                    <Text type="secondary">{selectedLocation.details}</Text>
                  )}
                </div>
              )}
              
              <LocationPicker
                onLocationSelect={handleLocationSelect}
                initialLocation={selectedLocation}
              />
            </Space>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
                size="large"
              >
                {isUnofficialOrg ? '提交審核' : '發布任務'}
              </Button>
              <Button
                onClick={() => navigate('/tasks')}
                size="large"
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default CreateTaskPage;