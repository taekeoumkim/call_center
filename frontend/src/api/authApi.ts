// axios를 사용하여 HTTP 요청을 보냄
import axios from 'axios';

export async function loginCounselor(username: string, password: string): Promise<string> {
  try {
    // 로그인 요청 전송 (상대 경로로 수정)
    const response = await axios.post('/api/auth/login', { username, password }); // 수정된 부분

    // 응답으로부터 JWT 토큰 반환 (백엔드에서 응답 형식을 {"token": "..."}으로 맞춰야 함)
    return response.data.token;
  } catch (error: any) {
    // 401 Unauthorized 에러: 아이디/비밀번호 오류
    if (error.response && error.response.status === 401) {
      // 백엔드가 반환하는 에러 메시지 형식에 따라 아래를 조정할 수 있습니다.
      // 예: error.response.data.message 또는 error.response.data.error
      throw new Error(error.response.data.message || '아이디 또는 비밀번호가 올바르지 않습니다.');
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
    // 회원가입 요청 전송 (상대 경로로 수정)
    await axios.post('/api/auth/register', { name, username, password });
  } catch (error: any) {
    // 서버가 명시적인 에러 메시지를 보낸 경우 (백엔드에서 {"error": "..."} 또는 {"message": "..."} 형식으로 응답)
    if (error.response && error.response.data) {
      throw new Error(error.response.data.error || error.response.data.message || '회원가입 중 오류가 발생했습니다.');
    }

    // 기타 에러 처리
    throw new Error('회원가입 중 오류가 발생했습니다.');
  }
}