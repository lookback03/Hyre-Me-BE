from datetime import datetime
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.database import Base, engine, DB_TYPE
from app import auth
from app.portfolio import router as portfolio_router, UPLOAD_ROOT

load_dotenv()

# models.Base.metadata.create_all(bind=engine) # 필요시 사용해 테이블을 자동 생성

app = FastAPI(
    title="hyre-me-BE",
    version="0.1.0",
    description="Hyre Me Backend API",
    openapi_tags=[
        {"name": "시스템", "description": "헬스 체크 및 서버 상태 확인 API"},
        {"name": "계정", "description": "회원가입, 로그인, 내 정보 조회/수정/탈퇴 API"},
        {"name": "포트폴리오", "description": "포트폴리오 기본 정보 및 경험 관리 API"},
        {"name": "기업", "description": "목표 기업 관리 API"},
        {"name": "자소서", "description": "자소서 생성 및 생성된 자소서 관리 API"},
    ],
)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")
app.include_router(portfolio_router)
app.include_router(auth.router)


@app.on_event("startup")
def create_local_sqlite_tables():
    if DB_TYPE == "sqlite":
        Base.metadata.create_all(bind=engine)

# CORS 설정
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", summary="헬스 체크", tags=["시스템"])
def health_check():
    """
    서버 헬스 체크
    
    서버의 정상 작동 여부를 반환합니다.
    - **status**: 보통 'ok'를 반환하면 정상 작동 중임을 의미합니다.
    """
    return {"status": "ok"}

@app.get("/current-time", summary="현재 서버 시간 조회", tags=["시스템"])
def current_time():
    """
    서버 시간 반환
    
    현재 접속한 서버의 시간을 확인합니다.
    - **current_time**: 생성된 서버 시간 (ISO 8601 포맷, 예: `2026-05-19T12:34:56.789123`)
    """
    return {"current_time": datetime.now().isoformat()}
