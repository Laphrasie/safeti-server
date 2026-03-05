from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://gasmonitor:gasmonitor_password@localhost/gasmonitor"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    GATEWAY_API_KEY: str = "gateway-api-key-change-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
