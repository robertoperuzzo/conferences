"""Sliding window chunking strategy using LangChain.

This strategy uses LangChain's RecursiveCharacterTextSplitter to create
overlapping chunks with document structure awareness.
"""

from typing import Dict, List, Any
import logging

from ..base import ChunkingStrategy, TokenCounter, ChunkingError
from ..models import ProcessedDocument, DocumentChunk
from ..utils import clean_text


logger = logging.getLogger(__name__)


class SlidingLangChainChunker(ChunkingStrategy):
    """Sliding window chunking using LangChain's splitter.

    This strategy creates overlapping chunks while respecting document
    structure (paragraphs, sentences, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the sliding window LangChain chunker.

        Args:
            config: Configuration dictionary containing:
                - chunk_size: Characters per chunk (default: 1000)
                - chunk_overlap: Characters to overlap (default: 80)
                - separators: List of separators
                  (default: ['\n\n', '\n', ' ', ''])
                - keep_separator: Whether to keep separators (default: False)
                - is_separator_regex: Whether separators are regex
                  (default: False)
        """
        super().__init__(config)
        # Override base class inference
        self.strategy_name = "sliding_langchain"

        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 80)
        self.separators = config.get('separators', ["\n\n", "\n", " ", ""])
        self.keep_separator = config.get('keep_separator', False)
        self.is_separator_regex = config.get('is_separator_regex', False)

        # Initialize token counter for metadata
        self.token_counter = TokenCounter()

        # Validate configuration
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    def chunk_document(
        self, document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk document using LangChain's RecursiveCharacterTextSplitter.

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
                    f"No text content for document {document.document_id}"
                )
                return []

            # Split text using LangChain's RecursiveCharacterTextSplitter
            chunks = self._split_text_recursively(text, document.document_id)

            # Create DocumentChunk objects
            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk = self._create_document_chunk(
                    document, chunk_text, i, text
                )
                document_chunks.append(chunk)

            logger.info(
                f"Created {len(document_chunks)} chunks for document "
                f"{document.document_id} using sliding LangChain strategy"
            )

            return document_chunks

        except Exception as e:
            logger.error(f"Sliding LangChain chunking failed: {str(e)}")
            raise ChunkingError(
                f"Sliding LangChain chunking failed: {str(e)}",
                strategy_name=self.strategy_name,
                document_id=document.document_id
            )

    def _split_text_recursively(
        self, text: str, document_id: str
    ) -> List[str]:
        """Split text using LangChain's RecursiveCharacterTextSplitter.

        Args:
            text: Text to split
            document_id: Document ID for error reporting

        Returns:
            List of text chunks
        """
        try:
            # Try to use LangChain's RecursiveCharacterTextSplitter
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
                keep_separator=self.keep_separator,
                is_separator_regex=self.is_separator_regex,
                length_function=len
            )

            return splitter.split_text(text)

        except ImportError as exc:
            logger.error(
                "LangChain RecursiveCharacterTextSplitter is not available. "
                "This strategy requires LangChain to be installed."
            )
            raise ChunkingError(
                "LangChain RecursiveCharacterTextSplitter is not available. "
                "This strategy requires LangChain to be installed.",
                strategy_name=self.strategy_name,
                document_id=document_id
            ) from exc

    def _create_document_chunk(
        self,
        document: ProcessedDocument,
        chunk_text: str,
        chunk_index: int,
        original_text: str
    ) -> DocumentChunk:
        """Create a DocumentChunk from text and metadata.

        Args:
            document: Source document
            chunk_text: Text content of the chunk
            chunk_index: Index of this chunk in the document
            original_text: Original document text for position calculation

        Returns:
            DocumentChunk object
        """
        # Find actual start position in original text
        start_pos = 0
        if chunk_index > 0:
            # This is an approximation - LangChain doesn't provide exact
            # positions
            start_pos = chunk_index * (self.chunk_size - self.chunk_overlap)

        end_pos = start_pos + len(chunk_text)

        # Count tokens in the chunk
        token_count = self.token_counter.count_tokens(chunk_text)

        return DocumentChunk(
            chunk_id=self.generate_chunk_id(document.document_id, chunk_index),
            document_id=document.document_id,
            strategy_name=self.strategy_name,
            content=chunk_text,
            start_position=max(0, start_pos),
            end_position=min(end_pos, len(original_text)),
            token_count=token_count,
            metadata={
                'title': document.title,
                'authors': document.authors,
                'chunk_index': chunk_index,
                'total_chunks': 0,  # Will be updated by pipeline
                'overlap_size': self.chunk_overlap,
                'separators_used': self.separators,
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
            'chunk_overlap': self.chunk_overlap,
            'separators': self.separators,
            'keep_separator': self.keep_separator,
            'is_separator_regex': self.is_separator_regex
        }
