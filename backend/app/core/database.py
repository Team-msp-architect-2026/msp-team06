# HomeLens AI - DB 비동기 엔진 및 세션 설정

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 비동기 DB 엔진 생성
# development 환경에서는 SQL 쿼리 로그 출력
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
)

# 비동기 세션 팩토리
# expire_on_commit=False: 커밋 후에도 세션 데이터 유지
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# SQLAlchemy ORM 베이스 클래스
# 모든 DB 모델이 이 클래스를 상속받음
class Base(DeclarativeBase):
    pass

# DB 세션 의존성 함수
# 각 API 요청마다 세션 열고 닫아줌 (FastAPI Depends로 사용)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()