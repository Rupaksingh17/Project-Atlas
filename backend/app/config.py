import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        APP_NAME: str = "Project Atlas - Report Copilot"
        API_KEY: str = os.getenv("API_KEY", "")
        OPS_API_KEY: str = os.getenv("OPS_API_KEY", "")
        DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
        DB_USER: str = os.getenv("DB_USER", "atlas_app")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        DB_NAME: str = os.getenv("DB_NAME", "atlas_db")
        READONLY_DB_USER: str = os.getenv("READONLY_DB_USER", "atlas_readonly")
        READONLY_DB_PASSWORD: str = os.getenv("READONLY_DB_PASSWORD", "")
        
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
        LLM_MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "800"))
        LLM_INPUT_USD_PER_1M_TOKENS: Optional[float] = float(os.getenv("LLM_INPUT_USD_PER_1M_TOKENS")) if os.getenv("LLM_INPUT_USD_PER_1M_TOKENS") else None
        LLM_OUTPUT_USD_PER_1M_TOKENS: Optional[float] = float(os.getenv("LLM_OUTPUT_USD_PER_1M_TOKENS")) if os.getenv("LLM_OUTPUT_USD_PER_1M_TOKENS") else None
        DATASET_LABEL: str = os.getenv("DATASET_LABEL", "production")
        REPORTS_DIR: str = os.getenv("REPORTS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "production_reports")))
        SQLITE_PATH: str = os.getenv("SQLITE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "atlas_local.db")))
        VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_data")))
        ALLOW_SQLITE_FALLBACK: bool = os.getenv("ALLOW_SQLITE_FALLBACK", "false").lower() == "true"
        
        CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
        REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))
        
        class Config:
            env_file = ".env"
            extra = "ignore"
except ImportError:
    class Settings:
        APP_NAME: str = "Project Atlas - Report Copilot"
        API_KEY: str = os.getenv("API_KEY", "")
        OPS_API_KEY: str = os.getenv("OPS_API_KEY", "")
        DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
        DB_USER: str = os.getenv("DB_USER", "atlas_app")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        DB_NAME: str = os.getenv("DB_NAME", "atlas_db")
        READONLY_DB_USER: str = os.getenv("READONLY_DB_USER", "atlas_readonly")
        READONLY_DB_PASSWORD: str = os.getenv("READONLY_DB_PASSWORD", "")
        
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
        LLM_MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "800"))
        LLM_INPUT_USD_PER_1M_TOKENS: Optional[float] = float(os.getenv("LLM_INPUT_USD_PER_1M_TOKENS")) if os.getenv("LLM_INPUT_USD_PER_1M_TOKENS") else None
        LLM_OUTPUT_USD_PER_1M_TOKENS: Optional[float] = float(os.getenv("LLM_OUTPUT_USD_PER_1M_TOKENS")) if os.getenv("LLM_OUTPUT_USD_PER_1M_TOKENS") else None
        DATASET_LABEL: str = os.getenv("DATASET_LABEL", "production")
        REPORTS_DIR: str = os.getenv("REPORTS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "production_reports")))
        SQLITE_PATH: str = os.getenv("SQLITE_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "atlas_local.db")))
        VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_data")))
        ALLOW_SQLITE_FALLBACK: bool = os.getenv("ALLOW_SQLITE_FALLBACK", "false").lower() == "true"
        
        CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
        REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))

settings = Settings()
