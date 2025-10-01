import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

const NotificationsPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>通知中心</Title>
      <p>通知功能將在後續實作中完成</p>
    </div>
  );
};

export default NotificationsPage;