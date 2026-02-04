"""Sliding window chunking strategy using Unstructured elements.

This strategy creates chunks based on document elements from Unstructured,
with custom overlap implementation that respects element boundaries.
"""

from typing import Dict, List, Any
import logging

from ..base import ChunkingStrategy, TokenCounter, ChunkingError
from ..models import ProcessedDocument, DocumentChunk
from ..utils import (
    calculate_overlap_positions,
    group_elements_by_priority,
    extract_text_from_elements
)


logger = logging.getLogger(__name__)


class SlidingUnstructuredChunker(ChunkingStrategy):
    """Sliding window chunking using Unstructured document elements.

    This strategy creates overlapping chunks based on document elements,
    respecting element boundaries and document structure.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the sliding window Unstructured chunker.

        Args:
            config: Configuration dictionary containing:
                - max_elements_per_chunk: Max elements in a chunk (default: 10)
                - overlap_percentage: Overlap as percentage (default: 0.2)
                - priority_elements: Element types to prioritize
                  (default: ['Title', 'Header', 'NarrativeText'])
                - respect_boundaries: Whether to respect element boundaries
                  (default: True)
        """
        super().__init__(config)
        # Override base class inference
        self.strategy_name = "sliding_unstructured"

        self.max_elements_per_chunk = config.get('max_elements_per_chunk', 10)
        self.overlap_percentage = config.get('overlap_percentage', 0.2)
        self.priority_elements = config.get(
            'priority_elements',
            ['Title', 'Header', 'NarrativeText']
        )
        self.respect_boundaries = config.get('respect_boundaries', True)

        # Initialize token counter for metadata
        self.token_counter = TokenCounter()

        # Validate configuration
        if self.max_elements_per_chunk <= 0:
            raise ValueError("max_elements_per_chunk must be positive")

        if self.overlap_percentage < 0 or self.overlap_percentage >= 1:
            raise ValueError("overlap_percentage must be between 0 and 1")

    def chunk_document(
        self, document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk document using Unstructured elements with sliding windows.

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
            # Check if we have elements from Unstructured processing
            if not document.elements:
                logger.error(
                    f"No elements found for document {document.document_id}, "
                    f"cannot proceed with sliding Unstructured strategy"
                )
                return self._fallback_text_chunking(document)

            # Group elements by priority if enabled
            if self.respect_boundaries:
                element_groups = group_elements_by_priority(
                    document.elements, self.priority_elements
                )
                chunks = self._chunk_element_groups(element_groups, document)
            else:
                chunks = self._chunk_elements_directly(
                    document.elements, document
                )

            logger.info(
                f"Created {len(chunks)} chunks for document "
                f"{document.document_id} using sliding Unstructured strategy"
            )

            return chunks

        except Exception as e:
            logger.error(f"Sliding Unstructured chunking failed: {str(e)}")
            raise ChunkingError(
                f"Sliding Unstructured chunking failed: {str(e)}",
                strategy_name=self.strategy_name,
                document_id=document.document_id
            )

    def _chunk_element_groups(
        self,
        element_groups: List[List[Dict[str, Any]]],
        document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk elements by respecting groups and boundaries.

        Args:
            element_groups: Grouped document elements
            document: Source document

        Returns:
            List of document chunks
        """
        chunks = []
        chunk_index = 0

        for group in element_groups:
            if not group:
                continue

            # Calculate overlap positions for this group
            overlap_positions = calculate_overlap_positions(
                group, self.overlap_percentage
            )

            for start_idx, end_idx in overlap_positions:
                elements_subset = group[start_idx:end_idx]

                if not elements_subset:
                    continue

                # Extract text from elements
                chunk_text = extract_text_from_elements(elements_subset)

                if not chunk_text.strip():
                    continue

                # Create chunk
                chunk = self._create_document_chunk(
                    document, chunk_text, elements_subset, chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1

        return chunks

    def _chunk_elements_directly(
        self,
        elements: List[Dict[str, Any]],
        document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Chunk elements directly without grouping.

        Args:
            elements: Document elements
            document: Source document

        Returns:
            List of document chunks
        """
        chunks = []

        # Calculate overlap positions for all elements
        overlap_positions = calculate_overlap_positions(
            elements, self.overlap_percentage
        )

        for chunk_index, (start_idx, end_idx) in enumerate(overlap_positions):
            elements_subset = elements[start_idx:end_idx]

            if not elements_subset:
                continue

            # Extract text from elements
            chunk_text = extract_text_from_elements(elements_subset)

            if not chunk_text.strip():
                continue

            # Create chunk
            chunk = self._create_document_chunk(
                document, chunk_text, elements_subset, chunk_index
            )
            chunks.append(chunk)

        return chunks

    def _fallback_text_chunking(
        self, document: ProcessedDocument
    ) -> List[DocumentChunk]:
        """Raise an exception when elements are not available.

        Args:
            document: The document to chunk

        Returns:
            Never returns - always raises an exception

        Raises:
            ChunkingError: Always raised when no elements are available
        """
        raise ChunkingError(
            f"No Unstructured elements found for document "
            f"{document.document_id}. This strategy requires documents to be "
            f"processed with Unstructured first.",
            strategy_name=self.strategy_name,
            document_id=document.document_id
        )

    def _create_document_chunk(
        self,
        document: ProcessedDocument,
        chunk_text: str,
        elements: List[Dict[str, Any]],
        chunk_index: int
    ) -> DocumentChunk:
        """Create a DocumentChunk from elements and metadata.

        Args:
            document: Source document
            chunk_text: Text content of the chunk
            elements: List of elements in this chunk
            chunk_index: Index of this chunk in the document

        Returns:
            DocumentChunk object
        """
        # Calculate positions from elements
        start_pos = 0
        end_pos = len(chunk_text)

        if elements:
            # Try to get actual positions from element metadata
            first_element = elements[0]
            last_element = elements[-1]

            # Extract positions if available
            start_pos = first_element.get('start_position', 0)
            end_pos = last_element.get('end_position', len(chunk_text))

        # Count tokens in the chunk
        token_count = self.token_counter.count_tokens(chunk_text)

        # Extract element metadata
        element_types = [elem.get('type', 'Unknown') for elem in elements]
        element_pages = [elem.get('page_number', 1) for elem in elements]

        return DocumentChunk(
            chunk_id=self.generate_chunk_id(document.document_id, chunk_index),
            document_id=document.document_id,
            strategy_name=self.strategy_name,
            content=chunk_text,
            start_position=start_pos,
            end_position=end_pos,
            token_count=token_count,
            metadata={
                'title': document.title,
                'authors': document.authors,
                'chunk_index': chunk_index,
                'total_chunks': 0,  # Will be updated by pipeline
                'element_count': len(elements),
                'element_types': element_types,
                'page_numbers': list(set(element_pages)),
                'overlap_percentage': self.overlap_percentage,
                'strategy_config': self.get_strategy_config()
            },
            elements=elements
        )

    def get_strategy_config(self) -> Dict[str, Any]:
        """Get the current configuration for this strategy.

        Returns:
            Dictionary containing strategy configuration
        """
        return {
            'strategy_name': self.strategy_name,
            'max_elements_per_chunk': self.max_elements_per_chunk,
            'overlap_percentage': self.overlap_percentage,
            'priority_elements': self.priority_elements,
            'respect_boundaries': self.respect_boundaries
        }
