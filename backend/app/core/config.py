"""Pydantic settings for configuration management."""
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
        """Force use of asyncpg and handle both postgres:// and postgresql:// schemes."""
        url = self.DATABASE_URL.strip()
        
        # Handle both standard schemes
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            # Ensure the driver is present even if the scheme is weird
            if "://" in url:
                url = "postgresql+asyncpg://" + url.split("://", 1)[1]
            else:
                url = "postgresql+asyncpg://" + url
                
        # asyncpg compatibility: translate/strip incompatible params
        url = url.replace("sslmode=require", "ssl=true")
        url = url.replace("channel_binding=require", "")
        
        # Clean up URL formatting
        url = url.replace("&&", "&").replace("?&", "?").rstrip("&").rstrip("?")
        
        return url

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
