"""AION AI NEWS OS — central settings loaded from environment variables."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


SITE_URL_DEFAULT = "https://aion-news-os.vercel.app"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "AION AI NEWS OS"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./aion.db"  # trocar por PostgreSQL em produção
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    ADMIN_SETUP_TOKEN: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    # Chaves de provedores de IA — deixar vazio até configurar
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    # Single source of truth for robots, sitemaps, RSS, canonical and social URLs.
    SITE_URL: str = SITE_URL_DEFAULT
    PUBLIC_API_URL: str = "https://aion-news-api.onrender.com"
    UPLOAD_DIR: str = "./uploads"
    IMAGE_PROVIDER: str = "pollinations"

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENV.lower() != "production":
            return self
        if self.SECRET_KEY == "CHANGE_ME_IN_ENV" or len(self.SECRET_KEY) < 32:
            raise ValueError("Production SECRET_KEY must be a generated value of at least 32 characters")
        if len(self.ADMIN_SETUP_TOKEN) < 16:
            raise ValueError("Production ADMIN_SETUP_TOKEN must be a generated value of at least 16 characters")
        if "*" in self.CORS_ORIGINS:
            raise ValueError("Production CORS_ORIGINS cannot contain a wildcard")
        return self

settings = Settings()
settings.SITE_URL = (settings.SITE_URL or SITE_URL_DEFAULT).rstrip("/")


def site_url() -> str:
    """Return the normalized canonical public URL."""
    return settings.SITE_URL
