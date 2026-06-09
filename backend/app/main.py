# HomeLens AI - FastAPI 앱 진입점

import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.config import settings
from app.api.v1 import router as api_router
from app.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    HTTP_ERRORS_TOTAL,
)

app = FastAPI(
    title="HomeLens AI API",
    description="부동산 AI 분석 서비스 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /metrics, /health 등 인프라 경로는 수집 제외
_SKIP_PATHS = {"/metrics", "/health", "/"}

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    path = request.url.path
    if path in _SKIP_PATHS:
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    labels = {
        "method": request.method,
        "endpoint": path,
        "status_code": str(response.status_code),
    }
    HTTP_REQUEST_DURATION.labels(**labels).observe(duration)
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    if response.status_code >= 400:
        HTTP_ERRORS_TOTAL.labels(**labels).inc()

    return response

app.include_router(api_router, prefix="/api/v1")

@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    return {"message": "HomeLens AI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}