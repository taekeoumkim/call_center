// frontend/src/pages/AuthPage.tsx
import React, { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom'; // 페이지 이동을 위해
import { signup, login, User } from '../services/authService'; // 경로 확인
import { useAuth } from '../context/AuthContext';

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true); // true: 로그인 폼, false: 회원가입 폼
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState(''); // 회원가입용 이름
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login: contextLogin } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const loggedInUser: User = await login({ username, password }); // 반환 타입이 User
        contextLogin(loggedInUser); // AuthContext의 상태 업데이트
        navigate('/main');
      } else {
        // ... (회원가입 로직 - 여기도 signup 응답 구조 확인 필요)
        // 이전 답변에서 signup 응답 구조도 확인해서 수정해야 함.
        // 예: const signupResponse = await signup({ username, password, name });
        // if (signupResponse.message === 'User created successfully' || (signupResponse.data && signupResponse.data.user_id)) { ... }
      }
    } catch (err: any) {
      console.error(isLogin ? 'Login error:' : 'Signup error:', err);
      // err 객체가 Error 인스턴스이므로 err.message 사용
      const errorMessage = err.message || (isLogin ? 'Login failed.' : 'Signup failed.');
      setError(errorMessage);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white shadow-md rounded-lg w-full max-w-md">
        <div className="flex border-b mb-6">
          <button
            className={`flex-1 py-2 text-center ${isLogin ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
            onClick={() => { setIsLogin(true); setError(null); }}
          >
            로그인
          </button>
          <button
            className={`flex-1 py-2 text-center ${!isLogin ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
            onClick={() => { setIsLogin(false); setError(null); }}
          >
            회원가입
          </button>
        </div>

        <h2 className="text-2xl font-bold mb-6 text-center">{isLogin ? '로그인' : '회원가입'}</h2>
        {error && <p className="mb-4 text-sm text-red-600 bg-red-100 p-3 rounded">{error}</p>}
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
                이름
              </label>
              <input
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                id="name"
                type="text"
                placeholder="이름을 입력하세요"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required={!isLogin}
              />
            </div>
          )}
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
              아이디 (Username)
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="username"
              type="text" // 또는 "email"
              placeholder="아이디를 입력하세요"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              비밀번호
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              id="password"
              type="password"
              placeholder="비밀번호를 입력하세요"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="flex items-center justify-between">
            <button
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
              type="submit"
              disabled={loading}
            >
              {loading ? '처리 중...' : (isLogin ? '로그인' : '회원가입')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;