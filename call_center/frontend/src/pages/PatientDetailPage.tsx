// src/pages/PatientDetailPage.tsx
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface ClientDetail {
  id: string;
  name?: string;
  age?: string;
  gender?: string;
  phone: string;
  riskLevel: number;
  memo?: string;
}

export default function PatientDetailPage() {
  const { id } = useParams();
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [form, setForm] = useState({ name: '', age: '', gender: '', memo: '' });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchClient = async () => {
      const res = await fetch('http://localhost:3001/clients/${clients.id}');
      const data = await res.json();
      setClient(data);
    };
    fetchClient();
  }, [id]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    const res = await fetch('http://localhost:3001/clients/${clients.id}', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form }),
    });

    if (res.ok) {
      alert('소견서가 저장되었습니다.');
      navigate('/main');
    } else {
      alert('저장에 실패했습니다.');
    }
  };

  const getRiskLabel = (level: number) =>
    ({ 1: '자살위험도 낮음', 2: '자살위험도 중간', 3: '자살위험도 높음' }[
      level
    ]);

  if (!client) return <div className='p-6'>로딩 중...</div>;

  return (
    <div className='max-w-xl mx-auto p-6 bg-white rounded shadow mt-8'>
      <h2 className='text-xl font-bold mb-4'>내담자 소견서 작성</h2>

      <label className='block mb-2 font-medium'>이름</label>
      <input
        type='text'
        name='name'
        value={form.name}
        onChange={handleChange}
        className='w-full p-2 border mb-4 rounded'
      />

      <label className='block mb-2 font-medium'>나이</label>
      <input
        type='text'
        name='age'
        value={form.age}
        onChange={handleChange}
        className='w-full p-2 border mb-4 rounded'
      />

      <label className='block mb-2 font-medium'>성별</label>
      <input
        type='text'
        name='gender'
        value={form.gender}
        onChange={handleChange}
        className='w-full p-2 border mb-4 rounded'
      />

      <div className='mb-4'>
        <p className='font-medium'>전화번호: {client.phone}</p>
        <p className='font-medium'>
          자살위험도: {getRiskLabel(client.riskLevel)}
        </p>
      </div>

      <label className='block mb-2 font-medium'>상담 내용 메모</label>
      <textarea
        name='memo'
        rows={5}
        value={form.memo}
        onChange={handleChange}
        className='w-full p-2 border rounded mb-6'
      />

      <button
        onClick={handleSave}
        className='px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
      >
        저장
      </button>
    </div>
  );
}
