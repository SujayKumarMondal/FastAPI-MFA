from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Core
    SECRET_KEY: str = "dev-secret-key-change-me"
    DEBUG: bool = False
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Postgres / DB
    DB_ENGINE: str = "postgresql"
    DB_NAME: Optional[str] = None
    DB_SCHEMA: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None

    # Email settings (for SMTP)
    EMAIL_BACKEND: str = "smtp"
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USER: Optional[str] = None
    EMAIL_HOST_PASSWORD: Optional[str] = None
    FRONTEND_URL: Optional[str] = None

    # Encryption key for sensitive data (Fernet urlsafe base64)
    ENCRYPTION_KEY: Optional[str] = None

    # Security / auth
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_WINDOW_MINUTES: int = 15
    MIN_PASSWORD_LENGTH: int = 8

    model_config = SettingsConfigDict(
        env_file=str((Path(__file__).resolve().parent.parent / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.DB_ENGINE and self.DB_ENGINE.startswith("postgres") and self.DB_NAME and self.DB_USER:
            user = quote_plus(self.DB_USER)
            password = quote_plus(self.DB_PASSWORD or "")
            host = self.DB_HOST or "localhost"
            port = self.DB_PORT or 5432
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{self.DB_NAME}"
        return "sqlite:///./db.sqlite3"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
