// axios를 사용하여 HTTP 요청을 보냄
import axios from 'axios';

// 백엔드 API의 기본 URL
const API_BASE = 'http://localhost:5000';

export async function loginCounselor(username: string, password: string): Promise<string> {
  try {
    // 로그인 요청 전송
    const response = await axios.post(`${API_BASE}/auth/login`, { username, password });

    // 응답으로부터 JWT 토큰 반환
    return response.data.token;
  } catch (error: any) {
    // 401 Unauthorized 에러: 아이디/비밀번호 오류
    if (error.response && error.response.status === 401) {
      throw new Error('아이디 또는 비밀번호가 올바르지 않습니다.');
    }

    // 기타 에러 처리
    throw new Error('로그인 중 오류가 발생했습니다.');
  }
}

export async function registerCounselor(data: {
  name: string;
  username: string;
  password: string;
}): Promise<void> {
  const { name, username, password } = data;

  try {
    // 회원가입 요청 전송
    await axios.post(`${API_BASE}/auth/register`, { name, username, password });
  } catch (error: any) {
    // 서버가 명시적인 에러 메시지를 보낸 경우
    if (error.response && error.response.data && error.response.data.error) {
      throw new Error(error.response.data.error);
    }

    // 기타 에러 처리
    throw new Error('회원가입 중 오류가 발생했습니다.');
  }
}