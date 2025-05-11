import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LogoImg from '../images/Logo.jpg';

interface Client {
  id: number;
  riskLevel: number; // 1=낮음, 2=중간, 3=높음
  phone: string;
}

export default function MainPage() {
  const [inSession, setInSession] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const navigate = useNavigate();

  const fetchClients = async () => {
    if (!inSession) return;
    const res = await fetch('http://localhost:3001/clients');
    const data = await res.json();
    setClients(data);
  };

  useEffect(() => {
    if (inSession) {
      fetchClients();
    } else {
      setClients([]);
    }
  }, [inSession]);

  const getRiskColor = (level: number) => {
    return {
      1: 'bg-green-400',
      2: 'bg-yellow-400',
      3: 'bg-red-500',
    }[level];
  };

  const getRiskLabel = (level: number) => {
    return {
      1: '자살위험도 낮음',
      2: '자살위험도 중간',
      3: '자살위험도 높음',
    }[level];
  };

  const sortedClients = [...clients].sort((a, b) => b.riskLevel - a.riskLevel);

  const handleLogout = () => {
    // 로그아웃 처리 후
    navigate('/');
  };

  return (
    <div className='min-h-screen bg-gray-50 p-6'>
      {/* Header */}
      <div className='flex justify-between items-center mb-8'>
        <div className='flex items-center space-x-2'>
          <img
            src={LogoImg}
            alt='Logo'
            className='w-6 h-6 object-cover rounded-sm'
          />
          <span className='font-bold text-lg'>Call Center</span>
        </div>
        <div className='space-x-6 text-lg font-medium'>
          <button onClick={() => navigate('/mypage')}>마이페이지</button>
          <button
            onClick={handleLogout}
            className='space-x-6 text-lg font-medium'
          >
            로그아웃
          </button>
        </div>
      </div>

      <div className='mt-32'>
        {/* Start Counseling Section */}
        <div className='bg-blue-100 p-10 rounded-xl text-center mb-10 w-[800px] mx-auto'>
          <h2 className='text-4xl font-bold mb-6'>상담 시작</h2>
          <button
            onClick={() => setInSession(!inSession)}
            className={`mb-4 px-6 py-2 text-white rounded ${
              inSession
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {inSession ? '상담 종료' : '상담 시작'}
          </button>
        </div>

        {/* Clients Waiting */}
        {inSession && (
          <>
            <h3 className='text-2xl font-bold mb-4'>내담자 대기열</h3>
            <div className='relative'>
              {/* 왼쪽 화살표 */}
              <button
                onClick={() => {
                  const container = document.getElementById('client-scroll');
                  container?.scrollBy({ left: -320, behavior: 'smooth' });
                }}
                className='absolute left-0 top-1/2 transform -translate-y-1/2 z-10 bg-white p-2 shadow rounded-full'
              >
                ◀
              </button>

              {/* 스크롤 컨테이너 */}
              <div
                id='client-scroll'
                className='flex overflow-x-auto gap-4 pb-2 scroll-smooth'
              >
                {sortedClients.map((client) => (
                  <div
                    key={client.id}
                    onClick={() => navigate(`/patient/${client.id}`)}
                    className='min-w-[280px] max-w-[280px] border rounded shadow cursor-pointer flex-shrink-0'
                  >
                    <div
                      className={`h-2 ${getRiskColor(
                        client.riskLevel
                      )} rounded-t`}
                    ></div>
                    <div className='p-4'>
                      <p className='font-semibold mb-2'>
                        {getRiskLabel(client.riskLevel)}
                      </p>
                      <p className='text-sm text-gray-600'>
                        전화번호: {client.phone}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* 오른쪽 화살표 */}
              <button
                onClick={() => {
                  const container = document.getElementById('client-scroll');
                  container?.scrollBy({ left: 320, behavior: 'smooth' });
                }}
                className='absolute right-0 top-1/2 transform -translate-y-1/2 z-10 bg-white p-2 shadow rounded-full'
              >
                ▶
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
