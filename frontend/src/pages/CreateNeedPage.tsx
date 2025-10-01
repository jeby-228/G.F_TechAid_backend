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
  Tag
} from 'antd';
import {
  EnvironmentOutlined,
  ExclamationCircleOutlined,
  SaveOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { NeedType, LocationData, Coordinates } from '@/types';
import { apiClient } from '@/services/api';
import LocationPicker from '@/components/LocationPicker';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface NeedFormData {
  title: string;
  description: string;
  needType: NeedType;
  urgencyLevel: number;
  locationData: LocationData;
  requirements: any;
  contactInfo?: any;
}

const CreateNeedPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);

  const needTypeOptions = [
    { value: NeedType.FOOD, label: '食物需求', icon: '🍚' },
    { value: NeedType.MEDICAL, label: '醫療需求', icon: '🏥' },
    { value: NeedType.SHELTER, label: '住宿需求', icon: '🏠' },
    { value: NeedType.CLOTHING, label: '衣物需求', icon: '👕' },
    { value: NeedType.RESCUE, label: '救援需求', icon: '🚨' },
    { value: NeedType.CLEANUP, label: '清理需求', icon: '🧹' }
  ];

  const urgencyLevels = [
    { value: 1, label: '一般', color: 'default' },
    { value: 2, label: '重要', color: 'blue' },
    { value: 3, label: '緊急', color: 'orange' },
    { value: 4, label: '非常緊急', color: 'red' },
    { value: 5, label: '危急', color: 'red' }
  ];

  const handleSubmit = async (values: NeedFormData) => {
    if (!selectedLocation) {
      message.error('請選擇位置');
      return;
    }

    setLoading(true);
    try {
      const needData = {
        ...values,
        locationData: selectedLocation,
        reporterId: user?.id
      };

      await apiClient.post('/needs', needData);
      message.success('需求發布成功');
      navigate('/needs');
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
          const coords: Coordinates = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          
          // Reverse geocoding would be done here in a real implementation
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

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/needs')}
          style={{ marginBottom: 16 }}
        >
          返回需求列表
        </Button>
        <Title level={2}>發布需求</Title>
        <Text type="secondary">請詳細描述您的需求，以便志工能夠提供適當的協助</Text>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            urgencyLevel: 1
          }}
        >
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="title"
                label="需求標題"
                rules={[{ required: true, message: '請輸入需求標題' }]}
              >
                <Input placeholder="簡短描述您的需求" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="needType"
                label="需求類型"
                rules={[{ required: true, message: '請選擇需求類型' }]}
              >
                <Select placeholder="選擇需求類型">
                  {needTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      <Space>
                        <span>{option.icon}</span>
                        <span>{option.label}</span>
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
            rules={[{ required: true, message: '請詳細描述您的需求' }]}
          >
            <TextArea
              rows={4}
              placeholder="請詳細說明您需要什麼協助，包括數量、規格等具體資訊"
            />
          </Form.Item>

          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="urgencyLevel"
                label="緊急程度"
                rules={[{ required: true, message: '請選擇緊急程度' }]}
              >
                <Select>
                  {urgencyLevels.map(level => (
                    <Option key={level.value} value={level.value}>
                      <Tag color={level.color}>{level.label}</Tag>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="聯絡資訊">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text type="secondary">
                    預設使用您的註冊資訊：{user?.phone || user?.email}
                  </Text>
                </Space>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="位置資訊"
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

          <Form.Item
            name="requirements"
            label="具體需求清單"
          >
            <TextArea
              rows={3}
              placeholder="例如：白米 5公斤、礦泉水 10瓶、毛毯 2條等"
            />
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
                發布需求
              </Button>
              <Button
                onClick={() => navigate('/needs')}
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

export default CreateNeedPage;