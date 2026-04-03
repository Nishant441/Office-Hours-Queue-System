"""Embedding provider using heavily optimized ONNX Runtime."""
from functools import lru_cache
import logging
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from huggingface_hub import hf_hub_download

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """Singleton wrapper for ONNX-based sentence embeddings.
    
    Uses ONNX Runtime and Rust tokenizers to eliminate the monumental 
    memory overhead of PyTorch and sentence-transformers in production.
    """
    
    _instance: "EmbeddingProvider | None" = None
    _session: ort.InferenceSession | None = None
    _tokenizer: Tokenizer | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _load_model(self) -> tuple[ort.InferenceSession, Tokenizer]:
        """Lazy load the ONNX model and tokenizer from HuggingFace cache."""
        if self._session is None or self._tokenizer is None:
            repo_id = "Xenova/all-MiniLM-L6-v2"
            logger.info("Downloading/Loading optimized ONNX models from HuggingFace...")
            
            # Download tiny quantized ONNX file and tokenizer layout
            model_path = hf_hub_download(repo_id=repo_id, filename="onnx/model_quantized.onnx")
            tokenizer_path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
            
            # Initialize Rust Fast Tokenizer
            self._tokenizer = Tokenizer.from_file(tokenizer_path)
            
            # Initialize ONNX CPU runtime
            sess_opt = ort.SessionOptions()
            sess_opt.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(model_path, sess_options=sess_opt, providers=["CPUExecutionProvider"])
            
        return self._session, self._tokenizer
        
    def encode(self, text: str) -> list[float]:
        """Encode text into a vector embedding using ONNX.
        
        Args:
            text: Input text to encode
            
        Returns:
            List of floats representing the embedding vector (384 dimensions)
        """
        session, tokenizer = self._load_model()
        
        # 1. Tokenization
        output = tokenizer.encode(text)
        input_ids = np.array([output.ids], dtype=np.int64)
        attention_mask = np.array([output.attention_mask], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids)
        
        # 2. Model Inference
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids
        }
        onnx_output = session.run(None, inputs)
        last_hidden_state = onnx_output[0]
        
        # 3. Mean Pooling Math
        input_mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(last_hidden_state * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
        embedding = sum_embeddings / sum_mask
        
        # 4. L2 Normalization Pipeline (Required for pgvector cosine sim)
        norm = np.linalg.norm(embedding, axis=1, keepdims=True)
        norm = np.clip(norm, a_min=1e-12, a_max=None)
        embedding = embedding / norm
        
        # Convert numpy array strictly to python float list for asyncpg/sqlalchemy
        return [float(x) for x in embedding[0]]
    
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
