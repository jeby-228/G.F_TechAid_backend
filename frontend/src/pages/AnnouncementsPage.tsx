import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

const AnnouncementsPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>系統公告</Title>
      <p>系統公告功能將在後續實作中完成</p>
    </div>
  );
};

export default AnnouncementsPage;