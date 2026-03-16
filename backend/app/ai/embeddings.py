"""Embedding provider using sentence-transformers."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingProvider:
    """Singleton wrapper for sentence-transformers model."""
    
    _instance: "EmbeddingProvider | None" = None
    _model: SentenceTransformer | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _load_model(self) -> SentenceTransformer:
        """Lazy load the sentence-transformers model."""
        if self._model is None:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return self._model
    
    def encode(self, text: str) -> list[float]:
        """Encode text into a vector embedding.
        
        Args:
            text: Input text to encode
            
        Returns:
            List of floats representing the embedding vector (384 dimensions)
        """
        model = self._load_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def encode_ticket(
        self,
        title: str,
        description: str,
        topic_tag: str | None = None,
    ) -> list[float]:
        """Encode a ticket into a vector embedding.
        
        Args:
            title: Ticket title
            description: Ticket description
            topic_tag: Optional topic tag
            
        Returns:
            List of floats representing the embedding vector
        """
        combined = f"{title}\n\n{description}"
        if topic_tag:
            combined = f"[{topic_tag}] {combined}"
        
        return self.encode(combined)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Get cached embedding provider instance."""
    return EmbeddingProvider()
