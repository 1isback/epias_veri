from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EPİAŞ Data Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/epias_db"
    
    # EPİAŞ Credentials — provide via backend/.env, never commit real values here.
    EPIAS_USERNAME: str = ""
    EPIAS_PASSWORD: str = ""
    EPIAS_AUTH_URL: str = "https://giris.epias.com.tr/cas/v1/tickets"
    EPIAS_BASE_URL: str = "https://seffaflik.epias.com.tr/electricity-service/v1"

    # Security (JWT) — override with a real secret via .env in any shared environment.
    SECRET_KEY: str = "dev-only-insecure-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()
