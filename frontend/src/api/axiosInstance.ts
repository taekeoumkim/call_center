// frontend/src/api/axiosInstance.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// 일반적인 API 응답 형식 (선택 사항, 다른 API들이 이 구조를 따른다면 유지)
export interface ApiResponse<T = any> {
  status?: string;
  data?: T;
  message?: string;
  error?: { /* ... */ };
}

// 로그인 성공 시 백엔드에서 직접 반환하는 데이터의 타입
export interface AuthData {
  message: string; // 'Login successful'
  access_token: string;
  refresh_token?: string; // 있을 수도 있고 없을 수도 있음 (백엔드 로직에 따라)
  user_id: number;
  name: string;
  username: string;
}

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('accessToken');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse>) => { // 일반적인 에러 응답은 ApiResponse 형태를 기대할 수 있음
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;