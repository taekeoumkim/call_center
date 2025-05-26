// frontend/src/services/authService.ts
import axiosInstance, { AuthData } from '../api/axiosInstance';
import { SignupData, LoginData } from '../types/authTypes';
import { ApiResponse, SignupSuccessData } from '../types/apiTypes';

export interface User {
  userId: number;
  name: string;
  username: string;
}

// 회원가입 함수는 백엔드 응답 구조에 따라 ApiResponse<SignupSuccessData> 등을 유지하거나 수정
export const signup = async (userData: SignupData): Promise<ApiResponse<SignupSuccessData>> => {
  try {
    const response = await axiosInstance.post<ApiResponse<SignupSuccessData>>('/auth/signup', userData);
    return response.data;
  } catch (error: any) {
    throw error.response?.data || { message: error.message };
  }
};

export const login = async (credentials: LoginData): Promise<User> => { // 반환 타입을 User로 명확히 함
  try {
    // 백엔드가 AuthData 형태로 직접 응답하므로, post의 제네릭 타입도 AuthData로 지정
    const response = await axiosInstance.post<AuthData>('/auth/login', credentials);
    const authDetails = response.data; // 이제 authDetails는 AuthData 타입

    if (authDetails.access_token && authDetails.user_id) {
      localStorage.setItem('accessToken', authDetails.access_token);
      if (authDetails.refresh_token) {
        localStorage.setItem('refreshToken', authDetails.refresh_token);
      }

      const currentUser: User = {
        userId: authDetails.user_id,
        name: authDetails.name,
        username: authDetails.username,
      };
      localStorage.setItem('currentUser', JSON.stringify(currentUser));
      return currentUser; // 성공 시 User 객체 반환
    } else {
      // access_token 또는 user_id가 없는 비정상적인 성공 응답
      throw new Error(authDetails.message || 'Login failed: Missing token or user ID in response.');
    }
  } catch (error: any) {
    const backendError = error.response?.data as AuthData | ApiResponse; // 에러 응답도 다양한 형식이 올 수 있음
    // 백엔드 로그인 실패 시 응답 형식에 따라 에러 메시지 추출
    // 예: 백엔드가 401 시 {'message': 'Invalid username or password'} 를 반환한다면
    let errorMessage = 'An unknown login error occurred.';
    if (backendError && typeof backendError === 'object' && 'message' in backendError) {
        errorMessage = backendError.message as string;
    } else if (error.message) {
        errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
};

// ... (logout, getCurrentUser, checkAuthStorage 함수는 이전과 거의 동일하게 유지 가능) ...
export const logout = (): void => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('currentUser');
};

export const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('currentUser');
  if (userStr) {
    try { return JSON.parse(userStr) as User; }
    catch (e) { localStorage.removeItem('currentUser'); return null; }
  }
  return null;
};

export const checkAuthStorage = (): boolean => {
  return !!localStorage.getItem('accessToken');
};