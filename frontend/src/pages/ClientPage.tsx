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
          if (prev >= MAX_RECORDING_TIME) return prev; // 초과 증가 방지
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
    <div className='min-h-screen bg-gray-50 flex flex-col items-center'>
      <header className='w-full bg-white shadow flex items-center px-6 py-3'>
        <img src={LogoImg} alt='로고' className='h-10 w-10 rounded-full mr-3' />
        <h1 className='text-xl font-bold text-gray-800'>Call Center</h1>
      </header>

      <main className='w-full max-w-lg mt-10 bg-white p-6 rounded-xl shadow-md'>
        <h2 className='text-2xl font-semibold text-center text-gray-800 mb-2'>
          내담자 페이지
        </h2>
        <p className='text-center text-gray-600 mb-6'>
          버튼을 누르고 현재 상황을 말씀해 주세요
        </p>

        <div className='flex justify-center mb-4'>
          <button
            onClick={handleRecordToggle}
            className={`px-6 py-3 rounded-full font-semibold shadow transition-all duration-200 ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-green-600 hover:bg-green-700'
            } text-white`}
          >
            🎙️ {isRecording ? '녹음 중지' : '녹음 시작'}
          </button>
        </div>

        <p className='text-center text-lg mb-4'>
          ⏱️ 녹음 시간: <span className='font-mono'>{recordingTime}s / {MAX_RECORDING_TIME}s</span>
        </p>

        {audioBlob && (
          <div className='mb-6 text-center'>
            <p className='mb-2 text-gray-700 font-medium'>
              🔊 녹음된 내용 듣기
            </p>
            <audio controls className='w-full'>
              <source src={URL.createObjectURL(audioBlob)} type='audio/webm' />
              브라우저가 오디오 태그를 지원하지 않습니다.
            </audio>
          </div>
        )}

        <input
          type='tel'
          placeholder='전화번호 (예: 010-1234-5678)'
          value={phoneNumber}
          onChange={handlePhoneChange}
          maxLength={13}
          className='w-full border border-gray-300 rounded-md px-4 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400'
        />

        <button
          onClick={handleSubmit}
          className='w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md shadow transition-all duration-200'
        >
          제출
        </button>
      </main>
    </div>
  );
};

export default ClientPage;
