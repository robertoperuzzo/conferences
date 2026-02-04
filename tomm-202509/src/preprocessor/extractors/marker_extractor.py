"""Marker extractor implementation for AI/ML-enhanced PDF processing.

This module provides PDF text extraction using Marker library with
advanced layout detection, mathematical equation processing, and
LLM enhancement capabilities.
"""

import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

# Marker for research-grade PDF processing
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    PdfConverter = None
    create_model_dict = None
    text_from_rendered = None
    ConfigParser = None
    MARKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class MarkerExtractionError(Exception):
    """Custom exception for Marker extraction failures."""


@dataclass
class MarkerConfig:
    """Configuration for Marker PDF extraction."""
    output_format: str = "markdown"  # markdown|json|html|chunks
    use_llm: bool = False           # LLM enhancement
    force_ocr: bool = False         # Force OCR processing
    extract_images: bool = True     # Extract images
    paginate_output: bool = False   # Page separation
    debug: bool = False            # Debug mode

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for Marker."""
        return {
            "output_format": self.output_format,
            "use_llm": self.use_llm,
            "force_ocr": self.force_ocr,
            "disable_image_extraction": not self.extract_images,
            "paginate_output": self.paginate_output,
            "debug": self.debug
        }


class MarkerExtractor(BaseExtractor):
    """Marker-based PDF extractor.

    Uses Marker library for AI/ML-enhanced PDF processing with superior
    layout detection, mathematical equation processing, and optional
    LLM enhancement.
    """

    def __init__(self, config: Optional[MarkerConfig] = None):
        """Initialize Marker extractor with configuration.

        Args:
            config: MarkerConfig instance, defaults to basic markdown
                extraction
        """
        self._check_dependencies()
        self.config = config or MarkerConfig()
        self._artifact_dict = None
        self._converter = None

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        if not MARKER_AVAILABLE:
            raise ImportError(
                "Marker dependencies not available. "
                "Install with: pip install marker-pdf"
            )

    @property
    def name(self) -> str:
        """Return the name identifier of this extractor."""
        return "marker"

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".pdf"]

    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return file_path.suffix.lower() in self.supported_formats

    @property
    def artifact_dict(self):
        """Lazy loading of Marker models to avoid startup overhead."""
        if self._artifact_dict is None:
            self._artifact_dict = create_model_dict()
        return self._artifact_dict

    @property
    def converter(self):
        """Lazy loading of Marker converter."""
        if self._converter is None:
            config_parser = ConfigParser(self.config.to_dict())
            self._converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=self.artifact_dict,
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service()
            )
        return self._converter

    def extract(self, file_path: Path,
                track_performance: bool = True,
                **kwargs) -> ExtractionResult:
        """Extract text using Marker with full performance metrics.

        Args:
            file_path: Path to PDF file
            track_performance: Whether to track performance metrics
            **kwargs: Additional options (unused for this extractor)

        Returns:
            ExtractionResult with text, performance metrics, and quality
        """
        self._check_file_exists(file_path)
        self._check_format_supported(file_path)

        with PerformanceTracker() as tracker:
            try:
                # Convert document with Marker
                rendered = self.converter(str(file_path))

                # Extract text based on output format
                if self.config.output_format == "markdown":
                    text = (rendered.markdown if hasattr(rendered, 'markdown')
                            else str(rendered))
                    method_data = {
                        "output_format": "markdown",
                        "metadata": getattr(rendered, 'metadata', {}),
                        "images": getattr(rendered, 'images', {})
                    }
                elif self.config.output_format == "json":
                    # JSON structure as text for compatibility
                    text = str(rendered)
                    method_data = {
                        "output_format": "json",
                        "children": getattr(rendered, 'children', []),
                        "block_type": getattr(rendered, 'block_type',
                                              'Document'),
                        "metadata": getattr(rendered, 'metadata', {})
                    }
                else:
                    # For other formats, extract text using Marker's utility
                    text, _, images = text_from_rendered(rendered)
                    method_data = {
                        "output_format": self.config.output_format,
                        "images": images,
                        "metadata": getattr(rendered, 'metadata', {})
                    }

            except Exception as e:
                raise MarkerExtractionError(
                    f"Marker extraction failed: {str(e)}"
                ) from e

            # Calculate performance metrics
            performance_metrics = (
                tracker.get_metrics(
                    len(text),
                    method_data.get('metadata', {}).get('page_count', 1)
                ) if track_performance else {}
            )

            # Add Marker-specific performance metrics
            if track_performance:
                performance_metrics.update({
                    "images_extracted": len(method_data.get('images', {})),
                    "tables_detected": self._count_tables(method_data),
                    "equations_processed": self._count_equations(text),
                    "marker_version": self._get_marker_version(),
                    "llm_enhanced": self.config.use_llm,
                    "output_format": self.config.output_format
                })

            # Calculate quality metrics
            quality_metrics = QualityAnalyzer.analyze_text(text)

            # Add Marker-specific quality metrics
            quality_metrics.update({
                "structure_elements": self._count_structure_elements(
                    method_data
                ),
                "image_reference_integrity": self._check_image_references(
                    text, method_data
                ),
                "equation_accuracy": self._assess_equation_quality(text),
                "table_structure_score": self._assess_table_quality(
                    method_data
                )
            })

            return ExtractionResult(
                text=text,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                method_specific_data={
                    'extraction_method': 'marker',
                    'file_format': file_path.suffix.lower(),
                    'output_format': self.config.output_format,
                    'marker_version': self._get_marker_version(),
                    'llm_enhanced': self.config.use_llm,
                    'force_ocr': self.config.force_ocr,
                    'extract_images': self.config.extract_images,
                    'images_extracted': len(method_data.get('images', {})),
                    'tables_detected': self._count_tables(method_data),
                    'equations_processed': self._count_equations(text),
                    # Include only marker-specific metadata, not file metadata
                    'table_of_contents': method_data.get(
                        'metadata', {}
                    ).get('table_of_contents', []),
                    'document_structure': method_data.get(
                        'metadata', {}
                    ).get('document_structure', {}),
                    # For markdown format, include markdown-specific data
                    **({
                        'markdown_metadata': method_data.get('metadata', {}),
                        'images': method_data.get('images', {})
                    } if self.config.output_format == "markdown" else {}),
                    # For json format, include structure data
                    **({
                        'children': method_data.get('children', []),
                        'block_type': method_data.get('block_type', 'Document')
                    } if self.config.output_format == "json" else {})
                }
            )

    def _count_tables(self, method_data: Dict) -> int:
        """Count detected tables in the document."""
        if self.config.output_format == "json":
            # Count Table type elements in JSON structure
            return self._count_elements_by_type(
                method_data.get('children', []), 'Table')
        elif "metadata" in method_data:
            # Extract from metadata if available
            return method_data.get('metadata', {}).get('table_count', 0)
        return 0

    def _count_equations(self, text: str) -> int:
        """Count LaTeX equations in extracted text."""
        # Count both inline ($...$) and display ($$...$$) equations
        inline_count = len(re.findall(r'\$[^$]+\$', text))
        display_count = len(re.findall(r'\$\$[^$]+\$\$', text))
        return inline_count + display_count

    def _get_marker_version(self) -> str:
        """Get Marker library version."""
        try:
            import marker
            return getattr(marker, '__version__', 'unknown')
        except (ImportError, AttributeError):
            return 'unknown'

    def _count_structure_elements(self, method_data: Dict) -> int:
        """Count structural elements like headings, paragraphs, etc."""
        if self.config.output_format == "json":
            return self._count_all_elements(method_data.get('children', []))
        return 0

    def _count_elements_by_type(self, elements: List,
                                element_type: str) -> int:
        """Recursively count elements of specific type."""
        count = 0
        for element in elements:
            if isinstance(element, dict):
                if element.get('block_type') == element_type:
                    count += 1
                # Recursively check children
                children = element.get('children', [])
                if children:
                    count += self._count_elements_by_type(
                        children, element_type)
        return count

    def _count_all_elements(self, elements: List) -> int:
        """Recursively count all elements."""
        count = len(elements)
        for element in elements:
            if isinstance(element, dict):
                children = element.get('children', [])
                if children:
                    count += self._count_all_elements(children)
        return count

    def _check_image_references(self, text: str, method_data: Dict) -> float:
        """Check integrity of image references in text."""
        images = method_data.get('images', {})
        if not images:
            return 1.0  # No images to check

        # Count image references in text (Markdown images)
        image_refs = len(re.findall(r'!\[.*?\]\(.*?\)', text))
        extracted_images = len(images)

        if extracted_images == 0:
            return 1.0 if image_refs == 0 else 0.0

        # Return ratio of referenced to extracted images
        return min(1.0, image_refs / extracted_images)

    def _assess_equation_quality(self, text: str) -> float:
        """Assess quality of equation conversion."""
        # Look for properly formatted LaTeX equations
        total_equations = self._count_equations(text)
        if total_equations == 0:
            return 1.0

        # Check for malformed equations (basic heuristic)
        # Mixed delimiters
        malformed = len(re.findall(r'\$[^$]*\$[^$]*\$', text))
        # Incomplete display equations
        malformed += len(re.findall(r'\$\$[^$]*\$[^$]*\$\$', text))

        return max(0.0, 1.0 - (malformed / total_equations))

    def _assess_table_quality(self, method_data: Dict) -> float:
        """Assess quality of table structure preservation."""
        # Basic implementation - can be enhanced based on
        # Marker's table metadata
        if self.config.output_format == "json":
            tables = self._count_tables(method_data)
            return 1.0 if tables >= 0 else 0.0  # Basic check
        return 1.0
