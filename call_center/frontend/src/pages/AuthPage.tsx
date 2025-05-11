// src/pages/AuthPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    name: '',
    username: '',
    password: '',
  });
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    const url = isLogin ? '/api/auth/login' : '/api/auth/register';

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (!res.ok) throw new Error('인증 실패');

      if (isLogin) {
        navigate('/main');
      } else {
        alert('회원가입 완료. 로그인 해주세요.');
        setIsLogin(true);
      }
    } catch (err) {
      alert('오류가 발생했습니다.');
    }
  };

  return (
    <div className='min-h-screen flex flex-col items-center justify-center p-6 bg-gray-100'>
      <h1 className='text-2xl font-bold mb-4'>
        {isLogin ? '상담사 로그인' : '상담사 회원가입'}
      </h1>

      {!isLogin && (
        <input
          type='text'
          name='name'
          placeholder='이름'
          className='mb-3 p-2 border w-64 rounded'
          value={form.name}
          onChange={handleChange}
        />
      )}
      <input
        type='text'
        name='username'
        placeholder='아이디'
        className='mb-3 p-2 border w-64 rounded'
        value={form.username}
        onChange={handleChange}
      />
      <input
        type='password'
        name='password'
        placeholder='비밀번호'
        className='mb-3 p-2 border w-64 rounded'
        value={form.password}
        onChange={handleChange}
      />
      <button
        onClick={handleSubmit}
        className='mb-3 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
      >
        {isLogin ? '로그인' : '회원가입'}
      </button>

      <p
        className='text-blue-500 cursor-pointer underline'
        onClick={() => setIsLogin(!isLogin)}
      >
        {isLogin ? '회원가입 하기' : '로그인 하기'}
      </p>
    </div>
  );
}
