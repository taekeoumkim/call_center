// 메인페이지
import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import LogoImg from '../images/Logo.jpg';

// Axios 기본 URL 설정
axios.defaults.baseURL = 'http://localhost:5000';

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
      const res = await axios.get('/api/queue', {
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
        '/api/status',
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
      const res = await axios.get('/api/status', {
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

  // 로그아웃 처리
  const handleLogout = async () => {
    try {
      await updateConsultingStatus(false); // 상담 종료 상태로 전환
    } catch (err) {
      console.error('로그아웃 중 상태 업데이트 실패:', err);
    }
    localStorage.removeItem('token'); // 토큰 삭제
    navigate('/'); // 로그인 페이지로 이동
  };

  // 내담자 스크롤 좌우 이동 핸들러
  const scrollLeft = () => scrollRef.current?.scrollBy({ left: -300, behavior: 'smooth' });
  const scrollRight = () => scrollRef.current?.scrollBy({ left: 300, behavior: 'smooth' });

    // 대기열 전체 삭제
  const resetQueue = async () => {
    try {
      await axios.delete('/api/queue/reset', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setClients([]); // UI에서도 대기열 초기화
    } catch (err) {
      console.error('대기열 리셋 실패:', err);
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen p-8">
      {/* 상단 바 (로고 + 마이페이지/로그아웃) */}
      <header className="flex justify-between items-center mb-12">
        <div className="flex items-center gap-3">
          <img src={LogoImg} alt="logo" className="w-10 h-10" />
          <h1 className="text-2xl font-bold text-gray-800">Call Center</h1>
        </div>
        <div className="flex gap-6">
          <button onClick={() => navigate('/mypage')} className="text-gray-600 hover:text-blue-600 transition">
            마이페이지
          </button>
          <button onClick={handleLogout} className="text-gray-600 hover:text-red-500 transition">
            로그아웃
          </button>
        </div>
      </header>

      {/* 상담 박스 */}
      <section className="flex justify-center mb-12">
        <div className="bg-blue-100 p-10 rounded-2xl shadow-xl text-center w-full max-w-lg">
          {counselorName && (
            <div className="text-xl font-semibold mb-2">
              {counselorName} 상담사님
            </div>
          )}
          <h2 className="text-2xl font-bold mb-6">
            {isConsulting ? '상담 중입니다' : '상담을 시작해주세요'}
          </h2>
          <button
            onClick={handleToggleConsulting}
            className={`px-8 py-3 text-white font-medium rounded-xl shadow-md transition duration-200 ${
              isConsulting ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isConsulting ? '상담 종료' : '상담 시작'}
          </button>
        </div>
      </section>

      {/* 내담자 대기열 목록 */}
      <section>
        <div className="flex items-center mb-4">
          <h3 className="text-xl font-bold text-gray-800 mr-2">내담자 대기열</h3>
          <button
            onClick={() => {
              if (window.confirm('정말 대기열을 리셋 하시겠습니까?')) {
                resetQueue();
              }
            }}
            className="text-sm px-4 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200 transition"
          >
            리셋
          </button>
        </div>

        <div className="relative">
          <button
            onClick={scrollLeft}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 text-3xl text-gray-400 hover:text-gray-700 px-2"
          >
            ◀
          </button>

          <div
            ref={scrollRef}
            className="mx-10 flex overflow-x-auto gap-5 py-3 scrollbar-hide"
          >
            {clients.map((client) => (
              <div
                key={client.id}
                onClick={() => navigate(`/patient/${client.id}`)}
                className={`min-w-[220px] bg-white border-t-4 ${riskColors[client.risk]} rounded-xl shadow-md p-5 cursor-pointer hover:shadow-lg hover:scale-105 transition`}
              >
                <div className="font-semibold mb-2 text-gray-800">{riskLabels[client.risk]}</div>
                <div className="text-sm text-gray-500">전화번호: {client.phone}</div>
              </div>
            ))}
          </div>

          <button
            onClick={scrollRight}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 text-3xl text-gray-400 hover:text-gray-700 px-2"
          >
            ▶
          </button>
        </div>
      </section>
    </div>
  );
};

export default MainPage;