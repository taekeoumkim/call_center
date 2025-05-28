// 상담사 로그인/회원가입 페이지
import React, { useState, useEffect } from 'react';
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

  const token = localStorage.getItem('token');

  // useEffect를 사용하여 컴포넌트 마운트 시 또는 token 변경 시 리디렉션 로직 실행
  useEffect(() => {
    if (token) {
      // 여기에 더 엄격한 토큰 유효성 검사를 추가할 수 있습니다.
      // 예: jwtDecode를 사용하여 토큰 만료 시간(exp) 확인
      // const decodedToken: { exp: number } = jwtDecode(token);
      // if (decodedToken.exp * 1000 > Date.now()) {
      //   navigate('/main');
      // } else {
      //   localStorage.removeItem('token'); // 만료된 토큰 제거
      // }
      
      // 현재는 토큰 존재 유무만으로 리디렉션
      navigate('/main');
    }
  }, [navigate, token]); // token이 변경될 때도 이 useEffect를 재실행

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

  // 만약 토큰이 있어서 /main으로 리디렉션될 예정이라면,
  // AuthPage의 UI를 렌더링하지 않고 null을 반환하여 깜빡임을 방지할 수 있습니다.
  if (token) { // 이 조건은 useEffect가 실행되기 전에 체크하여 UI 렌더링을 막음
    return null; // 또는 <LoadingSpinner /> 같은 것을 보여줄 수 있음
  }

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
