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
    <div className="flex flex-col items-center justify-start min-h-screen pt-[150px] bg-gray-100">
      {/* 상단 로고 및 앱 타이틀 */}
      <div className="flex items-center justify-center mb-6">
        <img
          src={LogoImg}
          alt="Logo"
          className="w-10 h-10 rounded-full object-cover mr-3"
        />
        <h1 className="text-3xl font-bold text-blue-500">Call Center</h1>
      </div>

      {/* 로그인/회원가입 폼 */}
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md space-y-4"
      >
        {/* 폼 제목 */}
        <h2 className="text-2xl font-bold text-center">
          {isLoginMode ? '로그인' : '회원가입'}
        </h2>

        {/* 이름 입력 필드 (회원가입 시에만 표시) */}
        {!isLoginMode && (
          <input
            type="text"
            name="name"
            placeholder="이름"
            value={formData.name}
            onChange={handleChange}
            className="w-full p-2 border rounded-lg"
            required
          />
        )}

        {/* 아이디 입력 필드 */}
        <input
          type="text"
          name="username"
          placeholder="아이디"
          value={formData.username}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg"
          required
        />

        {/* 비밀번호 입력 필드 */}
        <input
          type="password"
          name="password"
          placeholder="비밀번호"
          value={formData.password}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg"
          required
        />

        {/* 비밀번호 확인 입력 필드 (회원가입 시에만 표시) */}
        {!isLoginMode && (
          <input
            type="password"
            name="confirmPassword"
            placeholder="비밀번호 확인"
            value={formData.confirmPassword}
            onChange={handleChange}
            className="w-full p-2 border rounded-lg"
            required
          />
        )}

        {/* 에러 메시지 출력 */}
        {error && <p className="text-red-500 text-sm">{error}</p>}

        {/* 로그인/회원가입 버튼 */}
        <button
          type="submit"
          className="w-full bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600"
        >
          {isLoginMode ? '로그인' : '회원가입'}
        </button>

        {/* 로그인/회원가입 모드 전환 링크 */}
        <p
          className="text-sm text-center text-gray-600 cursor-pointer hover:underline"
          onClick={() => setIsLoginMode(!isLoginMode)}
        >
          {isLoginMode
            ? '계정이 없으신가요? 회원가입'
            : '이미 계정이 있으신가요? 로그인'}
        </p>
      </form>
    </div>
  );
};

export default AuthPage;
