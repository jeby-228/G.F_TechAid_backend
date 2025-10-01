import React from 'react';
import { Form, Input, Button, Card, Typography, Select, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { RootState } from '@/store';
import { register } from '@/store/slices/authSlice';
import { RegisterData, UserRole } from '@/types';

const { Title, Text } = Typography;
const { Option } = Select;

const RegisterPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const onFinish = async (values: RegisterData) => {
    try {
      await dispatch(register(values)).unwrap();
      message.success('註冊成功，請登入');
      navigate('/login');
    } catch (error) {
      message.error('註冊失敗，請重試');
    }
  };

  const roleOptions = [
    { value: UserRole.VICTIM, label: '受災戶' },
    { value: UserRole.VOLUNTEER, label: '一般志工' },
    { value: UserRole.OFFICIAL_ORG, label: '正式志工組織負責人' },
    { value: UserRole.UNOFFICIAL_ORG, label: '非正式志工組織負責人' },
    { value: UserRole.SUPPLY_MANAGER, label: '物資站點管理者' },
  ];

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card style={{ width: '100%', maxWidth: 500, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
            註冊帳號
          </Title>
          <Text type="secondary">加入光復e互助平台</Text>
        </div>

        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '請輸入姓名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="請輸入您的姓名"
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
              placeholder="請輸入手機號碼（選填）"
            />
          </Form.Item>

          <Form.Item
            name="role"
            label="身分角色"
            rules={[{ required: true, message: '請選擇您的身分角色' }]}
          >
            <Select placeholder="請選擇您的身分角色">
              {roleOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="password"
            label="密碼"
            rules={[
              { required: true, message: '請輸入密碼' },
              { min: 6, message: '密碼至少需要6個字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="請輸入密碼"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="確認密碼"
            dependencies={['password']}
            rules={[
              { required: true, message: '請確認密碼' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('兩次輸入的密碼不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="請再次輸入密碼"
            />
          </Form.Item>

          {error && (
            <div style={{ color: '#ff4d4f', marginBottom: 16, textAlign: 'center' }}>
              {error}
            </div>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              style={{ width: '100%' }}
            >
              註冊
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">
              已有帳號？ <Link to="/login">立即登入</Link>
            </Text>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default RegisterPage;