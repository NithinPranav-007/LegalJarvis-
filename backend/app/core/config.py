"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Needhi"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://legaljarvis:legaljarvis_dev_pass@localhost:5432/legaljarvis"
    )
    SYNC_DATABASE_URL: str = (
        "postgresql://legaljarvis:legaljarvis_dev_pass@localhost:5432/legaljarvis"
    )

    # Auth & Security
    JWT_SECRET: str = "dev_secret_change_in_production_893475982347598234"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM Gateway
    LLM_PROVIDER: str = "fake"  # 'openai', 'anthropic', 'gemini', 'local', 'fake'
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""
    LLM_TEMPERATURE: float = 0.0

    # Retrieval & Embeddings
    EMBED_MODEL: str = "BAAI/bge-m3"
    RERANK_MODEL: str = "BAAI/bge-reranker-base"
    EMBED_DIMENSION: int = 1024

    # Limits & Ingestion
    MAX_DOWNLOAD_GB: float = 5.0
    UPLOAD_RETENTION_DAYS: int = 30
    MAX_UPLOAD_SIZE_MB: int = 20
    RATE_LIMIT_PER_HOUR: int = 30

    # Legal Disclaimer (Mandatory per PRD FR-17 / D12)
    LEGAL_DISCLAIMER: str = (
        "Needhi provides automated legal research and informational analysis based on public "
        "court judgments and statutory texts. It does not provide legal advice or create an attorney-client "
        "relationship. Always verify citations and consult a qualified advocate for legal representation."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
