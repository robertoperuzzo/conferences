"""PyPDF extractor implementation using LangChain PyPDFParser.

This module provides PDF text extraction using LangChain's PyPDFParser
wrapper around the pypdf library, offering standardized Document objects
and better integration for LangChain workflows.
"""

import logging
from pathlib import Path
from typing import List

from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

# LangChain for PDF parsing
try:
    from langchain_community.document_loaders.parsers.pdf import PyPDFParser
    from langchain_core.documents import Document
    from langchain_core.document_loaders import Blob
    LANGCHAIN_AVAILABLE = True
except ImportError:
    PyPDFParser = None
    Document = None
    Blob = None
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PyPDFExtractor(BaseExtractor):
    """LangChain PyPDF-based PDF extractor.

    Uses LangChain's PyPDFParser which provides a standardized interface
    around the pypdf library with Document objects and better integration
    for future LangChain workflows.
    """

    def __init__(self):
        """Initialize PyPDF extractor."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain dependencies not available for PyPDF extraction. "
                "Install with: pip install langchain langchain-community"
            )

    @property
    def name(self) -> str:
        """Return the name identifier of this extractor."""
        return "pypdf"

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".pdf"]

    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return file_path.suffix.lower() in self.supported_formats

    def extract(self, file_path: Path,
                track_performance: bool = True, **kwargs) -> ExtractionResult:
        """Extract text using LangChain PyPDF parser.

        Args:
            file_path: Path to PDF file
            track_performance: Whether to track performance metrics
            **kwargs: Additional options (unused for this extractor)

        Returns:
            ExtractionResult containing extracted text and metrics
        """
        self._check_file_exists(file_path)
        self._check_format_supported(file_path)

        with PerformanceTracker() as tracker:
            parser = PyPDFParser()

            # Create a Blob from the PDF file
            blob = Blob.from_path(file_path)

            # Parse PDF into LangChain Documents
            documents = parser.parse(blob)

            # Extract text from Document objects
            text_parts = [doc.page_content for doc in documents]
            full_text = "\n".join(text_parts)
            pages_processed = len(documents)

            # Calculate metrics
            performance_metrics = (
                tracker.get_metrics(len(full_text), pages_processed)
                if track_performance else {}
            )
            quality_metrics = QualityAnalyzer.analyze_text(full_text)

            return ExtractionResult(
                text=full_text,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                method_specific_data={
                    "extraction_method": "pypdf",
                    "implementation": "langchain_pypdf_parser",
                    "pages_processed": pages_processed,
                    "document_objects": len(documents),
                    "file_format": file_path.suffix.lower()
                }
            )
