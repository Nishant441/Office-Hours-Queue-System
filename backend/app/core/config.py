"""Pydantic settings for configuration management."""
from urllib.parse import urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    DATABASE_URL_TEST: str | None = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI/ML
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.75
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Application
    PROJECT_NAME: str = "Office Hours Queue System"
    API_V1_PREFIX: str = "/api/v1"
    
    @property
    def async_database_url(self) -> str:
        """Build asyncpg-compatible URL: correct scheme, no query params.
        
        SSL is handled via connect_args in create_async_engine, not URL params.
        """
        url = self.DATABASE_URL.strip()
        
        # Normalize scheme to postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Strip ALL query parameters — asyncpg can't handle sslmode/channel_binding
        parsed = urlparse(url)
        clean = parsed._replace(query="")
        return urlunparse(clean)
    
    @property
    def ssl_connect_args(self) -> dict:
        """Return connect_args dict with SSL config if needed."""
        if "sslmode=require" in self.DATABASE_URL or "ssl" in self.DATABASE_URL:
            return {"ssl": "require"}
        return {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list, stripping trailing slashes."""
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
