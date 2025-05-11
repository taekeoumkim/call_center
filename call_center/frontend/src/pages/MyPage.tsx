// src/pages/MyPage.tsx
import { useEffect, useState } from 'react';

interface Record {
  id: string;
  name: string;
  age: string;
  gender: string;
  phone: string;
  riskLevel: number;
  memo: string;
}

export default function MyPage() {
  const [records, setRecords] = useState<Record[]>([]);
  const [selected, setSelected] = useState<Record | null>(null);

  useEffect(() => {
    const fetchRecords = async () => {
      const res = await fetch('/api/records');
      const data = await res.json();
      setRecords(data);
    };
    fetchRecords();
  }, []);

  const getRiskLabel = (level: number) =>
    ({ 1: '자살위험도 낮음', 2: '자살위험도 중간', 3: '자살위험도 높음' }[
      level
    ]);

  return (
    <div className='p-6 max-w-4xl mx-auto bg-gray-100 min-h-screen'>
      <h1 className='text-2xl font-bold mb-6'>상담 내역</h1>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <div className='space-y-3'>
          {records.map((record) => (
            <div
              key={record.id}
              onClick={() => setSelected(record)}
              className='p-4 bg-white rounded shadow hover:bg-blue-50 cursor-pointer'
            >
              <p className='font-semibold'>
                {record.name} ({record.age}, {record.gender})
              </p>
              <p className='text-sm text-gray-500'>
                {getRiskLabel(record.riskLevel)}
              </p>
            </div>
          ))}
        </div>

        {selected && (
          <div className='p-4 bg-white rounded shadow h-fit'>
            <h2 className='text-lg font-bold mb-4'>소견서 내용</h2>
            <p>
              <strong>이름:</strong> {selected.name}
            </p>
            <p>
              <strong>나이:</strong> {selected.age}
            </p>
            <p>
              <strong>성별:</strong> {selected.gender}
            </p>
            <p>
              <strong>전화번호:</strong> {selected.phone}
            </p>
            <p>
              <strong>자살위험도:</strong> {getRiskLabel(selected.riskLevel)}
            </p>
            <div className='mt-4'>
              <p className='font-semibold mb-1'>상담 내용 메모:</p>
              <p className='whitespace-pre-wrap'>{selected.memo}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
