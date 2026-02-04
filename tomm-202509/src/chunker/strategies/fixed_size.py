"""Fixed-size chunking strategy implementation.

This strategy splits documents into chunks of a fixed token count,
providing a simple baseline for comparison with other strategies.
"""

from typing import Dict, List, Any
import logging

from ..base import ChunkingStrategy, TokenCounter, ChunkingError
from ..models import ProcessedDocument, DocumentChunk
from ..utils import clean_text


logger = logging.getLogger(__name__)


class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size token-based chunking strategy.

    This strategy splits text into chunks with a fixed number of tokens,
    with optional overlap between chunks.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the fixed-size chunker.

        Args:
            config: Configuration dictionary containing:
                - chunk_size: Number of tokens per chunk (default: 1000)
                - chars_per_token: Character to token ratio (default: 4.0)
        """
        super().__init__(config)
        self.strategy_name = "fixed_size"  # Override base class inference

        self.chunk_size = config.get('chunk_size', 1000)
        self.chars_per_token = config.get('chars_per_token', 4.0)

        # Convert token sizes to character sizes for fast processing
        self.chunk_size_chars = int(self.chunk_size * self.chars_per_token)

        # Initialize token counter for final token counting only
        self.token_counter = TokenCounter('cl100k_base')

        # Validate configuration
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

    def chunk_document(
        self, document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk document using fixed-size token-based splitting.

        Args:
            document: The document to chunk

        Returns:
            List of document chunks

        Raises:
            ChunkingError: If chunking fails
        """
        if not self.validate_document(document):
            raise ChunkingError(
                f"Document validation failed for {document.document_id}",
                strategy_name=self.strategy_name,
                document_id=document.document_id
            )

        try:
            # Clean the text
            text = clean_text(document.full_text)

            if not text:
                logger.warning(
                    "No text content for document %s", document.document_id
                )
                return []

            # Split text using character-based estimation (4:1 ratio)
            chunks = self._split_text_by_chars(text)

            # Create DocumentChunk objects
            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk = self._create_document_chunk(
                    document, chunk_text, i
                )
                document_chunks.append(chunk)

            logger.info(
                "Created %d chunks for document %s using fixed-size strategy",
                len(document_chunks), document.document_id
            )

            return document_chunks

        except Exception as e:
            logger.error("Fixed-size chunking failed: %s", str(e))
            raise ChunkingError(
                f"Fixed-size chunking failed: {str(e)}",
                strategy_name=self.strategy_name,
                document_id=document.document_id
            ) from e

    def _split_text_by_chars(self, text: str) -> List[str]:
        """Split text into chunks using character-based estimation.

        Uses the 4:1 character-to-token ratio for fast processing without
        tokenizer overhead.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size_chars:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position for this chunk
            end = min(start + self.chunk_size_chars, len(text))

            # Try to break at word boundaries if we're not at the end
            if end < len(text):
                # Look backwards for a good break point
                break_chars = {' ', '\n', '\r', '\t', '.', '!', '?', ';', ','}
                search_start = max(start, end - 100)  # Don't search too far

                for i in range(end - 1, search_start - 1, -1):
                    if text[i] in break_chars:
                        end = i + 1
                        break

            # Extract chunk text
            chunk_text = text[start:end].strip()

            if chunk_text:  # Only add non-empty chunks
                chunks.append(chunk_text)

            # Calculate next start position (no overlap for fixed-size)
            if end >= len(text):
                break

            start = end

        return chunks

    def _split_text_by_tokens_direct(self, text: str) -> List[str]:
        """Split text into fixed-size token chunks using character estimation.

        This method uses the 4:1 character-to-token ratio for consistent
        chunk sizes without tokenizer overhead.

        Args:
            text: Text to split

        Returns:
            List of text chunks with consistent estimated token counts
        """
        return self._split_text_by_chars(text)

    def _create_document_chunk(
        self,
        document: ProcessedDocument,
        chunk_text: str,
        chunk_index: int
    ) -> DocumentChunk:
        """Create a DocumentChunk from text and metadata.

        Args:
            document: Source document
            chunk_text: Text content of the chunk
            chunk_index: Index of this chunk in the document

        Returns:
            DocumentChunk object
        """
        # Calculate positions (approximate for character-based splitting)
        start_pos = chunk_index * self.chunk_size
        end_pos = start_pos + len(chunk_text)

        # Estimate token count using character ratio
        token_count = int(len(chunk_text) / self.chars_per_token)

        return DocumentChunk(
            chunk_id=self.generate_chunk_id(document.document_id, chunk_index),
            document_id=document.document_id,
            strategy_name=self.strategy_name,
            content=chunk_text,
            start_position=max(0, start_pos),
            end_position=end_pos,
            token_count=token_count,
            metadata={
                'title': document.title,
                'authors': document.authors,
                'chunk_index': chunk_index,
                'total_chunks': 0,  # Will be updated by pipeline
                'strategy_config': self.get_strategy_config()
            }
        )

    def get_strategy_config(self) -> Dict[str, Any]:
        """Get the current configuration for this strategy.

        Returns:
            Dictionary containing strategy configuration
        """
        return {
            'strategy_name': self.strategy_name,
            'chunk_size': self.chunk_size,
            'chars_per_token': self.chars_per_token
        }
