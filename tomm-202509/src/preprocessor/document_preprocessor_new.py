"""Refactored document preprocessor with modular extractor architecture.

This module provides the main DocumentPreprocessor class that orchestrates
different document extractors through a clean, pluggable architecture.
"""

import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from .base import BaseExtractor, ExtractionResult
from .extractors.pypdf_extractor import PyPDFExtractor
from .extractors.unstructured_extractor import UnstructuredExtractor
from .extractors.marker_extractor import MarkerExtractor
from .extractors.markitdown_extractor import MarkItDownExtractor
from .utils.metadata_extractor import MetadataExtractor
from ..config import DATA_RAW_PATH, DATA_PROCESSED_PATH, LOGS_PATH

# Setup logging
logger = logging.getLogger(__name__)


class DocumentPreprocessor:
    """Main document preprocessor with pluggable extractors.

    This class provides a unified interface for document text extraction
    using various specialized extractors. It supports automatic format
    detection, lazy loading of extractors, and comprehensive error handling.
    """

    # Supported extraction methods
    SUPPORTED_METHODS = ['pypdf', 'unstructured', 'marker', 'markitdown']

    def __init__(self, raw_path: Optional[Path] = None,
                 processed_path: Optional[Path] = None):
        """Initialize the preprocessor with necessary paths.

        Args:
            raw_path: Path to raw documents (defaults to DATA_RAW_PATH)
            processed_path: Path for processed outputs
                (defaults to DATA_PROCESSED_PATH)
        """
        self.raw_path = raw_path or DATA_RAW_PATH
        self.processed_path = processed_path or DATA_PROCESSED_PATH
        self.logs_path = LOGS_PATH

        # Create directories if they don't exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Initialize available extractors with lazy loading
        self._available_extractors: Dict[str, Type[BaseExtractor]] = {
            'pypdf': PyPDFExtractor,
            'unstructured': UnstructuredExtractor,
            'marker': MarkerExtractor,
            'markitdown': MarkItDownExtractor,
        }
        self._loaded_extractors: Dict[str, BaseExtractor] = {}

    def get_extractor(self, method: str) -> BaseExtractor:
        """Get extractor instance with lazy loading.

        Args:
            method: Name of the extraction method

        Returns:
            Initialized extractor instance

        Raises:
            ValueError: If method is not supported
            ImportError: If dependencies for method are not available
        """
        if method not in self._loaded_extractors:
            if method not in self._available_extractors:
                raise ValueError(
                    f"Unknown extraction method: {method}. "
                    f"Supported methods: {self.SUPPORTED_METHODS}"
                )

            try:
                self._loaded_extractors[method] = (
                    self._available_extractors[method]()
                )
            except ImportError as e:
                raise ImportError(
                    f"Dependencies for {method} extractor not available: {e}"
                ) from e

        return self._loaded_extractors[method]

    def detect_optimal_extractor(self, file_path: Path) -> str:
        """Recommend optimal extractor based on file type.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Recommended extractor method name
        """
        file_extension = file_path.suffix.lower()

        # Route non-PDF files to MarkItDown for universal support
        if file_extension in [
            '.docx', '.pptx', '.xlsx', '.xls', '.jpg',
            '.jpeg', '.png', '.gif', '.mp3', '.wav',
            '.html', '.epub', '.zip', '.csv', '.json', '.xml'
        ]:
            return 'markitdown'

        # For PDFs, default to unstructured for quality
        elif file_extension == '.pdf':
            return 'unstructured'

        # For unknown/text formats, try MarkItDown first
        else:
            return 'markitdown'

    def extract_text_from_file(self, file_path: Union[str, Path],
                               method: str = "auto",
                               **kwargs) -> ExtractionResult:
        """Extract text using specified or auto-detected method.

        Args:
            file_path: Path to file to extract text from
            method: Extraction method ("auto" for auto-detection)
            **kwargs: Additional extractor-specific options

        Returns:
            ExtractionResult containing extracted text and metrics
        """
        file_path = Path(file_path)

        if method == "auto":
            method = self.detect_optimal_extractor(file_path)
            logger.info(
                f"Auto-detected method '{method}' for {file_path.name}"
            )

        extractor = self.get_extractor(method)

        if not extractor.supports_format(file_path):
            # Try to find a compatible extractor
            for alt_method in self.SUPPORTED_METHODS:
                if alt_method != method:
                    try:
                        alt_extractor = self.get_extractor(alt_method)
                        if alt_extractor.supports_format(file_path):
                            logger.warning(
                                f"Method {method} doesn't support "
                                f"{file_path.suffix}, using {alt_method}"
                            )
                            extractor = alt_extractor
                            method = alt_method
                            break
                    except ImportError:
                        continue
            else:
                raise ValueError(
                    f"No available extractor supports format {file_path.suffix}"
                )

        return extractor.extract(file_path, **kwargs)

    # Backward compatibility methods
    def extract_text_from_pdf(self, pdf_path: Union[str, Path],
                              method: str = "unstructured",
                              track_performance: bool = True) -> Optional[ExtractionResult]:
        """Legacy method for PDF extraction (backward compatibility).

        Args:
            pdf_path: Path to PDF file
            method: Extraction method
            track_performance: Whether to track performance

        Returns:
            ExtractionResult or None if extraction fails
        """
        warnings.warn(
            "extract_text_from_pdf is deprecated. Use extract_text_from_file instead.",
            DeprecationWarning,
            stacklevel=2
        )

        try:
            return self.extract_text_from_file(
                pdf_path, method, track_performance=track_performance
            )
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return None

    def _get_method_output_path(self, method: str) -> Path:
        """Get output directory for specific extraction method."""
        method_dir = self.processed_path / method
        method_dir.mkdir(parents=True, exist_ok=True)
        return method_dir

    def discover_documents(self, file_pattern: str = "*") -> List[Path]:
        """Discover documents in the raw data directory.

        Args:
            file_pattern: Glob pattern for file discovery

        Returns:
            List of discovered file paths
        """
        return list(self.raw_path.glob(file_pattern))

    def extract_metadata_from_filename(self, file_path: Path) -> Dict:
        """Extract metadata from filename (backward compatibility)."""
        warnings.warn(
            "This method is deprecated. Use MetadataExtractor.extract_metadata_from_filename instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return MetadataExtractor.extract_metadata_from_filename(file_path)

    def process_document(self, file_path: Path,
                         method: str = "auto",
                         **kwargs) -> Dict:
        """Process a single document and return comprehensive results.

        Args:
            file_path: Path to document to process
            method: Extraction method
            **kwargs: Additional options

        Returns:
            Dictionary containing extraction results and metadata
        """
        # Extract metadata
        metadata = MetadataExtractor.extract_metadata_from_filename(file_path)

        # Extract text
        try:
            extraction_result = self.extract_text_from_file(
                file_path, method, **kwargs
            )

            return {
                "status": "success",
                "file_path": str(file_path),
                "metadata": metadata,
                "extraction_result": extraction_result,
                "method_used": extraction_result.method_specific_data.get(
                    'extraction_method', method
                )
            }

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return {
                "status": "error",
                "file_path": str(file_path),
                "metadata": metadata,
                "error": str(e),
                "method_attempted": method
            }

    def process_documents(self, file_paths: Optional[List[Path]] = None,
                          file_pattern: str = "*",
                          method: str = "auto",
                          **kwargs) -> List[Dict]:
        """Process multiple documents.

        Args:
            file_paths: Specific files to process (if None, discover automatically)
            file_pattern: Pattern for file discovery
            method: Extraction method
            **kwargs: Additional options

        Returns:
            List of processing results
        """
        if file_paths is None:
            file_paths = self.discover_documents(file_pattern)

        results = []
        for file_path in file_paths:
            result = self.process_document(file_path, method, **kwargs)
            results.append(result)

        return results
