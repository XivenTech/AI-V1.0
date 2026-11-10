import React from 'react';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { DashboardPage } from './pages/DashboardPage';

export const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#0284c7',
          colorInfo: '#38bdf8',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          colorBgBase: '#0b0f19',
          colorBgContainer: '#1e293b',
          colorBorder: 'rgba(56, 189, 248, 0.2)',
          borderRadius: 8,
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
      }}
    >
      <DashboardPage />
    </ConfigProvider>
  );
};

export default App;
