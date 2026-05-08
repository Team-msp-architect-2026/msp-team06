# HomeLens AI - 앱 전체 환경변수 설정

from pydantic_settings import BaseSettings

# 환경변수 설정 클래스
# .env 파일에서 자동으로 값 읽어옴
class Settings(BaseSettings):
    # 앱 설정
    app_env: str = "development"
    app_port: int = 8000
    secret_key: str = ""

    # DB 연결 설정
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "homelens_dev"
    db_user: str = "homelens"
    db_password: str = ""

    # Redis 연결 설정
    redis_host: str = "localhost"
    redis_port: int = 6379

    # 외부 API 키 설정
    kakao_api_key: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""
    molit_api_key: str = ""
    anthropic_api_key: str = ""
    juso_api_key: str = ""

    @property
    # DB 연결 문자열 자동 생성 (asyncpg 비동기 드라이버 사용)
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    # Redis 연결 문자열 자동 생성
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"

# 전역 설정 인스턴스 (다른 모듈에서 import해서 사용)
settings = Settings()