      
# 음성 데이터를 통한 감정인식 연구: 자살 위험도 예측 및 우선순위 상담 시스템

## 📢 프로젝트 소개 (Project Introduction)

본 프로젝트는 음성 데이터를 분석하여 감정을 인식하고, 이를 기반으로 자살 위험도를 예측하여 상담 우선순위를 결정하는 시스템을 개발하는 것을 목표로 합니다. 한정된 상담 자원의 효율적인 분배를 통해 더 많은 위기 상황의 내담자에게 신속한 도움을 제공하고자 합니다.

**주요 문제 인식:**
*   자살 상담 콜센터의 응대율 저조 (예: '22년 응대율 60%)
*   상담원 충족률 부족 (예: '22년 직원 충족률 29%)
*   한정된 상담 자원으로 인한 위기 내담자 상담 지연 가능성

**솔루션:**
AI 기반 음성 감정 인식 및 자살 위험도 예측 시스템을 통해, 위험도가 높은 내담자를 우선적으로 상담사와 연결하여 자살 예방 효과를 극대화합니다.

## ✨ 주요 기능 (Key Features)

1.  **음성 데이터 수집 및 STT (Speech-To-Text) 변환:**
    *   ARS를 통해 내담자의 음성 데이터 실시간 수집
    *   VAD (Voice Activity Detection)로 음성 구간 탐지
    *   Whisper AI 모델을 사용하여 음성을 텍스트로 변환
2.  **텍스트 기반 자살 위험도 분류:**
    *   KoBERT와 같은 BERT 기반 언어 모델을 활용하여 텍스트 데이터 분석
    *   AI Hub의 상담 관련 데이터셋 및 자체 라벨링 데이터를 기반으로 모델 파인튜닝
    *   자살 위험도를 3단계 (예: 높음, 낮음, 거의 없음)로 분류
3.  **상담 우선순위 대기열 시스템:**
    *   분석된 자살 위험도에 따라 상담 전화 대기열 자동 조정
    *   위험도가 높은 내담자를 우선적으로 상담사와 매칭
4.  **상담사 웹 인터페이스:**
    *   실시간 대기열 현황 시각화 (위험도별 분류)
    *   내담자 정보 및 위험도 예측 결과 확인
    *   상담 내용 기록 및 관리 기능

## 🛠️ 기술 스택 (Tech Stack)

**Frontend:**
*   React
*   TypeScript
*   React Router
*   CSS (또는 선택한 스타일링 라이브러리)
*   Axios (또는 Fetch API) - API 통신

**Backend:**
*   Python 3.12
*   Flask 3.0.x
    *   Flask-SQLAlchemy (ORM)
    *   Flask-Migrate (데이터베이스 마이그레이션)
    *   Flask-Login (사용자 인증 및 세션 관리)
    *   Flask-CORS (Cross-Origin Resource Sharing)
*   SQLite (개발용 데이터베이스)

**AI / Machine Learning:**
*   OpenAI Whisper (Speech-To-Text)
*   KoBERT (또는 유사 BERT 기반 모델) (Text Classification)
*   PyTorch (또는 TensorFlow) (모델 학습 및 추론)

**Dataset:**
*   AI Hub '복지 분야 콜센터 상담데이터' (기반 데이터)
*   자체 라벨링 데이터 (자살 위험도 분류용)

## 📂 프로젝트 구조 (Project Structure)

```
call_center/
├── backend/                    # Flask 백엔드 애플리케이션
│   ├── app/                    # 핵심 애플리케이션 로직
│   ├── instance/               # 인스턴스 특정 설정 및 파일 (예: SQLite DB 파일)
│   │   ├── app.db              # SQLite 데이터베이스 파일
│   │   └── uploads/            # 내담자 음성 녹음 파일 업로드 폴더
│   ├── migrations/             # Flask-Migrate 데이터베이스 마이그레이션 스크립트
│   ├── tests/                  # 백엔드 테스트 코드
│   ├── run.py                  # Flask 개발 서버 실행 스크립트
│   └── requirements.txt        # Python 의존성 목록
│
├── frontend/                   # React 프론트엔드 애플리케이션
│   ├── public/                 # 정적 에셋 (index.html, favicon 등)
│   ├── src/                    # React 소스 코드
│   │   ├── api/                # 백엔드 API 호출 함수 모듈
│   │   ├── components/         # 재사용 가능한 UI 컴포넌트
│   │   ├── hooks/              # (커스텀 React Hooks, 선택 사항)
│   │   ├── images/             # 이미지 파일
│   │   ├── pages/              # 페이지 단위 컴포넌트
│   │   │   ├── AuthPage.tsx
│   │   │   ├── MainPage.tsx
│   │   │   ├── MyPage.tsx
│   │   │   ├── ClientPage.tsx
│   │   │   └── ClientDetailPage.tsx
│   │   ├── services/           # 프론트엔드 서비스 로직
│   │   ├── styles/             # 전역 스타일 또는 CSS 모듈
│   │   ├── App.tsx             # 메인 애플리케이션 컴포넌트 (라우팅 설정 등)
│   │   ├── index.tsx           # React 애플리케이션 진입점
│   │   └── react-app-env.d.ts  # TypeScript 타입 정의
│   ├── .env                    # 프론트엔드 환경 변수
│   ├── package.json            # npm/yarn 의존성 및 스크립트 정의
│   └── tsconfig.json           # TypeScript 설정
│
├── .gitignore                  # Git 추적 제외 파일/폴더 목록
└── README.md                   # 프로젝트 설명 파일
```

      
## ⚙️ 설치 및 실행 방법 (Setup and Run)

**1. 사전 요구 사항 (Prerequisites):**
*   Python 3.12 이상
*   Node.js 및 npm (또는 Yarn)
*   Git

**2. Backend 설정 및 실행:**

```bash
# 1. 프로젝트 클론
git clone [프로젝트 GitHub 저장소 URL]
cd call_center_project/backend

# 2. 가상 환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 의존성 패키지 설치
pip install -r requirements.txt

# 4. 데이터베이스 마이그레이션 (최초 실행 시 또는 모델 변경 시)
# set FLASK_APP=run.py (Windows)
# export FLASK_APP=run.py (macOS/Linux)
flask db init  # 최초 1회
flask db migrate -m "initial migration"
flask db upgrade

# 5. Flask 개발 서버 실행
python run.py
# 서버는 기본적으로 http://localhost:5000 에서 실행됩니다.
```

**3. Frontend 설정 및 실행:**

```bash
# 1. 의존성 설치
cd call_center_project/frontend
npm install

# 2. React 빌드
npm run build
```

## 👨‍💻 팀원 (Team Members)

| 이름    | 역할               |
|---------|--------------------|
| 박승빈 | 팀장 / AI 모델 연구 및 개발, 데이터 셋 라벨링|
| 김태겸 | 팀원 / Front-end 개발, 데이터 셋 라벨링|
| 노선우 | 팀원 / Back-end 개발, 데이터 셋 라벨링|
| 이용재 | 팀원 / AI 모델 연구 및 개발, 데이터 셋 라벨링|

(지도교수: 정진우)
