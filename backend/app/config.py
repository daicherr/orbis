from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default alinhado ao docker-compose.yml (porta 5433 no host)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:admin@localhost:5433/rpg_cultivo"
    # Nunca versionar chave real; use backend/.env
    GEMINI_API_KEY: str = "YOUR_GEMINI_API_KEY"
    # Compat: ainda aceitamos GEMINI_MODEL como fallback.
    GEMINI_MODEL: str = "models/gemini-2.5-flash-preview-09-2025"

    # Modelos por tarefa (preferidos).
    GEMINI_MODEL_DEFAULT: str = "models/gemini-2.5-flash-preview-09-2025"
    GEMINI_MODEL_STORY: str = "models/gemini-3-flash-preview"
    GEMINI_MODEL_COMBAT: str = "models/gemini-3-pro-preview"
    GEMINI_MODEL_FAST: str = "models/gemini-2.5-flash-preview-09-2025"

    @property
    def async_database_url(self) -> str:
        """URL para LangGraph PostgresSaver (usa psycopg, não asyncpg)."""
        # Converte postgresql+asyncpg:// para postgresql://
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
