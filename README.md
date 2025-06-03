      
# 음성 데이터를 통한 감정인식 연구: 자살 위험도 예측 및 우선순위 상담 시스템

## 📢 프로젝트 소개 (Project Introduction)

본 프로젝트는 음성 데이터를 분석하여 감정을 인식하고, 이를 기반으로 자살 위험도를 예측하여 상담 우선순위를 결정하는 시스템을 개발하는 것을 목표로 합니다. 한정된 상담 자원의 효율적인 분배를 통해 더 많은 위기 상황의 내담자에게 신속한 도움을 제공하고자 합니다.

**주요 문제 인식:**
*   자살 상담 콜센터의 응대율 저조 ('22년 응대율 60%)
*   상담원 충족률 부족 ('22년 직원 충족률 29%)
*   한정된 상담 자원으로 인한 위기 내담자 상담 지연 가능성

**솔루션:**
AI 기반 음성 감정 인식 및 자살 위험도 예측 시스템을 통해, 위험도가 높은 내담자를 우선적으로 상담사와 연결하여 자살 예방 효과를 극대화합니다.

## ✨ 주요 기능 (Key Features)

1.  **음성 데이터 수집 및 STT (Speech-To-Text) 변환:**
    *   ARS를 통해 내담자의 음성 데이터 실시간 수집
    *   VAD (Voice Activity Detection)로 음성 구간 탐지
    *   Whisper AI 모델을 사용하여 음성을 텍스트로 변환
2.  **텍스트 기반 자살 위험도 분류:**
    *   RoBERTa 기반 언어 모델을 활용하여 텍스트 데이터 분석
    *   AI Hub의 상담 관련 데이터셋 및 자체 라벨링 데이터를 기반으로 모델 파인튜닝
    *   자살 위험도를 3단계(높음, 중간, 낮음)로 분류
3.  **상담 우선순위 대기열 시스템:**
    *   분석된 자살 위험도에 따라 상담 전화 대기열 자동 조정
    *   위험도가 높은 내담자를 우선적으로 상담사와 매칭
4.  **상담사 웹 인터페이스:**
    *   실시간 대기열 현황 시각화 (위험도별 분류)
    *   내담자 정보 및 위험도 예측 결과 확인
    *   상담 내용 기록 및 관리 기능

## 🛠️ 기술 스택 (Tech Stack)

**Frontend:**
*   React (컴포넌트 기반 UI 라이브러리)
*   TypeScript (정적 타입을 지원하는 JavaScript 확장)
*   React Router (SPA 내 라우팅 및 페이지 전환 관리)
*   Tailwind CSS (유틸리티 기반 CSS 프레임워크)
*   Axios (API 통신용 HTTP 클라이언트 라이브러리)

**Backend:**
*   Python 3.12
*   Flask 3.1.1
    *   Flask-SQLAlchemy (ORM)
    *   Flask-Migrate (데이터베이스 마이그레이션)
    *   Flask-Login (사용자 인증 및 세션 관리)
    *   Flask-CORS (Cross-Origin Resource Sharing)
*   SQLite (개발용 데이터베이스)
*   liboqs-python (Quantum-Resistant Cryptography https://github.com/open-quantum-safe/liboqs-python)

**AI / Machine Learning:**
*   OpenAI Whisper (Speech-To-Text)
*   RoBERTa (Text Classification)
*   PyTorch (모델 학습 및 추론)

**Dataset:**
*   AI Hub '복지 분야 콜센터 상담데이터' (기반 데이터)
*   자체 라벨링 데이터 (자살 위험도 분류용)

## 📂 프로젝트 구조 (Project Structure)

```
call_center/
├── backend/                    # Flask 백엔드 애플리케이션
│   ├── alembic/                # Flask-Migrate 설정
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

**2. Frontend 설정 및 실행:**

```bash
# 1. 의존성 설치
cd call_center_project/frontend
npm install

# 2. React 빌드
npm run build
```

**3. Backend 설정 및 실행:**

```bash
# 1. 프로젝트 클론
git clone https://github.com/taekeoumkim/call_center.git
cd call_center_project/backend

# 2. 가상 환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 의존성 패키지 설치

# 3-1. liboqs-python 설치: (Linux 환경 추천)

# liboqs (C 라이브러리) 빌드 및 설치에 필요한 의존성 설치
sudo apt update && sudo apt upgrade
sudo apt install build-essential cmake git libssl-dev ninja-build

# liboqs (C 라이브러리) 소스 코드 클론, 빌드 및 설치
# liboqs를 클론할 적당한 디렉토리로 이동 (예: 홈 디렉토리)
cd ~

# liboqs 저장소 클론
git clone --branch main https://github.com/open-quantum-safe/liboqs.git
cd liboqs

# 빌드 디렉토리 생성 및 이동
mkdir build && cd build

# CMake를 사용하여 빌드 파일 생성
# 기본적으로 OQS_USE_OPENSSL=ON 이지만 명시적으로 지정할 수 있습니다.
# 알고리즘을 선택적으로 빌드할 수도 있지만, 기본값으로 대부분 활성화됩니다.
# cmake .. # make를 사용하려면
cmake -GNinja .. # ninja를 사용하려면 (더 빠름)

# liboqs 빌드 (컴퓨터 코어 수에 맞게 -j 옵션 조정 가능)
# make -j$(nproc) # make를 사용하려면
ninja # ninja를 사용하려면

# liboqs 시스템에 설치 (기본적으로 /usr/local 에 설치됨)
# sudo make install # make를 사용하려면
# 또는
sudo ninja install # ninja를 사용하려면

# 공유 라이브러리 캐시 업데이트
sudo ldconfig

# 원래 프로젝트 디렉토리로 돌아가기
cd ~

# liboqs-python 설치
git clone --depth=1 https://github.com/open-quantum-safe/liboqs-python
cd liboqs-python
pip install .
    
# 나머지 의존성 설치
pip install -r requirements.txt

# 4. 데이터베이스 마이그레이션 (최초 실행 시 또는 모델 변경 시)
# set FLASK_APP=run.py (Windows)
# export FLASK_APP=run.py (macOS/Linux)
flask db init  # migrations 폴더 없을 시
flask db migrate -m "initial migration"
flask db upgrade

# 5. Flask 개발 서버 실행
python run.py
# 서버는 기본적으로 http://localhost:5000 에서 실행됩니다.
```


## 👨‍💻 팀원 (Team Members)

| 이름    | 역할               |
|---------|--------------------|
| 박승빈 | 팀장 / AI 모델 연구 및 개발, 데이터 셋 라벨링|
| 김태겸 | 팀원 / Front-end 개발, 데이터 셋 라벨링|
| 노선우 | 팀원 / Back-end 개발, 데이터 셋 라벨링|
| 이용재 | 팀원 / AI 모델 연구 및 개발, 데이터 셋 라벨링|

(지도교수: 정진우)
