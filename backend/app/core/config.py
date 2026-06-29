# HomeLens AI - 앱 전체 환경변수 설정

import boto3
import json
import os
from pydantic_settings import BaseSettings


def _load_secret(secret_name_env: str) -> dict:
    name = os.getenv(secret_name_env, "")
    if not name:
        return {}
    try:
        client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'eu-west-3'))
        data = json.loads(client.get_secret_value(SecretId=name)['SecretString'])
        
        # password_secret_arn이 있으면 실제 패스워드를 별도 시크릿에서 읽기
        if "password_secret_arn" in data and "password" not in data:
            try:
                pw_data = json.loads(client.get_secret_value(SecretId=data["password_secret_arn"])['SecretString'])
                data["password"] = pw_data.get("password", "")
            except Exception as e:
                print(f"패스워드 시크릿 조회 실패: {e}")
        
        return data
    except Exception as e:
        print(f"Secrets Manager 조회 실패 ({secret_name_env}): {e}")
        return {}


_kakao = _load_secret("KAKAO_SECRET_NAME")
_naver = _load_secret("NAVER_SECRET_NAME")
_molit = _load_secret("MOLIT_SECRET_NAME")
_mois = _load_secret("MOIS_SECRET_NAME")
_rds = _load_secret("RDS_SECRET_NAME")
_redis = _load_secret("REDIS_SECRET_NAME")


class Settings(BaseSettings):
    # 앱 설정
    app_env: str = "development"
    app_port: int = 8000
    secret_key: str = ""

    # DB 연결 설정
    db_host: str = _rds.get("host", os.getenv("DB_HOST", "localhost"))
    db_port: int = int(_rds.get("port", os.getenv("DB_PORT", 5432)))
    db_name: str = _rds.get("dbname", os.getenv("DB_NAME", "homelens"))
    db_user: str = _rds.get("username", os.getenv("DB_USER", "homelens_admin"))
    db_password: str = _rds.get("password", os.getenv("DB_PASSWORD", ""))
    # Redis 연결 설정 — Secrets Manager > 환경변수 > 기본값 순으로 참조
    redis_host: str = _redis.get("host", os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = int(_redis.get("port", os.getenv("REDIS_PORT", 6379)))

    # 외부 API 키 설정
    kakao_api_key: str = _kakao.get("rest_api_key", os.getenv("KAKAO_API_KEY", ""))
    naver_client_id: str = _naver.get("client_id", os.getenv("NAVER_CLIENT_ID", ""))
    naver_client_secret: str = _naver.get("client_secret", os.getenv("NAVER_CLIENT_SECRET", ""))
    molit_api_key: str = _molit.get("confm_key", _molit.get("api_key", _molit.get("service_key", os.getenv("MOLIT_API_KEY", ""))))
    anthropic_api_key: str = ""
    juso_api_key: str = _mois.get("service_key", os.getenv("JUSO_API_KEY", ""))

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?ssl=require"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"

    class Config:
        env_file = ".env"


settings = Settings()