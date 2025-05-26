// frontend/src/services/counselorService.ts
import axiosInstance, { ApiResponse } from '../api/axiosInstance'; // 경로 확인

// 대기열 항목 타입 (MainPage.tsx와 일치 또는 여기서 정의 후 export)
export interface QueueItem {
  call_id: number;
  phone_number: string;
  risk_level: number; // 0, 1, 2
  received_at: string; // ISO 문자열 형태
  status: string;
  // 필요시 백엔드 응답에 따라 다른 필드 추가
}

// 상담사 상태 변경 API
export const updateCounselorStatus = async (status: 'available' | 'busy' | 'offline'): Promise<ApiResponse> => {
  try {
    // JWT가 구현되어 있으므로 user_id는 헤더의 토큰에서 자동으로 처리됨
    const response = await axiosInstance.post<ApiResponse>('/counselor/status', { status });
    return response.data;
  } catch (error: any) {
    throw error.response?.data || { message: error.message };
  }
};

// 상담사 대기열 조회 API
export const getCounselorQueue = async (): Promise<QueueItem[]> => { // 반환 타입을 QueueItem 배열로 지정
  try {
    // JWT가 구현되어 있으므로 user_id는 헤더의 토큰에서 자동으로 처리됨
    const response = await axiosInstance.get<ApiResponse<QueueItem[]>>('/counselor/queue'); // 백엔드 응답이 data: QueueItem[] 형태라고 가정
    if (response.data.status === 'success' && Array.isArray(response.data.data)) {
      return response.data.data;
    } else if (Array.isArray(response.data)) { // 만약 응답이 바로 배열 형태라면
         return response.data as QueueItem[];
    }
    // 예상치 못한 응답 구조 처리
    console.error("Unexpected queue response structure:", response.data);
    return []; // 또는 에러 throw
  } catch (error: any) {
    console.error("Error fetching counselor queue:", error);
    throw error.response?.data || { message: error.message };
  }
};