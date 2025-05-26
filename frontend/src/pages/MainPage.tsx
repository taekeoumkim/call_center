// frontend/src/pages/MainPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom'; // Link 추가
import { getCurrentUser, User, logout } from '../services/authService'; // 경로 확인
import { updateCounselorStatus, getCounselorQueue, QueueItem } from '../services/counselorService'; // 경로 확인

const MainPage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isCounseling, setIsCounseling] = useState(false); // 상담 시작/종료 상태
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // 로그인한 사용자 정보 로드
  useEffect(() => {
    const user = getCurrentUser();
    if (user) {
      setCurrentUser(user);
    } else {
      navigate('/auth'); // 사용자가 없으면 로그인 페이지로 (이중 안전장치)
    }
  }, [navigate]);

  // 대기열 가져오기 함수
  const fetchQueue = useCallback(async () => {
    if (!currentUser || !isCounseling) { // 상담 중 상태일 때만, 그리고 사용자가 있을 때만
      // setQueue([]); // 상담 종료 시 대기열 비우기 (선택 사항)
      return;
    }
    setLoadingQueue(true);
    setError(null);
    try {
      const queueData = await getCounselorQueue();
      setQueue(queueData);
    } catch (err: any) {
      setError(err.message || '대기열 정보를 가져오는데 실패했습니다.');
      console.error("Fetch queue error:", err);
    } finally {
      setLoadingQueue(false);
    }
  }, [currentUser, isCounseling]); // currentUser, isCounseling 변경 시 fetchQueue 재생성

  // 주기적으로 대기열 업데이트 (상담 시작 상태일 때만)
  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;
    if (isCounseling && currentUser) {
      fetchQueue(); // 즉시 한번 호출
      intervalId = setInterval(fetchQueue, 10000); // 10초마다 대기열 업데이트
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId); // 컴포넌트 언마운트 또는 isCounseling 변경 시 인터벌 정리
      }
    };
  }, [isCounseling, currentUser, fetchQueue]); // isCounseling, currentUser, fetchQueue 변경 시 effect 재실행

  const handleToggleCounseling = async () => {
    const newCounselingStatus = !isCounseling;
    const newApiStatus = newCounselingStatus ? 'available' : 'busy'; // 또는 'offline' 등 백엔드 상태값에 맞게

    try {
      await updateCounselorStatus(newApiStatus); // 백엔드에 상태 변경 요청
      setIsCounseling(newCounselingStatus);
      if (!newCounselingStatus) { // 상담 종료 시
        setQueue([]); // 대기열 비우기
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || `상태를 ${newApiStatus}로 변경하는데 실패했습니다.`);
      console.error("Update status error:", err);
    }
  };

  const handleLogout = () => {
    logout();
    // navigate('/auth'); // logout 함수 내부에서 이미 처리하고 있음
  };

  // --- UI 렌더링 로직 (기존 MainPage.tsx의 구조를 최대한 활용) ---
  // 위험도에 따른 스타일 반환 함수 (문서 내용 참고 또는 새로 작성)
  const getRiskLevelStyles = (level: number): { text: string; colorClass: string; } => {
    if (level === 2) return { text: '높음', colorClass: 'bg-red-500 text-white' }; // 백엔드가 0,1,2 사용하므로 2가 높음
    if (level === 1) return { text: '중간', colorClass: 'bg-yellow-400 text-black' };
    return { text: '낮음', colorClass: 'bg-green-500 text-white' }; // 0이 낮음
  };

  // 메인페이지 우측 윗부분 마이페이지/로그아웃 (문서 내용 참고하여 JSX 작성)
  const renderHeaderActions = () => (
    <div className="absolute top-4 right-4 flex space-x-4">
      <Link to="/mypage" className="text-blue-600 hover:text-blue-800">마이페이지</Link>
      <button onClick={handleLogout} className="text-red-600 hover:text-red-800">로그아웃</button>
    </div>
  );

  // 대기열 카드 렌더링 (문서 내용 참고하여 JSX 작성)
  // "옆으로 대기열이 추가되다 화면을 넘어가도 화면 양옆에 화살표 표시" -> 이 부분은 CSS나 라이브러리(예: react-slick) 필요 가능성
  const renderQueueCards = () => (
    <div className="mt-6">
      {/* 로딩 및 에러 메시지 표시 */}
      {loadingQueue && <p>대기열 로딩 중...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loadingQueue && queue.length === 0 && !error && isCounseling && (
        <p>현재 대기 중인 내담자가 없습니다.</p>
      )}
      {!isCounseling && <p>상담을 시작하면 대기열이 표시됩니다.</p>}

      {/* 카드 스택 형식 (Tailwind CSS 예시) */}
      {/* 실제 카드 스택 UI는 기존 MainPage.tsx에 구현된 것을 사용하거나, 아래 예시를 참고하여 수정 */}
      <div className="flex overflow-x-auto space-x-4 p-4 scrollbar-thin scrollbar-thumb-blue-500 scrollbar-track-blue-100">
        {isCounseling && queue.map(item => {
          const riskStyles = getRiskLevelStyles(item.risk_level);
          return (
            <div key={item.call_id} className="min-w-[300px] bg-white shadow-lg rounded-lg border">
              <div className={`p-3 font-semibold ${riskStyles.colorClass}`}>
                자살위험도: {riskStyles.text}
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-600">전화번호: {item.phone_number}</p>
                <p className="text-sm text-gray-600">접수시간: {new Date(item.received_at).toLocaleString()}</p>
                <Link
                  to={`/report/${item.call_id}`} // 소견서 작성 페이지 라우트 경로
                  className="mt-4 block w-full text-center bg-indigo-600 text-white py-2 px-4 rounded hover:bg-indigo-700"
                >
                  소견서 작성/보기
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );


  if (!currentUser) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>; // 또는 스켈레톤 UI
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {renderHeaderActions()}
      <h1 className="text-3xl font-bold mb-2">상담사 메인 페이지</h1>
      <p className="text-gray-700 mb-6">환영합니다, {currentUser.name}님 ({currentUser.username})!</p>

      <button
        onClick={handleToggleCounseling}
        className={`px-6 py-2 rounded font-semibold text-white ${
          isCounseling ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
        }`}
      >
        {isCounseling ? '상담 종료' : '상담 시작'}
      </button>

      {renderQueueCards()}

      {/* 여기에 기존 MainPage.tsx의 다른 UI 요소들을 통합합니다. */}
    </div>
  );
};

export default MainPage;