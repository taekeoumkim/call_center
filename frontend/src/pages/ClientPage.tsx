// 내담자 상황 녹음, 전화번호 입력 페이지
import React, { useState, useRef, useEffect } from 'react';
import LogoImg from '../images/Logo.jpg';

const ClientPage: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const MAX_RECORDING_TIME = 10;

  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= MAX_RECORDING_TIME) return prev;
          return prev + 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
  
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  useEffect(() => {
    if (recordingTime >= MAX_RECORDING_TIME && isRecording) {
      stopRecording();
      alert('최대 10초까지 녹음할 수 있습니다.');
    }
  }, [recordingTime, isRecording]);

  const startRecording = async () => {
    try {
      setAudioBlob(null);

      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const localChunks: Blob[] = [];

      recorder.ondataavailable = (e: BlobEvent) => {
        localChunks.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(localChunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
    } catch (error) {
      console.error('마이크 접근 오류:', error);
      alert('마이크 접근을 허용해주세요.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const handleRecordToggle = () => {
    isRecording ? stopRecording() : startRecording();
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');

    if (value.length <= 3) {
      setPhoneNumber(value);
    } else if (value.length <= 7) {
      setPhoneNumber(`${value.slice(0, 3)}-${value.slice(3)}`);
    } else {
      setPhoneNumber(
        `${value.slice(0, 3)}-${value.slice(3, 7)}-${value.slice(7, 11)}`
      );
    }
  };

  const validatePhoneNumber = (phone: string): boolean => {
    const phoneRegex = /^010-\d{4}-\d{4}$/;
    return phoneRegex.test(phone);
  };

  const handleSubmit = async () => {
    if (!audioBlob || !phoneNumber) {
      alert('녹음과 전화번호를 모두 입력해주세요.');
      return;
    }

    if (!validatePhoneNumber(phoneNumber)) {
      alert('올바른 전화번호 형식(010-0000-0000)으로 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('phone', phoneNumber);

    try {
      const response = await fetch('http://localhost:5000/api/submit', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        alert('제출되었습니다.');
        setPhoneNumber('');
        setAudioBlob(null);
        setRecordingTime(0);
      } else {
        const result = await response.json();
        if (result.error === 'No available counselors') {
          alert('현재 상담사가 없습니다. 나중에 다시 시도해주세요.');
        } else {
          alert('제출에 실패했습니다.');
        }
      }
    } catch (error) {
      console.error('제출 중 오류:', error);
      alert('서버 오류가 발생했습니다.');
    }
  };

  return (
    <div className='min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center font-sans'>
      <header className='w-full bg-white shadow-md flex items-center px-6 py-2.5'>
        <img src={LogoImg} alt='로고' className='h-8 w-8 rounded-full mr-2' />
        <h1 className='text-xl font-semibold text-blue-800 tracking-tight'>Call Center</h1>
      </header>
  
      <main className='w-full max-w-lg mt-12 bg-white p-10 rounded-3xl shadow-xl transition-all duration-300 hover:shadow-2xl'>
        <h2 className='text-3xl font-bold text-center text-blue-800 mb-2 tracking-tight'>내담자 상담</h2>
        <p className='text-center text-gray-600 mb-8 text-sm'>
          버튼을 눌러 현재 상황을 말씀해주세요.
        </p>
  
        <div className='flex justify-center mb-6'>
          <button
            onClick={handleRecordToggle}
            className={`flex items-center justify-center gap-2 w-44 py-3 rounded-full font-medium text-lg shadow-md transition-all duration-300 ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse ring-2 ring-red-300'
                : 'bg-green-500 hover:bg-green-600'
            } text-white`}
          >
            🎙️ {isRecording ? '중지하기' : '녹음 시작'}
          </button>
        </div>
  
        <div className='text-center text-blue-700 text-sm mb-6'>
          <span className='inline-block px-4 py-1 bg-blue-100 rounded-full font-mono'>
            ⏱ {recordingTime}s / {MAX_RECORDING_TIME}s
          </span>
        </div>
  
        {audioBlob && (
          <div className='mb-6'>
            <div className='border border-blue-200 p-4 rounded-xl shadow-sm bg-blue-50'>
              <p className='mb-2 text-blue-700 font-semibold text-sm text-center'>🔊 녹음된 음성</p>
              <audio controls className='w-full'>
                <source src={URL.createObjectURL(audioBlob)} type='audio/webm' />
                브라우저가 오디오를 지원하지 않습니다.
              </audio>
            </div>
          </div>
        )}
  
        <input
          type='tel'
          placeholder='전화번호 입력: 010-0000-0000'
          value={phoneNumber}
          onChange={handlePhoneChange}
          maxLength={13}
          className='w-full border border-blue-200 rounded-xl px-4 py-3 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm'
        />
  
        <button
          onClick={handleSubmit}
          className='w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl shadow-md transition-all duration-200 text-sm'
        >
          상담 요청하기
        </button>
      </main>
  
      <footer className='text-xs text-gray-400 mt-8 mb-4'>
        © 2025 Call Center. All rights reserved.
      </footer>
    </div>
  );
};

export default ClientPage;
