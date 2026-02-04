"""Document preprocessing module with modular extractor architecture.

This module provides comprehensive document processing capabilities
with support for multiple extraction methods and file formats.
"""

from .document_preprocessor import DocumentPreprocessor
from .base import BaseExtractor, ExtractionResult
from .extractors.pypdf_extractor import PyPDFExtractor
from .extractors.unstructured_extractor import UnstructuredExtractor
from .extractors.marker_extractor import MarkerExtractor, MarkerConfig
from .extractors.markitdown_extractor import MarkItDownExtractor
from .utils.performance_tracker import PerformanceTracker
from .utils.quality_analyzer import QualityAnalyzer
from .utils.metadata_extractor import MetadataExtractor

__all__ = [
    'DocumentPreprocessor',
    'BaseExtractor',
    'ExtractionResult',
    'PyPDFExtractor',
    'UnstructuredExtractor',
    'MarkerExtractor',
    'MarkerConfig',
    'MarkItDownExtractor',
    'PerformanceTracker',
    'QualityAnalyzer',
    'MetadataExtractor'
]
