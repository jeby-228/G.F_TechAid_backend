import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Select,
  message,
  Avatar,
  Row,
  Col,
  Divider,
  Space,
  Tag
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/store';
import { User, UserRole } from '@/types';
import { apiClient } from '@/services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const ProfilePage: React.FC = () => {
  const [form] = Form.useForm();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const { user } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        name: user.name,
        email: user.email,
        phone: user.phone,
        role: user.role
      });
    }
  }, [user, form]);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      await apiClient.put(`/users/${user?.id}`, values);
      message.success('個人資料更新成功');
      setIsEditing(false);
    } catch (error) {
      message.error('更新失敗，請重試');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setIsEditing(false);
  };

  const getRoleDisplay = (role: UserRole) => {
    const roleMap = {
      [UserRole.ADMIN]: '系統管理員',
      [UserRole.VICTIM]: '受災戶',
      [UserRole.OFFICIAL_ORG]: '正式志工組織負責人',
      [UserRole.UNOFFICIAL_ORG]: '非正式志工組織負責人',
      [UserRole.SUPPLY_MANAGER]: '物資站點管理者',
      [UserRole.VOLUNTEER]: '一般志工'
    };
    return roleMap[role] || role;
  };

  const getRoleColor = (role: UserRole) => {
    const colorMap = {
      [UserRole.ADMIN]: 'red',
      [UserRole.VICTIM]: 'orange',
      [UserRole.OFFICIAL_ORG]: 'blue',
      [UserRole.UNOFFICIAL_ORG]: 'cyan',
      [UserRole.SUPPLY_MANAGER]: 'green',
      [UserRole.VOLUNTEER]: 'purple'
    };
    return colorMap[role] || 'default';
  };

  if (!user) {
    return <div>載入中...</div>;
  }

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card>
        <Row gutter={24}>
          <Col xs={24} sm={8} style={{ textAlign: 'center' }}>
            <Avatar size={120} icon={<UserOutlined />} style={{ marginBottom: 16 }} />
            <div>
              <Title level={4}>{user.name}</Title>
              <Tag color={getRoleColor(user.role)}>
                {getRoleDisplay(user.role)}
              </Tag>
              {!user.isApproved && user.role === UserRole.UNOFFICIAL_ORG && (
                <div style={{ marginTop: 8 }}>
                  <Tag color="orange">待審核</Tag>
                </div>
              )}
            </div>
          </Col>

          <Col xs={24} sm={16}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <Title level={3}>個人資料</Title>
              {!isEditing ? (
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={() => setIsEditing(true)}
                >
                  編輯資料
                </Button>
              ) : (
                <Space>
                  <Button
                    icon={<CloseOutlined />}
                    onClick={handleCancel}
                  >
                    取消
                  </Button>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    loading={loading}
                    onClick={() => form.submit()}
                  >
                    儲存
                  </Button>
                </Space>
              )}
            </div>

            <Form
              form={form}
              layout="vertical"
              onFinish={handleSave}
              disabled={!isEditing}
            >
              <Form.Item
                name="name"
                label="姓名"
                rules={[{ required: true, message: '請輸入姓名' }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="請輸入姓名"
                />
              </Form.Item>

              <Form.Item
                name="email"
                label="電子郵件"
                rules={[
                  { required: true, message: '請輸入電子郵件' },
                  { type: 'email', message: '請輸入有效的電子郵件格式' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="請輸入電子郵件"
                  disabled // Email should not be editable
                />
              </Form.Item>

              <Form.Item
                name="phone"
                label="手機號碼"
                rules={[
                  { pattern: /^09\d{8}$/, message: '請輸入有效的手機號碼格式' }
                ]}
              >
                <Input
                  prefix={<PhoneOutlined />}
                  placeholder="請輸入手機號碼"
                />
              </Form.Item>

              <Form.Item
                name="role"
                label="身分角色"
              >
                <Select disabled placeholder="身分角色">
                  <Option value={UserRole.VICTIM}>受災戶</Option>
                  <Option value={UserRole.VOLUNTEER}>一般志工</Option>
                  <Option value={UserRole.OFFICIAL_ORG}>正式志工組織負責人</Option>
                  <Option value={UserRole.UNOFFICIAL_ORG}>非正式志工組織負責人</Option>
                  <Option value={UserRole.SUPPLY_MANAGER}>物資站點管理者</Option>
                </Select>
              </Form.Item>
            </Form>

            <Divider />

            <div>
              <Title level={4}>帳號資訊</Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Text type="secondary">註冊時間</Text>
                  <div>{new Date(user.createdAt).toLocaleDateString('zh-TW')}</div>
                </Col>
                <Col span={12}>
                  <Text type="secondary">最後更新</Text>
                  <div>{new Date(user.updatedAt).toLocaleDateString('zh-TW')}</div>
                </Col>
              </Row>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default ProfilePage;