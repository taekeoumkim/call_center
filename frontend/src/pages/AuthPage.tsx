// 상담사 로그인/회원가입 페이지
import React, { useState } from 'react';
import { loginCounselor, registerCounselor } from '../api/authApi'; // 인증 API 호출 함수 import
import { useNavigate } from 'react-router-dom'; // 페이지 이동을 위한 hook
import LogoImg from '../images/Logo.jpg'; // 로고 이미지 import

const AuthPage: React.FC = () => {
  // 로그인 모드 여부 상태 (true = 로그인, false = 회원가입)
  const [isLoginMode, setIsLoginMode] = useState(true);

  // 폼 입력값 상태 (이름, 아이디, 비밀번호 등)
  const [formData, setFormData] = useState({
    name: '',             // 상담사 이름
    username: '',         // 아이디
    password: '',         // 비밀번호
    confirmPassword: '',  // 비밀번호 확인 (회원가입용)
  });

  // 에러 메시지 상태
  const [error, setError] = useState('');

  // 페이지 이동을 위한 훅
  const navigate = useNavigate();

  // 입력값 유효성 검사 함수 (회원가입 시에만 적용됨)
  const validateInput = (): boolean => {
    const { username, password, confirmPassword } = formData;

    if (isLoginMode) {
      // 로그인 모드일 경우 별도 유효성 검사 없이 통과
      return true;
    }

    // 회원가입 모드일 경우 유효성 검사 진행
    const usernameRegex = /^[a-zA-Z0-9]{4,12}$/; // 아이디: 영문+숫자, 4~12자
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/; // 비밀번호: 영문+숫자 포함, 8자 이상

    if (!usernameRegex.test(username)) {
      setError('아이디는 4~12자의 영문 또는 숫자여야 합니다.');
      return false;
    }

    if (!passwordRegex.test(password)) {
      setError('비밀번호는 8자 이상이며 영문과 숫자를 포함해야 합니다.');
      return false;
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return false;
    }

    setError('');
    return true;
  };

  // 입력값 변경 핸들러
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 유효성 검사 실패 시 중단
    if (!validateInput()) return;

    try {
      if (isLoginMode) {
        // 로그인 시도
        const token = await loginCounselor(
          formData.username,
          formData.password
        );

        localStorage.setItem('token', token);
        navigate('/main');
      } else {
        // 회원가입 요청
        await registerCounselor({
          name: formData.name,
          username: formData.username,
          password: formData.password,
        });

        alert('회원가입 성공! 로그인 해주세요.');
        setFormData({
          name: '',
          username: '',
          password: '',
          confirmPassword: '',
        }); // 입력값 초기화
        setIsLoginMode(true); // 로그인 모드로 전환
      }
    } catch (err: any) {
      setError(err.message || '오류가 발생했습니다.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center font-sans">
      {/* 상단 헤더 */}
      <header className="w-full bg-white shadow-md flex items-center px-6 py-2.5">
        <img src={LogoImg} alt="로고" className="h-8 w-8 rounded-full mr-2" />
        <h1 className="text-xl font-semibold text-blue-800 tracking-tight">Call Center</h1>
      </header>

      {/* 로그인/회원가입 카드 */}
      <main className="w-full max-w-md mt-16 bg-white p-10 rounded-3xl shadow-xl transition-all duration-300 hover:shadow-2xl">
        <h2 className="text-3xl font-bold text-center text-blue-800 mb-4">
          {isLoginMode ? '상담사 로그인' : '상담사 회원가입'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLoginMode && (
            <input
              type="text"
              name="name"
              placeholder="이름"
              value={formData.name}
              onChange={handleChange}
              className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
              required
            />
          )}

          <input
            type="text"
            name="username"
            placeholder="아이디"
            value={formData.username}
            onChange={handleChange}
            className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
            required
          />

          <input
            type="password"
            name="password"
            placeholder="비밀번호"
            value={formData.password}
            onChange={handleChange}
            className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
            required
          />

          {!isLoginMode && (
            <input
              type="password"
              name="confirmPassword"
              placeholder="비밀번호 확인"
              value={formData.confirmPassword}
              onChange={handleChange}
              className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
              required
            />
          )}

          {error && <p className="text-red-500 text-sm text-center">{error}</p>}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl shadow-md transition-all duration-200 text-sm"
          >
            {isLoginMode ? '로그인' : '회원가입'}
          </button>

          <p
            className="text-sm text-center text-blue-600 cursor-pointer hover:underline"
            onClick={() => setIsLoginMode(!isLoginMode)}
          >
            {isLoginMode
              ? '계정이 없으신가요? 회원가입'
              : '이미 계정이 있으신가요? 로그인'}
          </p>
        </form>
      </main>

      <footer className="text-xs text-gray-400 mt-8 mb-4">
        © 2025 Call Center. All rights reserved.
      </footer>
    </div>
  );
};

export default AuthPage;
