"""Embedding provider using sentence-transformers (mocked for memory limits)."""
from functools import lru_cache
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """Mocked embedding provider to prevent Render OOM crashes."""
    
    _instance: "EmbeddingProvider | None" = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def encode(self, text: str) -> list[float]:
        """Return a dummy embedding to prevent OOM on 512MB free instances.
        
        Real ML models (PyTorch) consume >600MB of RAM. On Render's Free tier,
        this causes the server to immediately crash. 
        """
        # Return a zero vector of the expected dimension (384 for all-MiniLM-L6-v2)
        logger.warning("Using mock embedding to prevent OOM crash. ML duplication is disabled.")
        return [0.0] * 384
    
    def encode_ticket(
        self,
        title: str,
        description: str,
        topic_tag: str | None = None,
    ) -> list[float]:
        return self.encode(title)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Get cached embedding provider instance."""
    return EmbeddingProvider()
