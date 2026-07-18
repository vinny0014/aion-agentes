"""AION AGENTES — Configurações centrais (carregadas de .env)."""
from pydantic_settings import BaseSettings


SITE_URL_DEFAULT = "https://aion-news-os.vercel.app"


class Settings(BaseSettings):
    APP_NAME: str = "AION AGENTES"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./aion.db"  # trocar por PostgreSQL em produção
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    # Fonte unica de verdade para toda saida dependente de URL
    # (robots, sitemaps, RSS, canonical, OG, JSON-LD, posts sociais).
    SITE_URL: str = SITE_URL_DEFAULT
    # Chaves de provedores de IA — deixar vazio até configurar
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
settings.SITE_URL = (settings.SITE_URL or SITE_URL_DEFAULT).rstrip("/")


def site_url() -> str:
    """URL publica oficial do portal — ponto unico de configuracao."""
    return settings.SITE_URL
