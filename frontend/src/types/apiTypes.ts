// frontend/src/types/apiTypes.ts

// 일반적인 API 응답 형식
export interface ApiResponse<T = any> {
    status?: string;
    data?: T;
    message?: string;
    error?: {
      code?: string | number;
      name?: string;
      description?: string;
      details?: any;
    };
  }
  
  // 회원가입 성공 시 백엔드가 반환하는 data 객체 내의 타입
  export interface SignupSuccessData {
    user_id: number;
    username: string;
    message?: string; // 최상위 message와 중복될 수 있으나, data 내에도 있을 수 있음
  }