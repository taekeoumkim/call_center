// axios를 사용하여 HTTP 요청을 보냄
import axios from 'axios';

// 로깅 함수 추가
const logEvent = (event: string, data?: any) => {
  console.log(`[AuthAPI] ${event}`, data ? data : '');
};

export async function loginCounselor(username: string, password: string): Promise<string> {
  try {
    logEvent('로그인 시도', { username });
    const response = await axios.post('/api/auth/login', { username, password });
    const token = response.data.access_token;

    if (token && typeof token === 'string' && token.split('.').length === 3) {
      localStorage.setItem('token', token); // 로컬 스토리지에 저장하는 키는 'token' 그대로 사용해도 무방
      logEvent('로그인 성공', { username });
      return token;
    } else {
      logEvent('로그인 실패 - 유효하지 않은 토큰', { token });
      console.error('Invalid access_token received from server:', token);
      // 백엔드에서 'message' 필드도 보내므로, 그것을 사용할 수도 있음
      const serverMessage = response.data.message;
      throw new Error(serverMessage || '로그인에 실패했습니다: 서버로부터 유효하지 않은 토큰을 받았습니다.');
    }
  } catch (error: any) {
    logEvent('로그인 에러', { 
      error: error instanceof Error ? error.message : 'Unknown error',
      response: error.response?.data 
    });
    console.error('Login error in authApi:', error);
    if (error.response) {
      console.error('Login error response data:', error.response.data);
      console.error('Login error response status:', error.response.status);
      // 백엔드가 {message: "..."} 형식으로 에러를 보내므로 이를 활용
      throw new Error(error.response.data.message || '아이디 또는 비밀번호가 올바르지 않습니다.');
    }
    // axios 요청 자체가 실패한 경우 (네트워크 오류 등)
    throw new Error(error.message || '로그인 중 오류가 발생했습니다. 네트워크 연결을 확인해주세요.');
  }
}

export async function registerCounselor(data: {
  name: string;
  username: string;
  password: string;
}): Promise<void> {
  const { name, username, password } = data;

  try {
    logEvent('회원가입 시도', { username, name });
    console.log('회원가입 요청 데이터:', { name, username, password: '***' });
    const response = await axios.post('/api/auth/register', { name, username, password });
    console.log('회원가입 응답:', response.data);
    logEvent('회원가입 성공', { username });
  } catch (error: any) {
    logEvent('회원가입 실패', { 
      error: error instanceof Error ? error.message : 'Unknown error',
      response: error.response?.data 
    });
    console.error('회원가입 상세 오류:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      headers: error.response?.headers
    });
    // 서버가 명시적인 에러 메시지를 보낸 경우 (백엔드에서 {"error": "..."} 또는 {"message": "..."} 형식으로 응답)
    if (error.response && error.response.data) {
      throw new Error(error.response.data.error || error.response.data.message || '회원가입 중 오류가 발생했습니다.');
    }

    // 기타 에러 처리
    throw new Error('회원가입 중 오류가 발생했습니다.');
  }
}