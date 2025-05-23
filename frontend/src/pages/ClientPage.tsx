// 내담자 상황 녹음, 전화번호 입력 페이지
import React, { useState, useRef, useEffect } from 'react';
import LogoImg from '../images/Logo.jpg';

const ClientPage: React.FC = () => {
  // 사용자의 녹음 상태를 관리
  const [isRecording, setIsRecording] = useState(false);
  // MediaRecorder 객체를 저장 (녹음 제어용)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  // 녹음 시간 (초)을 저장
  const [recordingTime, setRecordingTime] = useState(0);
  // 전화번호 입력값 상태
  const [phoneNumber, setPhoneNumber] = useState('');
  // 녹음된 음성 데이터를 Blob으로 저장
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  // setInterval로 만든 타이머를 기억하기 위한 참조값
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 녹음 상태 변화 감지 후 타이머 동작 제어
  useEffect(() => {
    if (isRecording) {
      // 1초마다 recordingTime 증가
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      // 녹음이 멈추면 타이머 제거
      if (timerRef.current) clearInterval(timerRef.current);
    }

    // 컴포넌트 언마운트 시 타이머 정리
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  // 녹음 시작 함수
  const startRecording = async () => {
    try {
      setAudioBlob(null); // 이전 녹음 삭제

      // 녹음 중일 경우 먼저 중지
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }

      // 마이크 권한 요청 및 스트림 생성
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const localChunks: Blob[] = [];

      // 데이터 조각이 수신될 때마다 localChunks에 저장
      recorder.ondataavailable = (e: BlobEvent) => {
        localChunks.push(e.data);
      };

      // 녹음이 완료되면 Blob으로 변환하고 저장
      recorder.onstop = () => {
        const blob = new Blob(localChunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        // 마이크 스트림 정지 (자원 반납)
        stream.getTracks().forEach((track) => track.stop());
      };

      // 녹음 시작
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0); // 타이머 초기화
    } catch (error) {
      console.error('마이크 접근 오류:', error);
      alert('마이크 접근을 허용해주세요.');
    }
  };

  // 녹음 중지 함수
  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // 버튼 클릭 시 녹음 시작/중지 토글
  const handleRecordToggle = () => {
    isRecording ? stopRecording() : startRecording();
  };

  // 전화번호 입력 처리: 숫자만 필터링 후 하이픈 자동 삽입
  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, ''); // 숫자 외 제거

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

  // 전화번호 유효성 검사(010-0000-0000 형식)
  const validatePhoneNumber = (phone: string): boolean => {
    const phoneRegex = /^010-\d{4}-\d{4}$/;
    return phoneRegex.test(phone);
  };

  // 제출 버튼 클릭 시 실행
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
    formData.append('audio', audioBlob, 'recording.webm'); // 오디오 파일 첨부
    formData.append('phone', phoneNumber); // 전화번호 첨부

    try {
      const response = await fetch('http://localhost:5000/api/submit', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        alert('제출되었습니다.');
        // 입력 초기화
        setPhoneNumber('');
        setAudioBlob(null);
        setRecordingTime(0);
      } else {
        const result = await response.json();
        // 상담사 부재 등의 오류 처리
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
      {/* 상단 로고 및 제목 */}
      <header className='w-full bg-white shadow flex items-center px-6 py-3'>
        <img src={LogoImg} alt='로고' className='h-10 w-10 rounded-full mr-3' />
        <h1 className='text-xl font-bold text-gray-800'>Call Center</h1>
      </header>

      {/* 메인 폼 영역 */}
      <main className='w-full max-w-lg mt-10 bg-white p-6 rounded-xl shadow-md'>
        <h2 className='text-2xl font-semibold text-center text-gray-800 mb-2'>
          내담자 페이지
        </h2>
        <p className='text-center text-gray-600 mb-6'>
          버튼을 누르고 현재 상황을 말씀해 주세요
        </p>

        {/* 녹음 버튼 */}
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

        {/* 녹음 시간 표시 */}
        <p className='text-center text-lg mb-4'>
          ⏱️ 녹음 시간: <span className='font-mono'>{recordingTime}s</span>
        </p>

        {/* 녹음 미리 듣기 */}
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

        {/* 전화번호 입력 */}
        <input
          type='tel'
          placeholder='전화번호 (예: 010-1234-5678)'
          value={phoneNumber}
          onChange={handlePhoneChange}
          maxLength={13}
          className='w-full border border-gray-300 rounded-md px-4 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400'
        />

        {/* 제출 버튼 */}
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
