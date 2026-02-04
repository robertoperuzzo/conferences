"""Unstructured.io extractor implementation for enhanced document processing.

This module provides PDF text extraction using Unstructured.io library
with structure awareness and element-based processing capabilities.
"""

import logging
from pathlib import Path
from typing import List

from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

# Unstructured.io for enhanced document processing
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    partition_pdf = None
    UNSTRUCTURED_AVAILABLE = False

logger = logging.getLogger(__name__)


class UnstructuredExtractor(BaseExtractor):
    """Unstructured.io-based PDF extractor.

    Uses Unstructured.io library for premium quality extraction with
    structure awareness and element-based processing capabilities.
    """

    def __init__(self):
        """Initialize Unstructured extractor."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if not UNSTRUCTURED_AVAILABLE:
            raise ImportError(
                "Unstructured.io dependencies not available. "
                "Install with: pip install 'unstructured[pdf]'"
            )

    @property
    def name(self) -> str:
        """Return the name identifier of this extractor."""
        return "unstructured"

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".pdf"]

    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return file_path.suffix.lower() in self.supported_formats

    def extract(self, file_path: Path,
                track_performance: bool = True,
                strategy: str = "auto",
                extract_images: bool = False,
                **kwargs) -> ExtractionResult:
        """Extract text and structure using Unstructured.io.

        Args:
            file_path: Path to PDF file
            track_performance: Whether to track performance metrics
            strategy: Processing strategy
                     ("auto", "fast", "ocr_only", "hi_res")
            extract_images: Whether to extract and process images
            **kwargs: Additional options

        Returns:
            ExtractionResult with elements, metadata, and flat text
        """
        self._check_file_exists(file_path)
        self._check_format_supported(file_path)

        with PerformanceTracker() as tracker:
            # Use unstructured to partition the PDF
            elements = partition_pdf(
                str(file_path),
                strategy=strategy,
                extract_images=extract_images,
                infer_table_structure=True,
                chunking_strategy=None  # We handle chunking separately
            )

            # Process elements to extract text and metadata
            processed_elements = []
            full_text_parts = []

            for i, element in enumerate(elements):
                element_dict = {
                    'type': element.category,
                    'text': str(element),
                    'element_id': f"elem_{i}",
                    'metadata': (
                        element.metadata.to_dict()
                        if hasattr(element, 'metadata') else {}
                    )
                }
                processed_elements.append(element_dict)
                full_text_parts.append(str(element))

            # Combine all text
            full_text = "\n".join(full_text_parts)

            # Calculate metrics
            pages_with_numbers = [
                elem for elem in elements
                if (hasattr(elem, 'metadata') and
                    hasattr(elem.metadata, 'page_number'))
            ]
            pages_processed = (
                len(set(
                    elem.metadata.page_number for elem in pages_with_numbers
                ))
                if pages_with_numbers else 1
            )

            performance_metrics = (
                tracker.get_metrics(len(full_text), pages_processed)
                if track_performance else {}
            )
            quality_metrics = QualityAnalyzer.analyze_text(full_text)
            quality_metrics["structure_elements"] = len(processed_elements)

            return ExtractionResult(
                text=full_text,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                method_specific_data={
                    'extraction_method': 'unstructured',
                    'processing_strategy': strategy,
                    'elements': processed_elements,
                    'element_count': len(processed_elements),
                    'extract_images': extract_images,
                    'file_format': file_path.suffix.lower()
                }
            )
