# HomeLens AI - FastAPI 앱 진입점

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as api_router

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="HomeLens AI API",
    description="부동산 AI 분석 서비스 API",
    version="1.0.0",
)

# CORS 미들웨어 설정
# 프론트엔드(React Native)에서 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 라우터 등록 (/api/v1 prefix)
app.include_router(api_router, prefix="/api/v1")

# 루트 엔드포인트 (API 동작 확인용)
@app.get("/")
async def root():
    return {"message": "HomeLens AI API", "version": "1.0.0"}

# 헬스체크 엔드포인트 (서버 상태 확인용)
@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}