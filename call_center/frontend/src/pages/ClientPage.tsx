// src/pages/ClientPage.tsx
import { useState, useEffect } from 'react';
import Recorder from '../components/Recorder';

export default function ClientPage() {
  const [password, setPassword] = useState('');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  useEffect(() => {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance('현재 상황을 말해주세요');
    synth.speak(utter);
  }, []);

  const handleSubmit = async () => {
    if (!audioBlob || !password) {
      alert('음성과 비밀번호를 모두 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('password', password);

    try {
      await fetch('/api/client/submit', {
        method: 'POST',
        body: formData,
      });
      alert('제출이 완료되었습니다.');
    } catch (error) {
      alert('제출 중 오류 발생.');
    }
  };

  return (
    <div className='min-h-screen flex flex-col items-center justify-center p-6 bg-gray-100'>
      <h1 className='text-2xl font-semibold mb-6'>내담자 페이지</h1>
      <Recorder onRecorded={(blob) => setAudioBlob(blob)} />
      <input
        type='password'
        placeholder='비밀번호 입력'
        className='mt-4 p-2 border border-gray-400 rounded w-64'
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button
        className='mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
        onClick={handleSubmit}
      >
        제출
      </button>
    </div>
  );
}
