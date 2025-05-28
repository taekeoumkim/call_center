// 마이페이지
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// 소견서(Report) 인터페이스 정의
interface Report {
  id: number;
  name: string;
  age: number;
  gender: string;
  phone: string;
  risk: number;
  memo: string;
  created_at: string;
}

const MyPage: React.FC = () => {
  // 전체 소견서 리스트
  const [reports, setReports] = useState<Report[]>([]);
  // 검색 후 필터링된 소견서 리스트
  const [filteredReports, setFilteredReports] = useState<Report[]>([]);
  // 검색 조건(이름/전화번호)
  const [searchField, setSearchField] = useState<'name' | 'phone'>('name');
  // 검색어
  const [searchText, setSearchText] = useState('');
  // 팝업으로 열람할 선택된 소견서
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  // 팝업 표시 여부
  const [showPopup, setShowPopup] = useState(false);
  // 페이지 이동을 위한 훅
  const navigate = useNavigate();
  // 로컬 스토리지에서 JWT 토큰 조회
  const token = localStorage.getItem('token');

  // 페이지 마운트 시 소견서 불러오기
  useEffect(() => {
    if (!token) {
      // 토큰이 없으면 로그인 페이지로 리디렉션
      navigate('/');
      return;
    }

    // 토큰이 있으면 소견서 목록 API 호출
    axios.get('/api/counselor/myreports', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        // 성공 시 전체 및 필터용 상태 모두 저장
        setReports(res.data.reports);
        setFilteredReports(res.data.reports);
      })
      .catch(() => {
        alert('소견서 정보를 불러오는 데 실패했습니다.');
        navigate('/');
      });
  }, [navigate, token]);

  // 검색 시 호출되는 함수
  const handleSearch = () => {
    const filtered = reports.filter(report => {
      const targetValue = report[searchField];
      if (searchField === 'phone') {
        // 하이픈 제거 후 비교
        const normalizedTarget = targetValue.replace(/-/g, '');
        const normalizedSearch = searchText.replace(/-/g, '');
        return normalizedTarget.includes(normalizedSearch);
      }
      // 이름 검색은 그대로
      return targetValue.includes(searchText);
    });
    setFilteredReports(filtered);
  };

  // 숫자형 위험도 값을 텍스트로 변환
  const riskToText = (risk: number) => {
    switch (risk) {
      case 0:
        return '낮음';
      case 1:
        return '중간';
      case 2:
        return '높음';
      default:
        return '알 수 없음';
    }
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center font-sans px-4 py-8">
      {/* 헤더 */}
      <header className="w-full max-w-5xl bg-white rounded-3xl shadow-md px-6 py-4 mb-8 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-blue-800 tracking-tight">상담 내역</h1>
        <div className="space-x-4 text-sm">
          <button onClick={() => navigate('/main')} className="text-blue-600 hover:underline">
            홈
          </button>
          <button onClick={handleLogout} className="text-red-600 hover:underline">
            로그아웃
          </button>
        </div>
      </header>
  
      {/* 메인 카드 */}
      <main className="w-full max-w-5xl bg-white p-8 rounded-3xl shadow-xl transition-all duration-300 hover:shadow-2xl">
        {/* 검색 필터 */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 mb-6 space-y-3 sm:space-y-0">
          <select
            value={searchField}
            onChange={e => setSearchField(e.target.value as 'name' | 'phone')}
            className="border border-blue-200 px-4 py-2 rounded-xl text-sm focus:ring-2 focus:ring-blue-400"
          >
            <option value="name">이름</option>
            <option value="phone">전화번호</option>
          </select>
          <input
            type="text"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
            placeholder="검색어 입력"
            className="border border-blue-200 px-4 py-2 rounded-xl text-sm focus:ring-2 focus:ring-blue-400 flex-1"
          />
          <button
            onClick={handleSearch}
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-xl shadow-md text-sm"
          >
            검색
          </button>
        </div>
  
        {/* 테이블 */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm border rounded-xl overflow-hidden">
            <thead>
              <tr className="bg-blue-100 text-blue-800 text-center">
                <th className="p-2">이름</th>
                <th className="p-2">전화번호</th>
                <th className="p-2">성별</th>
                <th className="p-2">나이</th>
                <th className="p-2">자살위험도</th>
                <th className="p-2">작성일</th>
                <th className="p-2">소견서</th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.map(report => (
                <tr key={report.id} className="text-center border-t hover:bg-blue-50">
                  <td className="p-2">{report.name}</td>
                  <td className="p-2">{report.phone}</td>
                  <td className="p-2">{report.gender}</td>
                  <td className="p-2">{report.age}</td>
                  <td className="p-2">{riskToText(report.risk)}</td>
                  <td className="p-2">{report.created_at}</td>
                  <td className="p-2">
                    <button
                      onClick={() => {
                        setSelectedReport(report);
                        setShowPopup(true);
                      }}
                      className="text-blue-600 underline hover:text-blue-800"
                    >
                      조회
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
  
      {/* 팝업 */}
      {showPopup && selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-3xl shadow-xl w-full max-w-md">
            <h2 className="text-xl font-bold text-blue-800 mb-4 text-center">소견서 상세</h2>
            <div className="space-y-2 text-sm text-gray-700">
              <div><strong>이름:</strong> {selectedReport.name}</div>
              <div><strong>나이:</strong> {selectedReport.age}</div>
              <div><strong>성별:</strong> {selectedReport.gender}</div>
              <div><strong>전화번호:</strong> {selectedReport.phone}</div>
              <div><strong>자살위험도:</strong> {riskToText(selectedReport.risk)}</div>
              <div><strong>작성일:</strong> {selectedReport.created_at}</div>
              <div><strong>소견 내용:</strong> {selectedReport.memo}</div>
            </div>
            <div className="text-center mt-6">
              <button
                onClick={() => setShowPopup(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded-xl shadow-sm transition"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
  
      <footer className="text-xs text-gray-400 mt-8 mb-4 text-center">
        © 2025 Call Center. All rights reserved.
      </footer>
    </div>
  );
};

export default MyPage;