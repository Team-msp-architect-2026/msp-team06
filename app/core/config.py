from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "HomeLens AI"
    ENV: str = "dev"


    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "homelens_app"
    DB_PASSWORD: str = ""
    DB_NAME: str = "homelens_dev"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    AWS_REGION: str = "eu-west-3"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"

settings = Settings()
