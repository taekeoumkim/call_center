// 메인페이지
import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import LogoImg from '../images/Logo.jpg';

// JWT 디코딩 결과 타입
interface DecodedToken {
  id: number;
  name: string;
  exp: number;
}

// 내담자 인터페이스
interface Client {
  id: number;
  phone: string;
  risk: 0 | 1 | 2;
}

// 위험도 라벨 매핑
const riskLabels = {
  0: '자살위험도 낮음',
  1: '자살위험도 중간',
  2: '자살위험도 높음',
};

// 위험도 색상 매핑 (테두리 색)
const riskColors = {
  0: 'border-green-500',
  1: 'border-yellow-400',
  2: 'border-red-500',
};

const MainPage = () => {
  // 상담 상태 및 상태 업데이트용
  const [isConsulting, setIsConsulting] = useState(false);
  // 내담자 목록 상태
  const [clients, setClients] = useState<Client[]>([]);
  // 상담사 이름 상태
  const [counselorName, setCounselorName] = useState('');

  // 페이지 이동용 hook
  const navigate = useNavigate();
  // JWT 토큰 가져오기
  const token = localStorage.getItem('token');

  // 스크롤 참조 및 interval 타이머 참조
  const scrollRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 대기열 목록 불러오기
  const fetchQueue = async () => {
    try {
      const res = await axios.get('/api/client/queue', {
        headers: { Authorization: `Bearer ${token}` },
      });
      // 위험도 높은 순으로 정렬
      const sorted = res.data.clients.sort((a: Client, b: Client) => b.risk - a.risk);
      setClients(sorted);
    } catch (err) {
      console.error('대기열 오류:', err);
    }
  };

  // 상담 상태 변경 요청
  const updateConsultingStatus = async (active: boolean) => {
    try {
      await axios.post(
        '/api/counselor/status',
        { is_active: active ? 1 : 0 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (err) {
      console.error('상담 상태 변경 실패:', err);
    }
  };

  // 상담 상태 초기 조회
  const getConsultingStatus = async (): Promise<boolean> => {
    try {
      const res = await axios.get('/api/counselor/status', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const active = res.data.is_active === 1;
      setIsConsulting(active);
      return active;
    } catch (err) {
      console.error('상담 상태 조회 실패:', err);
      setIsConsulting(false);
      return false;
    }
  };

  // 내담자 카드 클릭 핸들러 (배정 API 호출 추가)
  const handleClientCardClick = async (client_id: number) => {
    if (!isConsulting) { // 상담 시작 상태일 때만 배정 시도 (또는 다른 조건)
      alert('상담을 먼저 시작해주세요.');
      return;
    }

    if (!token) return;

    // 사용자에게 확인 (선택 사항)
    if (!window.confirm("이 내담자와 상담을 시작하시겠습니까?")) {
      return;
    }

    try {
      // 백엔드의 '/api/counselor/assign_client/<client_call_id>' API 호출
      const response = await axios.post(
        `/api/counselor/assign_client/${client_id}`, 
        {}, // POST 요청이지만 바디 데이터는 없을 수 있음
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.status === 200) {
        // 배정 성공 시 ClientDetailPage로 이동
        console.log("Client assigned:", response.data.client); // 성공 로그 (선택적)
        navigate(`/patient/${client_id}`);
      } else {
        // 배정 실패 (200이 아닌 경우, 또는 에러는 catch에서 처리)
        alert(response.data.message || '내담자 배정에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('내담자 배정 실패:', err);
      if (axios.isAxiosError(err) && err.response) {
        alert(`내담자 배정 실패: ${err.response.data.message || '서버 오류가 발생했습니다.'}`);
      } else {
        alert('내담자 배정 중 알 수 없는 오류가 발생했습니다.');
      }
    }
  };

  // 컴포넌트 마운트 시: 토큰 확인 및 상담사 이름 추출
  useEffect(() => {
    if (!token) {
      navigate('/');
    } else {
      try {
        const decoded = jwtDecode<DecodedToken>(token);
        setCounselorName(decoded.name);
      } catch (err) {
        console.error('토큰 디코딩 실패:', err);
        navigate('/');
      }
      getConsultingStatus(); // 현재 상담 상태 불러오기
    }
  }, [token, navigate]);

  // 상담 상태 변경 시: 대기열 polling 처리
  useEffect(() => {
    if (isConsulting) {
      fetchQueue(); // 즉시 1회 호출
      intervalRef.current = setInterval(fetchQueue, 5000); // 5초마다 polling
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setClients([]); // 대기열 초기화
    }

    // unmount 시에도 interval 제거
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isConsulting]);

  // 상담 시작/종료 버튼 핸들러
  const handleToggleConsulting = () => {
    const next = !isConsulting;
    setIsConsulting(next);
    updateConsultingStatus(next);
  };

  const handleLogout = async () => {
    if (token) { // 토큰이 있을 때만 상태 변경 API 호출 시도
      try {
        await axios.post(
          '/api/counselor/status', // <--- API 경로 수정
          { is_active: 0 }, // 상담사 상태를 'offline'으로 변경 (is_active: 0)
          { headers: { Authorization: `Bearer ${token}` } }
        );
        console.log('상담사 상태가 오프라인으로 변경되었습니다.');
      } catch (error) {
        console.error('로그아웃 중 상담사 상태 변경 실패:', error);
        // 이 에러를 사용자에게 알릴 수도 있지만,
        // 일반적으로 상태 변경 실패와 관계없이 클라이언트 측 로그아웃은 진행합니다.
      }
    }

    // 항상 클라이언트 측 로그아웃 작업 수행
    localStorage.removeItem('token'); // 로컬 스토리지에서 토큰 제거
    axios.defaults.headers.common['Authorization'] = null; // Axios 헤더에서도 토큰 제거 (선택적이지만 좋은 습관)
    navigate('/'); // 로그인 페이지로 리디렉션
    // 필요하다면, 상태 관리 라이브러리(Redux, Zustand 등)의 사용자 정보도 초기화합니다.
  };

  // 내담자 스크롤 좌우 이동 핸들러
  const scrollLeft = () => scrollRef.current?.scrollBy({ left: -300, behavior: 'smooth' });
  const scrollRight = () => scrollRef.current?.scrollBy({ left: 300, behavior: 'smooth' });

    // 대기열 전체 삭제
  const resetQueue = async () => {
    try {
      await axios.delete('/api/client/queue/reset', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setClients([]); // UI에서도 대기열 초기화
    } catch (err) {
      console.error('대기열 리셋 실패:', err);
      // 사용자에게 에러 메시지 표시
      if (axios.isAxiosError(err) && err.response) {
          alert(`대기열 리셋 실패: ${err.response.data.message || err.message}`);
      } else {
          alert('대기열 리셋 중 알 수 없는 오류가 발생했습니다.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white font-sans flex flex-col items-center">
      {/* Header */}
      <header className="w-full bg-white shadow-md flex justify-between items-center px-4 sm:px-6 py-3">
        <div className="flex items-center gap-3">
          <img src={LogoImg} alt="로고" className="h-8 w-8 rounded-full" />
          <h1 className="text-xl font-semibold text-blue-800 tracking-tight">Call Center</h1>
        </div>
        <div className="flex gap-4 sm:gap-6 text-sm">
          <button onClick={() => navigate('/mypage')} className="text-gray-600 hover:text-blue-600 transition">
            마이페이지
          </button>
          <button onClick={handleLogout} className="text-gray-600 hover:text-red-500 transition">
            로그아웃
          </button>
        </div>
      </header>
  
      {/* Main Container */}
      <main className="w-full max-w-screen-xl min-h-[70vh] mt-10 sm:mt-16 bg-white p-6 sm:p-10 lg:p-12 rounded-3xl shadow-2xl transition-all duration-300 hover:shadow-3xl">
        {/* 상담 박스 */}
        <section className="text-center mb-12 sm:mb-16">
          {counselorName && (
            <p className="text-base sm:text-xl font-semibold text-blue-800 mb-2">
              👩‍⚕️ {counselorName} 상담사님
            </p>
          )}
          <h2 className="text-2xl sm:text-3xl font-bold text-blue-800 mb-6 tracking-tight">
            {isConsulting ? '상담 중입니다' : '상담을 시작해주세요'}
          </h2>
          <button
            onClick={handleToggleConsulting}
            className={`px-8 sm:px-10 py-3 sm:py-4 text-base sm:text-lg font-semibold text-white rounded-full shadow-md transition-all duration-200 ${
              isConsulting
                ? 'bg-red-500 hover:bg-red-600 animate-pulse ring-2 ring-red-300'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isConsulting ? '상담 종료' : '상담 시작'}
          </button>
        </section>
  
        {/* 내담자 대기열 */}
        <section>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-3 sm:gap-0">
            <h3 className="text-xl sm:text-2xl font-bold text-blue-800">내담자 대기열</h3>
            <button
              onClick={() => {
                if (window.confirm('정말 대기열을 리셋 하시겠습니까?')) {
                  resetQueue();
                }
              }}
              className="text-sm px-4 py-2 bg-red-100 text-red-600 rounded-full hover:bg-red-200 transition"
            >
              대기열 리셋
            </button>
          </div>
  
          <div className="relative">
            <button
              onClick={scrollLeft}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 text-2xl sm:text-3xl text-gray-400 hover:text-gray-700 px-2"
            >
              ◀
            </button>
  
            <div
              ref={scrollRef}
              className="px-4 sm:px-6 flex overflow-x-auto gap-6 py-3 scrollbar-hide"
            >
              {clients.map((client) => (
                <div
                  key={client.id}
                  onClick={() => handleClientCardClick(client.id)}
                  className={`min-w-[240px] bg-blue-50 border-t-4 ${riskColors[client.risk]} rounded-xl shadow-md p-5 cursor-pointer hover:shadow-lg hover:scale-105 transition`}
                >
                  <div className="font-semibold text-blue-800 mb-1">{riskLabels[client.risk]}</div>
                  <div className="text-sm text-gray-600">📞 {client.phone}</div>
                </div>
              ))}
            </div>
  
            <button
              onClick={scrollRight}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 text-2xl sm:text-3xl text-gray-400 hover:text-gray-700 px-2"
            >
              ▶
            </button>
          </div>
        </section>
      </main>
  
      <footer className="text-xs text-gray-400 mt-8 mb-4 text-center px-4">
        © 2025 Call Center. All rights reserved.
      </footer>
    </div>
  );
};

export default MainPage;