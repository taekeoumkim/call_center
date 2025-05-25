// 소견서 작성페이지
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// 기본 Axios 설정: 백엔드 API 주소
axios.defaults.baseURL = 'http://localhost:5000';

// 내담자 정보 인터페이스
interface Client {
  id: number;
  phone: string;
  risk: 0 | 1 | 2;  // 자살 위험도 (0: 낮음, 1: 중간, 2: 높음)
}

// JWT 토큰 디코딩 결과 인터페이스
interface DecodedToken {
  name: string;
  exp: number;
}

// 입력 폼 상태 인터페이스
interface FormState {
  name: string;
  age: string;
  gender: string;
  note: string;
}

// 자살 위험도에 따른 색상 스타일
const riskColors = {
  0: 'bg-green-500',
  1: 'bg-yellow-400',
  2: 'bg-red-500',
};

// 자살 위험도 라벨
const riskLabels = {
  0: '자살위험도 낮음',
  1: '자살위험도 중간',
  2: '자살위험도 높음',
};

const ClientDetailPage = () => {
  // URL 파라미터에서 내담자 ID 추출
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // 로컬 스토리지에서 JWT 토큰 가져오기
  const token = localStorage.getItem('token');

  // 내담자 정보 상태
  const [client, setClient] = useState<Client | null>(null);

  // 입력 폼 상태
  const [form, setForm] = useState<FormState>({
    name: '',
    age: '',
    gender: '',
    note: '',
  });

  // 로그인한 상담사의 이름
  const [counselorName, setCounselorName] = useState('');

  // 컴포넌트 마운트 시 실행
  useEffect(() => {
    // 토큰이 없으면 로그인 페이지로 이동
    if (!token) {
      navigate('/');
      return;
    }

    // 토큰을 디코딩해서 상담사 이름 추출
    try {
      const decoded = jwtDecode<DecodedToken>(token);
      setCounselorName(decoded.name);
    } catch (err) {
      console.error('토큰 디코딩 실패:', err);
      navigate('/');
    }

    // 내담자 정보 요청
    const fetchClient = async () => {
      try {
        const res = await axios.get(`/api/client/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setClient(res.data);  // 내담자 정보 저장
      } catch (err) {
        console.error('내담자 정보 불러오기 실패:', err);
      }
    };

    fetchClient();  // 비동기 함수 호출
  }, [id, navigate, token]);

  // 입력값 변경 핸들러
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));  // 상태 업데이트
  };

  // 소견서 저장 및 대기열 삭제 후 메인으로 이동
  const handleSave = async () => {
    if (!client) return;

    try {
      // 소견서 작성 요청
      await axios.post(
        '/api/report',
        {
          client_id: client.id,
          name: form.name,
          age: parseInt(form.age),
          gender: form.gender,
          memo: form.note,
          phone: client.phone,
          risk: client.risk,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 대기열에서 해당 내담자 삭제
      await axios.post(
        '/api/queue/delete',
        { client_id: client.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 메인 페이지로 이동
      navigate('/main');
    } catch (err) {
      console.error('저장 실패:', err);
    }
  };

  // 로딩 중 표시
  if (!client) return <div className="p-6">로딩 중...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center font-sans px-4 py-8">
      <main className="w-full max-w-xl bg-white p-8 rounded-3xl shadow-xl transition-all duration-300 hover:shadow-2xl">
        <h2 className="text-2xl font-bold text-center text-blue-800 mb-6 tracking-tight">
          {counselorName} 상담사님 - 내담자 소견서 작성
        </h2>

        {/* 소견서 작성 폼 */}
        <div className="space-y-6">
          {/* 이름 입력 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">이름</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
              placeholder="내담자 이름 입력"
            />
          </div>

          {/* 나이 입력 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">나이</label>
            <input
              type="number"
              name="age"
              value={form.age}
              onChange={handleChange}
              className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm"
              placeholder="내담자 나이 입력"
            />
          </div>

          {/* 성별 선택 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">성별</label>
            <div className="flex space-x-4">
              {['남성', '여성'].map((g) => (
                <label key={g} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="gender"
                    value={g}
                    checked={form.gender === g}
                    onChange={handleChange}
                    className="accent-blue-600"
                  />
                  <span className="text-sm text-gray-700">{g}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 전화번호 표시 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">전화번호</label>
            <div className="px-4 py-3 border border-blue-100 rounded-xl bg-gray-100 text-sm text-gray-700">
              {client.phone}
            </div>
          </div>

          {/* 자살위험도 표시 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">자살위험도</label>
            <div className="flex items-center space-x-3 px-4 py-3 border border-blue-100 rounded-xl bg-gray-100">
              <span className={`w-4 h-4 rounded-full ${riskColors[client.risk]}`} />
              <span className="text-sm text-gray-700">{riskLabels[client.risk]}</span>
            </div>
          </div>

          {/* 상담 메모 */}
          <div>
            <label className="block text-sm font-semibold text-blue-800 mb-1">상담 메모</label>
            <textarea
              name="note"
              value={form.note}
              onChange={handleChange}
              className="w-full border border-blue-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 placeholder-gray-400 text-sm h-32 resize-none"
              placeholder="상담 중 느낀 점이나 주요 내용을 작성해주세요"
            />
          </div>

          {/* 저장 & 취소 버튼 */}
          <div className="pt-4 space-y-3">
            <button
              onClick={handleSave}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl shadow-md transition-all duration-200 text-sm"
            >
              저장
            </button>
            <button
              onClick={() => navigate(-1)}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-3 rounded-xl shadow-sm transition-all duration-200 text-sm"
            >
              취소
            </button>
          </div>
        </div>
      </main>

      <footer className="text-xs text-gray-400 mt-8 mb-4">
        © 2025 Call Center. All rights reserved.
      </footer>
    </div>
  );

};

export default ClientDetailPage;