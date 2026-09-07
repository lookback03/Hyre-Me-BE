# Hyre Me - Backend

취준생을 위한 AI 자기소개서 작성 서비스 'Hyre Me'의 백엔드 리포지토리입니다.
RESTful API 형태로 서비스를 제공하며, 구글의 AI (Gemini API)를 활용하여 사용자 맞춤형 자기소개서를 생성합니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: SQLAlchemy (ORM), MySQL (PyMySQL) / SQLite (로컬 개발용)
- **Authentication**: JWT (PyJWT, passlib)
- **AI**: Google GenAI (Gemini)
- **Server**: Uvicorn

## 주요 기능

- **시스템**: 서버 상태 확인 및 헬스 체크
- **계정 관리**: 회원가입, 로그인 (JWT), 사용자 정보 조회·수정 및 회원 탈퇴
- **포트폴리오 관리**: 사용자의 기본 정보, 경험 관리 및 파일 업로드
- **목표 기업 관리**: 취업 목표 기업 데이터 관리
- **자기소개서 관리**: Google GenAI를 활용한 자기소개서 자동 생성 및 생성된 자소서 관리

## 디렉토리 구조

```text
hyre-me-BE/
├── app/
│   ├── ai_service.py     # AI (GenAI) 관련 비즈니스 로직
│   ├── auth.py           # 계정 검증, 로그인 및 토큰 발급
│   ├── database.py       # 데이터베이스 연결 및 세션 관리
│   ├── main.py           # FastAPI 애플리케이션 엔트리 포인트, 라우터 및 미들웨어 설정
│   ├── models.py         # SQLAlchemy 모델 정의
│   ├── portfolio.py      # 포트폴리오 및 파일 업로드 관련 라우터
│   └── schemas.py        # Pydantic을 이용한 요청/응답 스키마
├── uploads/
│   └── resumes/          # 포트폴리오 첨부 파일 업로드 경로
├── requirements.txt      # 프로젝트 의존성 라이브러리 목록
└── README.md             # 프로젝트 소개 문서
```

## 시작하기

### 1. 가상환경 설정 및 의존성 패키지 설치

```bash
# 가상환경 생성 (선택 사항)
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS / Linux)
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

프로젝트 최상단 폴더에 `.env` 파일을 생성하고 필요한 환경변수를 추가합니다.

```env
# 허용할 CORS Origin 목록 (기본값: http://localhost:3000)
CORS_ORIGINS=http://localhost:3000

# 프로젝트 실행 환경에 맞춰 필요한 DB 연결 정보 및 로그인(JWT) 시크릿 변수, Google GenAI API 키 등을 기록합니다.
```

### 3. 서버 실행

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 다음 링크에서 Swagger UI를 통해 API 문서를 확인하고 테스트할 수 있습니다.
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc
