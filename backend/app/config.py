from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/gemrpg"
    GEMINI_API_KEY: str = "YOUR_GEMINI_API_KEY"

    class Config:
        env_file = ".env"

settings = Settings()
