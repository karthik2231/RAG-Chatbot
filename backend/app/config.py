from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VectorDoc API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql://raguser:ragpassword@localhost:5432/rag_chatbot"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    ollama_timeout_seconds: float = 180.0
    ollama_keep_alive: str = "30m"
    ollama_num_predict: int = 160
    ollama_num_ctx: int = 1536

    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    upload_dir: Path = Path("uploads")
    faiss_index_dir: Path = Path("faiss_indexes")

    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    max_upload_size_mb: int = 25

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
