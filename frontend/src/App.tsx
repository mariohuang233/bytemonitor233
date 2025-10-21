/**
 * 应用主组件
 */
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Landing from './pages/Landing';
import Home from './pages/Home';
import 'dayjs/locale/zh-cn';

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#667eea',
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/jobs" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;

