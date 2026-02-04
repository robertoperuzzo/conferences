"""
Embedding generator for document chunks.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text using sentence transformers."""
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize the embedding generator."""
        self.model_name = model_name
        self.model = None
        
    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully")
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for embedding generation. "
                    "Install it with: pip install sentence-transformers"
                ) from e
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.generate_embeddings([text])[0]
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        
        self._load_model()
        
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.model.encode(texts)
            
            # Convert numpy arrays to lists
            if isinstance(embeddings, np.ndarray):
                return embeddings.tolist()
            
            return [emb.tolist() if isinstance(emb, np.ndarray) else emb 
                   for emb in embeddings]
                   
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def create_embedding_text(self, document_title: str, chunk_content: str) -> str:
        """Create text for embedding by combining title and content."""
        if document_title:
            return f"{document_title}. {chunk_content}"
        return chunk_content
    
    def get_embedding_dimensions(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        self._load_model()
        # Generate a test embedding to get dimensions
        test_embedding = self.generate_embedding("test")
        return len(test_embedding)
