import os
try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        APP_NAME: str = "Project Atlas - Report Copilot"
        API_KEY: str = os.getenv("API_KEY", "atlas-secret-key-2026")
        DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
        DB_USER: str = os.getenv("DB_USER", "root")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        DB_NAME: str = os.getenv("DB_NAME", "atlas_db")
        READONLY_DB_USER: str = os.getenv("READONLY_DB_USER", "atlas_readonly")
        READONLY_DB_PASSWORD: str = os.getenv("READONLY_DB_PASSWORD", "AtlasReadOnly2026!")
        
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
        REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))
        
        class Config:
            env_file = ".env"
            extra = "ignore"
except ImportError:
    class Settings:
        APP_NAME: str = "Project Atlas - Report Copilot"
        API_KEY: str = os.getenv("API_KEY", "atlas-secret-key-2026")
        DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
        DB_USER: str = os.getenv("DB_USER", "root")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        DB_NAME: str = os.getenv("DB_NAME", "atlas_db")
        READONLY_DB_USER: str = os.getenv("READONLY_DB_USER", "atlas_readonly")
        READONLY_DB_PASSWORD: str = os.getenv("READONLY_DB_PASSWORD", "AtlasReadOnly2026!")
        
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
        REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))

settings = Settings()
