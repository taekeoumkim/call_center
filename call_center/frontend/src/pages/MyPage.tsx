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
    axios.get('/api/myreports', {
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

  // 검색 버튼 클릭 시 호출되는 함수
  const handleSearch = () => {
    // 선택한 검색 기준에 따라 필터링
    const filtered = reports.filter(report =>
      report[searchField].includes(searchText)
    );
    setFilteredReports(filtered);
  };

  // 숫자형 위험도 값을 텍스트로 변환
  const riskToText = (risk: number) => {
    switch (risk) {
      case 1:
        return '낮음';
      case 2:
        return '중간';
      case 3:
        return '높음';
      default:
        return '알 수 없음';
    }
  };

  // 로그아웃 처리
  const handleLogout = async () => {
    try {
      // 상담사 상태를 0 (상담 종료)로 변경
      await axios.post(
        '/api/status',
        { is_active: 0 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('상태 업데이트 실패:', error);
      // 실패하더라도 로그아웃은 계속 진행
    } finally {
      // 토큰 삭제 및 로그인 페이지로 이동
      localStorage.removeItem('token');
      navigate('/');
    }
  };

  return (
    <div className="p-6">
      {/* 상단 헤더 */}
      <div className="flex justify-between mb-4">
        <div className="text-2xl font-bold">상담사 마이페이지</div>
        <div className="space-x-4">
          <button onClick={() => navigate('/main')} className="text-blue-600 hover:underline">홈</button>
          <button onClick={handleLogout} className="text-red-600 hover:underline">로그아웃</button>
        </div>
      </div>

      {/* 검색 필터 영역 */}
      <div className="flex items-center mb-4 space-x-2">
        <select
          value={searchField}
          onChange={e => setSearchField(e.target.value as 'name' | 'phone')}
          className="border p-2"
        >
          <option value="name">이름</option>
          <option value="phone">전화번호</option>
        </select>
        <input
          type="text"
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          placeholder="검색어 입력"
          className="border p-2"
        />
        <button onClick={handleSearch} className="bg-blue-500 text-white px-4 py-2 rounded">검색</button>
      </div>

      {/* 소견서 목록 테이블 */}
      <table className="w-full border">
        <thead>
          <tr className="bg-gray-100 text-center">
            <th className="p-2 border">이름</th>
            <th className="p-2 border">전화번호</th>
            <th className="p-2 border">성별</th>
            <th className="p-2 border">나이</th>
            <th className="p-2 border">자살위험도</th>
            <th className="p-2 border">작성일</th>
            <th className="p-2 border">소견서 보기</th>
          </tr>
        </thead>
        <tbody>
          {filteredReports.map(report => (
            <tr key={report.id} className="text-center">
              <td className="p-2 border">{report.name}</td>
              <td className="p-2 border">{report.phone}</td>
              <td className="p-2 border">{report.gender}</td>
              <td className="p-2 border">{report.age}</td>
              <td className="p-2 border">{riskToText(report.risk)}</td>
              <td className="p-2 border">{report.created_at}</td>
              <td className="p-2 border">
                <button
                  onClick={() => {
                    setSelectedReport(report);
                    setShowPopup(true);
                  }}
                  className="text-blue-600 underline"
                >
                  조회
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 소견서 상세보기 팝업 */}
      {showPopup && selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">소견서</h2>
            <div className="space-y-2">
              <div><strong>이름:</strong> {selectedReport.name}</div>
              <div><strong>나이:</strong> {selectedReport.age}</div>
              <div><strong>성별:</strong> {selectedReport.gender}</div>
              <div><strong>전화번호:</strong> {selectedReport.phone}</div>
              <div><strong>자살위험도:</strong> {riskToText(selectedReport.risk)}</div>
              <div><strong>작성일:</strong> {selectedReport.created_at}</div>
              <div><strong>소견 내용:</strong> {selectedReport.memo}</div>
            </div>
            <div className="text-right mt-4">
              <button onClick={() => setShowPopup(false)} className="px-4 py-2 bg-gray-300 rounded">닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyPage;