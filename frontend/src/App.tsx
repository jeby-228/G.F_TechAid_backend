import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ConfigProvider } from 'antd';
import zhTW from 'antd/locale/zh_TW';
import { store } from '@/store';
import { router } from '@/router';
import { getCurrentUser } from '@/store/slices/authSlice';
import './App.css';

function App() {
  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('token');
    if (token) {
      store.dispatch(getCurrentUser());
    }
  }, []);

  return (
    <Provider store={store}>
      <ConfigProvider locale={zhTW}>
        <div className="App">
          <RouterProvider router={router} />
        </div>
      </ConfigProvider>
    </Provider>
  );
}

export default App;