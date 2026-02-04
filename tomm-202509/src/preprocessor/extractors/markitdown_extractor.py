"""MarkItDown extractor implementation for multi-format document processing.

This module provides universal document text extraction using Microsoft's
MarkItDown library with support for various file formats and LLM-optimized
Markdown output.
"""

import logging
from pathlib import Path
from typing import List, Optional, Any

from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

# MarkItDown for multi-format document processing
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MarkItDown = None
    MARKITDOWN_AVAILABLE = False

logger = logging.getLogger(__name__)


class MarkItDownExtractor(BaseExtractor):
    """MarkItDown-based multi-format document extractor.

    Uses Microsoft's MarkItDown library for converting various document
    formats to clean, LLM-optimized Markdown. Supports Office documents,
    images, audio, HTML, and more.
    """

    def __init__(self,
                 enable_plugins: bool = False,
                 llm_client: Optional[Any] = None,
                 llm_model: Optional[str] = None,
                 docintel_endpoint: Optional[str] = None):
        """Initialize MarkItDown extractor with optional enhancements.

        Args:
            enable_plugins: Whether to enable third-party plugins
            llm_client: Optional LLM client for enhanced processing
            llm_model: LLM model name (e.g., 'gpt-4o')
            docintel_endpoint: Azure Document Intelligence endpoint
        """
        self._check_dependencies()
        self.enable_plugins = enable_plugins
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.docintel_endpoint = docintel_endpoint

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if not MARKITDOWN_AVAILABLE:
            raise ImportError(
                "MarkItDown dependencies not available. "
                "Install with: pip install 'markitdown[all]'"
            )

    @property
    def name(self) -> str:
        """Return the name identifier of this extractor."""
        return "markitdown"

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions."""
        return [
            # Office documents
            ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
            # Images
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
            # Audio
            ".mp3", ".wav", ".m4a",
            # Web and structured data
            ".html", ".htm", ".csv", ".json", ".xml",
            # E-books and archives
            ".epub", ".zip",
            # Text formats
            ".txt", ".md", ".rtf"
        ]

    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return file_path.suffix.lower() in self.supported_formats

    def extract(self, file_path: Path,
                track_performance: bool = True,
                enable_llm: bool = False,
                **kwargs) -> ExtractionResult:
        """Extract text using MarkItDown with performance tracking.

        Args:
            file_path: Path to file to extract text from
            track_performance: Whether to track performance metrics
            enable_llm: Whether to enable LLM enhancement
                       for images/presentations
            **kwargs: Additional options

        Returns:
            ExtractionResult containing extracted text and metrics
        """
        self._check_file_exists(file_path)
        self._check_format_supported(file_path)

        with PerformanceTracker() as tracker:
            # Configure MarkItDown with optional enhancements
            md_config = {
                'enable_plugins': self.enable_plugins,
            }

            if enable_llm and self.llm_client:
                md_config.update({
                    'llm_client': self.llm_client,
                    'llm_model': self.llm_model or 'gpt-4o'
                })

            if self.docintel_endpoint:
                md_config['docintel_endpoint'] = self.docintel_endpoint

            md = MarkItDown(**md_config)

            # Convert document to markdown
            result = md.convert(str(file_path))
            markdown_text = result.text_content

            # Calculate metrics
            performance_metrics = (
                tracker.get_metrics(len(markdown_text), 1)
                if track_performance else {}
            )
            quality_metrics = QualityAnalyzer.analyze_text(markdown_text)

            return ExtractionResult(
                text=markdown_text,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                method_specific_data={
                    "extraction_method": "markitdown",
                    "file_format": file_path.suffix.lower(),
                    "supports_format": True,
                    "output_format": "markdown",
                    "llm_enhanced": enable_llm and self.llm_client is not None,
                    "plugins_enabled": self.enable_plugins,
                    "azure_docintel": self.docintel_endpoint is not None,
                    "file_size_bytes": file_path.stat().st_size,
                    "markitdown_version": self._get_markitdown_version()
                }
            )

    def _get_markitdown_version(self) -> str:
        """Get MarkItDown library version."""
        try:
            import markitdown
            return getattr(markitdown, '__version__', 'unknown')
        except (ImportError, AttributeError):
            return 'unknown'
