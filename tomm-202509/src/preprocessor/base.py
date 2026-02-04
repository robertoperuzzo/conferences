"""Base classes and shared models for document preprocessors.

This module provides the foundation for all document extractors with common
interfaces, data models, and utilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any


@dataclass
class ExtractionResult:
    """Result of document text extraction with performance and quality metrics.

    This standardized result format is used by all extractors to ensure
    consistent output structure across different extraction methods.
    """
    text: str
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    method_specific_data: Dict[str, Any]

    @property
    def processing_time(self) -> float:
        """Get processing time from performance metrics.

        Returns:
            Processing time in seconds, or 0.0 if not available
        """
        return self.performance_metrics.get('processing_time_seconds', 0.0)


class BaseExtractor(ABC):
    """Abstract base class for all document extractors.

    This class defines the common interface that all extractors must implement,
    ensuring consistency and enabling pluggable extractor architecture.
    """

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this extractor can process the file format
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self, file_path: Path, **kwargs) -> ExtractionResult:
        """Extract text from the given file.

        Args:
            file_path: Path to the file to extract text from
            **kwargs: Additional extractor-specific options

        Returns:
            ExtractionResult containing extracted text and metrics

        Raises:
            ImportError: If required dependencies are not available
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name identifier of this extractor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions (with dots)."""
        raise NotImplementedError

    def _check_file_exists(self, file_path: Path) -> None:
        """Validate that the file exists.

        Args:
            file_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def _check_format_supported(self, file_path: Path) -> None:
        """Validate that the file format is supported.

        Args:
            file_path: Path to validate

        Raises:
            ValueError: If format is not supported
        """
        if not self.supports_format(file_path):
            raise ValueError(
                f"Extractor {self.name} does not support format "
                f"{file_path.suffix}. Supported: {self.supported_formats}"
            )
