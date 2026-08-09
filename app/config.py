from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    chromadb_url: str = "http://chromadb:8000"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-5"
    rag_score_threshold: float = 0.65
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
