"""Abstract base classes and interfaces for chunking strategies.

This module defines the core interfaces that all chunking strategies must
implement to ensure consistency and interoperability.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import time
import psutil

from .models import (
    ProcessedDocument, DocumentChunk,
    ChunkingResult, ChunkingStatistics
)


logger = logging.getLogger(__name__)


class ChunkingStrategy(ABC):
    """Abstract base class for all chunking strategies.
    
    All concrete chunking implementations must inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the chunking strategy with configuration.
        
        Args:
            config: Strategy-specific configuration parameters
        """
        self.config = config
        # Extract strategy name from class name
        class_name = self.__class__.__name__.lower()
        if class_name.endswith('chunker'):
            self.strategy_name = class_name[:-7]  # Remove 'chunker' suffix
        else:
            self.strategy_name = class_name
        
    @abstractmethod
    def chunk_document(
        self, document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk a single document using this strategy.
        
        Args:
            document: The preprocessed document to chunk
            
        Returns:
            List of chunks created from the document
            
        Raises:
            ChunkingError: If chunking fails
        """
        pass
    
    @abstractmethod
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get the current configuration for this strategy.
        
        Returns:
            Dictionary containing strategy configuration
        """
        pass
    
    def process_document_with_stats(
        self,
        document: ProcessedDocument
    ) -> ChunkingResult:
        """Process a document and return result with statistics.
        
        This method wraps chunk_document with timing and memory tracking.
        
        Args:
            document: The document to process
            
        Returns:
            ChunkingResult with chunks and performance statistics
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            # Perform the chunking
            chunks = self.chunk_document(document)
            
            # Calculate statistics
            processing_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_usage = end_memory - start_memory if start_memory else None
            
            statistics = self._calculate_statistics(
                chunks, processing_time, memory_usage
            )
            
            return ChunkingResult(
                strategy_name=self.strategy_name,
                document_id=document.document_id,
                chunks=chunks,
                statistics=statistics,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Chunking failed for document {document.document_id} "
                f"with strategy {self.strategy_name}: {str(e)}"
            )
            
            return ChunkingResult(
                strategy_name=self.strategy_name,
                document_id=document.document_id,
                chunks=[],
                statistics=ChunkingStatistics(
                    total_chunks=0,
                    avg_chunk_size=0,
                    min_chunk_size=0,
                    max_chunk_size=0,
                    avg_token_count=0,
                    min_token_count=0,
                    max_token_count=0,
                    processing_time=processing_time
                ),
                success=False,
                error_message=str(e)
            )
    
    def _calculate_statistics(
        self,
        chunks: List[DocumentChunk],
        processing_time: float,
        memory_usage: Optional[float] = None
    ) -> ChunkingStatistics:
        """Calculate statistics for a list of chunks."""
        if not chunks:
            return ChunkingStatistics(
                total_chunks=0,
                avg_chunk_size=0,
                min_chunk_size=0,
                max_chunk_size=0,
                avg_token_count=0,
                min_token_count=0,
                max_token_count=0,
                processing_time=processing_time,
                memory_usage_mb=memory_usage
            )
        
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        token_counts = [chunk.token_count for chunk in chunks]
        
        return ChunkingStatistics(
            total_chunks=len(chunks),
            avg_chunk_size=sum(chunk_sizes) / len(chunks),
            min_chunk_size=min(chunk_sizes),
            max_chunk_size=max(chunk_sizes),
            avg_token_count=sum(token_counts) / len(token_counts),
            min_token_count=min(token_counts),
            max_token_count=max(token_counts),
            processing_time=processing_time,
            memory_usage_mb=memory_usage
        )
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (psutil.Error, OSError):
            return None
    
    def validate_document(self, document: ProcessedDocument) -> bool:
        """Validate that a document can be processed by this strategy.
        
        Args:
            document: The document to validate
            
        Returns:
            True if document is valid, False otherwise
        """
        if not document.full_text or not document.full_text.strip():
            logger.warning(
                f"Document {document.document_id} has no full_text content"
            )
            return False
        
        if not document.document_id:
            logger.warning("Document has no document_id")
            return False
        
        return True
    
    def generate_chunk_id(
        self, 
        document_id: str, 
        chunk_index: int
    ) -> str:
        """Generate a unique chunk ID.
        
        Args:
            document_id: The parent document ID
            chunk_index: The index of this chunk in the document
            
        Returns:
            Unique chunk identifier
        """
        return f"{document_id}_{self.strategy_name}_{chunk_index:03d}"


class ChunkingError(Exception):
    """Custom exception for chunking-related errors."""
    
    def __init__(self, message: str, strategy_name: str = None, 
                 document_id: str = None):
        self.strategy_name = strategy_name
        self.document_id = document_id
        super().__init__(message)


class TokenCounter:
    """Utility class for counting tokens in text.
    
    This class provides a consistent interface for token counting
    across all chunking strategies.
    """
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize the token counter.
        
        Args:
            encoding_name: The tokenizer encoding to use
        """
        self.encoding_name = encoding_name
        self._encoder = None
    
    @property
    def encoder(self):
        """Lazy loading of the tiktoken encoder."""
        if self._encoder is None:
            try:
                import tiktoken
                self._encoder = tiktoken.get_encoding(self.encoding_name)
            except ImportError:
                logger.warning(
                    "tiktoken not available, falling back to character-based "
                    "token estimation"
                )
                self._encoder = "fallback"
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        if self.encoder == "fallback":
            # Rough estimation: ~0.75 tokens per word
            return int(len(text.split()) * 0.75)
        
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using fallback: {e}")
            return int(len(text.split()) * 0.75)
