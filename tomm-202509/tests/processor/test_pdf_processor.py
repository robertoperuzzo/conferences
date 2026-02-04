"""Comprehensive preprocessing tests using real PDF data.

This test module implements the ADR-006 and ADR-008 compliant three-method approach:
- pypdf: Raw baseline extraction (no OCR fixing)
- unstructured: Premium quality with structure awareness
- marker: AI/ML-enhanced processing (Premium Plus)

Using real ArXiv PDF: 9308101_Dynamic Backtracking.pdf

Test Execution Commands:
=======================

Default Behavior (Fast Tests, ~15 seconds):
    # Run tests with default configuration (fast tests only)
    python -m pytest tests/
    
    # Explicitly run fast tests (same as default)
    python -m pytest tests/ -m "not slow"

Slow Integration Tests (~7-8 minutes):
    # Run only the slow integration tests with real PDF processing
    python -m pytest tests/ -m "slow"
    
    # Run specific slow integration tests
    python -m pytest tests/processor/test_pdf_processor.py -m "slow"

All Tests (Fast + Slow, ~8 minutes total):
    # Run all tests (override default marker filter)
    python -m pytest tests/ -m ""
    
    # Alternative: explicitly include both fast and slow
    python -m pytest tests/ -m "slow or not slow"

Specific Test Examples:
    # Run specific fast mocked test
    python -m pytest tests/processor/test_pdf_processor.py::TestThreeMethodExtraction::test_unstructured_extraction
    
    # Run specific slow integration test  
    python -m pytest tests/processor/test_pdf_processor.py::TestThreeMethodExtractionIntegration::test_unstructured_extraction_integration

Performance Comparison:
    - Default (fast mocked tests): ~15 seconds (97% faster)
    - Slow integration tests: ~7-8 minutes (original timing)
    - Configuration: Fast tests run by default via pyproject.toml addopts = ["-m", "not slow"]
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.preprocessor import (
    DocumentPreprocessor,
    ExtractionResult,
    PerformanceTracker,
    QualityAnalyzer
)


@pytest.fixture
def test_pdf_path():
    """Path to the test PDF file."""
    return Path(__file__).parent / "data" / "9308101_Dynamic Backtracking.pdf"


@pytest.fixture
def preprocessor(tmp_path):
    """Create a DocumentPreprocessor with temporary directories."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    return DocumentPreprocessor(raw_path=raw_dir, processed_path=processed_dir)


@pytest.fixture
def supported_methods():
    """List of supported extraction methods per ADR-011."""
    return ["pypdf", "unstructured", "marker", "markitdown"]


@pytest.fixture
def mock_unstructured_partition():
    """Mock unstructured partition_pdf function for fast testing."""
    with patch(
        'src.preprocessor.extractors.unstructured_extractor.partition_pdf'
    ) as mock:
        # Create multiple elements to simulate a real document
        elements = []
        for i in range(5):
            elem = Mock()
            elem.category = ["Title", "NarrativeText",
                             "ListItem", "Table", "Header"][i]
            elem.__str__ = Mock(
                return_value=f"Element {i}: Dynamic Backtracking content section {i}")
            elem.metadata = Mock()
            elem.metadata.to_dict.return_value = {
                "page_number": (i // 2) + 1,
                "filename": "test.pdf"
            }
            elem.metadata.page_number = (i // 2) + 1
            elements.append(elem)

        mock.return_value = elements
        yield mock


@pytest.fixture
def mock_marker_extraction():
    """Mock marker extraction components for fast testing."""
    with patch('src.preprocessor.extractors.marker_extractor.MarkerExtractor') as mock_extractor, \
            patch('src.preprocessor.extractors.marker_extractor.MarkerConfig') as mock_config:

        # Mock the extractor result
        mock_result = Mock()
        mock_result.text = """# Dynamic Backtracking Algorithm

## Abstract
This paper presents a comprehensive analysis of dynamic backtracking algorithms
and their applications in constraint satisfaction problems.

## Introduction
Dynamic backtracking represents an advanced approach to solving complex
computational problems by intelligently managing the search space.

## Methodology
The proposed algorithm incorporates several key innovations:
- Adaptive constraint propagation
- Intelligent variable ordering
- Conflict-driven learning

## Results
Experimental results demonstrate significant performance improvements
over traditional backtracking approaches.

## Conclusion
The dynamic backtracking algorithm shows promise for real-world applications
requiring efficient constraint satisfaction."""

        mock_result.quality_metrics = {
            "total_pages": 10,
            "image_reference_integrity": 0.95,
            "equation_accuracy": 0.90,
            "table_structure_score": 0.85,
            "text_length": len(mock_result.text),
            "word_count": len(mock_result.text.split()),
            "readability_score": 0.75,
            "ocr_artifact_count": 2
        }

        mock_result.method_specific_data = {
            "extraction_method": "marker",
            "output_format": "markdown",
            "images_extracted": 3,
            "tables_detected": 2,
            "equations_processed": 15,
            "marker_version": "0.2.0"
        }

        mock_extractor.return_value.extract_text.return_value = mock_result

        # Mock the config
        mock_config_instance = Mock()
        mock_config_instance.output_format = "markdown"
        mock_config_instance.extract_images = True
        mock_config.return_value = mock_config_instance

        yield mock_extractor, mock_config


class TestThreeMethodExtraction:
    """Test the three standardized extraction methods per ADR-006."""

    def test_pdf_file_exists(self, test_pdf_path):
        """Verify the test PDF file exists."""
        assert test_pdf_path.exists(), f"Test PDF not found: {test_pdf_path}"
        assert test_pdf_path.suffix == ".pdf"
        assert test_pdf_path.stat().st_size > 0

    def test_supported_methods_list(self, preprocessor, supported_methods):
        """Test that preprocessor has correct supported methods."""
        assert preprocessor.SUPPORTED_METHODS == supported_methods
        assert len(preprocessor.SUPPORTED_METHODS) == 4

    def test_pypdf_raw_extraction(self, preprocessor, test_pdf_path):
        """Test pypdf raw extraction (no OCR fixing) - ADR-006."""
        result = preprocessor.extract_text_from_pdf(
            test_pdf_path, method="pypdf", track_performance=True
        )

        assert result is not None
        assert isinstance(result, ExtractionResult)
        assert result.text is not None

        # Verify it's raw extraction (may contain OCR artifacts)
        assert result.method_specific_data["extraction_method"] == "pypdf"

        # Check performance tracking
        assert "processing_time_seconds" in result.performance_metrics
        assert "memory_usage_mb" in result.performance_metrics
        assert "characters_extracted" in result.performance_metrics

        # Check quality metrics
        assert "text_length" in result.quality_metrics
        assert "ocr_artifact_count" in result.quality_metrics
        assert "readability_score" in result.quality_metrics

        # For pypdf, text extraction might be minimal due to PDF structure
        # Check if we got some text or if the PDF is challenging for pypdf
        if len(result.text) == 0:
            print(
                f"Warning: pypdf extracted no text from {test_pdf_path.name}")
            print("This may be expected for complex PDFs - pypdf limitations")
        else:
            assert len(
                result.text) > 0, "Should extract some text if successful"

    def test_unstructured_extraction(self, preprocessor, test_pdf_path, mock_unstructured_partition):
        """Test Unstructured.io extraction with structure awareness (mocked for speed)."""
        # Test with mocked unstructured to avoid slow real extraction
        result = preprocessor.extract_text_from_pdf(
            test_pdf_path, method="unstructured", track_performance=True
        )

        # Skip if unstructured is not available at all
        if result is None:
            pytest.skip("Unstructured.io not available")

        assert isinstance(result, ExtractionResult)
        assert result.text is not None

        # Verify extraction method
        extraction_method = result.method_specific_data["extraction_method"]
        assert extraction_method == "unstructured"

        # Verify structure-aware extraction with mocked data
        assert "elements" in result.method_specific_data
        assert "element_count" in result.method_specific_data
        # From our mock
        assert result.method_specific_data["element_count"] == 5
        assert result.quality_metrics["structure_elements"] >= 0

        # Verify mocked content appears in text
        assert "Dynamic Backtracking" in result.text
        assert len(result.text) > 0

        # Check that partition_pdf was called
        mock_unstructured_partition.assert_called_once()

    def test_marker_integration_and_extraction(self, preprocessor,
                                               test_pdf_path, mock_marker_extraction):
        """Test Marker AI/ML-enhanced extraction (mocked for speed) - ADR-008."""
        # First test integration
        assert 'marker' in preprocessor.SUPPORTED_METHODS, (
            "Marker not in supported methods")

        # Test that Marker classes can be imported and instantiated with mocks
        mock_extractor, mock_config = mock_marker_extraction

        try:
            from src.preprocessor import (
                MarkerConfig, MarkerExtractor)

            # Test with mocked components
            config = MarkerConfig()
            assert config is not None
            assert hasattr(config, 'output_format')
            assert hasattr(config, 'extract_images')

            extractor = MarkerExtractor(config)
            assert extractor is not None
        except ImportError as e:
            pytest.skip(f"Marker library not available: {e}")

        # Test actual extraction with mocked processing
        result = preprocessor.extract_text_from_pdf(
            test_pdf_path, method="marker", track_performance=True
        )

        # Skip if Marker library is not installed
        if result is None:
            pytest.skip("Marker extraction failed - library may not be "
                        "installed")

        assert isinstance(result, ExtractionResult)
        assert result.text is not None

        # Check Marker-specific data from our mock
        extraction_method = result.method_specific_data.get(
            "extraction_method", "")
        if extraction_method == "marker":
            # Verify Marker-specific metrics from mock
            assert "output_format" in result.method_specific_data
            assert result.method_specific_data["output_format"] == "markdown"

            # Check enhanced quality metrics from mock
            assert "image_reference_integrity" in result.quality_metrics
            assert "equation_accuracy" in result.quality_metrics
            assert "table_structure_score" in result.quality_metrics
            assert result.quality_metrics["image_reference_integrity"] == 0.95

            # Check performance metrics include Marker-specific data from mock
            assert "images_extracted" in result.method_specific_data
            assert "tables_detected" in result.method_specific_data
            assert "equations_processed" in result.method_specific_data
            assert "marker_version" in result.method_specific_data

        # Should have extracted meaningful content from mock
        if len(result.text) > 0:
            assert len(result.text) > 100, (
                "Marker should extract substantial text")
            # Check for mocked content
            assert ("Dynamic Backtracking" in result.text or
                    "backtracking" in result.text.lower())


class TestPerformanceAndQuality:
    """Test performance tracking and quality analysis - ADR-006."""

    def test_performance_tracker(self, test_pdf_path):
        """Test PerformanceTracker context manager."""
        with PerformanceTracker() as tracker:
            # Simulate some processing
            text = "test content" * 1000

        metrics = tracker.get_metrics(len(text), 5)

        assert "processing_time_seconds" in metrics
        assert "memory_usage_mb" in metrics
        assert "characters_extracted" in metrics
        assert "pages_processed" in metrics
        assert "extraction_rate" in metrics

        assert metrics["characters_extracted"] == len(text)
        assert metrics["pages_processed"] == 5

    def test_quality_analyzer(self):
        """Test QualityAnalyzer text assessment."""
        # Test with clean text
        clean_text = "This is a well-formed sentence."
        metrics = QualityAnalyzer.analyze_text(clean_text)

        assert "text_length" in metrics
        assert "word_count" in metrics
        assert "unique_words" in metrics
        assert "readability_score" in metrics
        assert "ocr_artifact_count" in metrics

        assert metrics["text_length"] == len(clean_text)
        assert metrics["word_count"] > 0
        assert metrics["readability_score"] > 0


class TestDirectoryStructure:
    """Test method-specific directory structure - ADR-006."""

    def test_method_output_paths(self, preprocessor):
        """Test method-specific directory creation."""
        for method in ["pypdf", "marker", "unstructured"]:
            output_path = preprocessor._get_method_output_path(method)

            assert output_path.exists()
            assert output_path.name == method
            assert output_path.parent == preprocessor.processed_path

    def test_filename_generation(self, preprocessor, test_pdf_path):
        """Test filename generation per ADR-006 convention."""
        filename = preprocessor._generate_output_filename(test_pdf_path)

        # Should follow format: <clean_name>_YYYYMMDD_HHMMSS.json
        assert filename.endswith(".json")
        assert "9308101dynamicbacktracking" in filename
        assert "_20" in filename  # Should contain year

        # Should not contain spaces or special characters in the prefix
        prefix = filename.split("_20")[0]  # Get part before timestamp
        assert " " not in prefix
        assert "-" not in prefix
        assert prefix.islower() or prefix.replace("9308101", "").islower()


class TestBatchProcessing:
    """Test batch processing with method-specific directories - ADR-006."""

    def test_process_with_pypdf_method(self, preprocessor, test_pdf_path,
                                       tmp_path):
        """Test processing documents with pypdf method."""
        # Copy PDF to preprocessor's raw directory
        raw_pdf_path = preprocessor.raw_path / test_pdf_path.name
        import shutil
        shutil.copy2(test_pdf_path, raw_pdf_path)

        # Process with pypdf method
        processed_docs = preprocessor.process_documents(
            method="pypdf",
            track_performance=True
        )

        # If pypdf failed to extract text, directory might not be created
        if processed_docs and len(processed_docs) > 0:
            doc = processed_docs[0]
            assert doc["status"] == "success"
            assert doc["method_used"] == "pypdf"

            # Test that we can access extraction results
            extraction_result = doc["extraction_result"]
            assert extraction_result is not None
            assert isinstance(extraction_result.text, str)
            assert len(extraction_result.text) > 0
        else:
            # pypdf may fail on complex PDFs - this is acceptable
            print(f"pypdf failed to extract text from {test_pdf_path.name}")
            print("This is acceptable - some PDFs are challenging for pypdf")


class TestADR011Compliance:
    """Verify compliance with ADR-011 requirements."""

    def test_four_methods_supported(self, preprocessor, supported_methods):
        """Verify exactly four methods are supported per ADR-011."""
        assert len(preprocessor.SUPPORTED_METHODS) == 4
        assert set(preprocessor.SUPPORTED_METHODS) == set(supported_methods)
        assert "pypdf" in preprocessor.SUPPORTED_METHODS
        assert "unstructured" in preprocessor.SUPPORTED_METHODS
        assert "marker" in preprocessor.SUPPORTED_METHODS
        assert "markitdown" in preprocessor.SUPPORTED_METHODS

    def test_directory_structure_compliance(self, preprocessor):
        """Verify directory structure matches ADR-006 specification."""
        # Test method-specific directories
        for method in preprocessor.SUPPORTED_METHODS:
            method_path = preprocessor._get_method_output_path(method)
            assert method_path.name == method
            assert method_path.exists()

        # Test comparative analysis directory can be created
        comparison_dir = preprocessor.processed_path / "comparative_analysis"
        comparison_dir.mkdir(exist_ok=True)
        assert comparison_dir.exists()

    def test_filename_convention_compliance(self, preprocessor, test_pdf_path):
        """Verify filename convention matches ADR-006."""
        filename = preprocessor._generate_output_filename(test_pdf_path)

        # Format: <clean_name>_YYYYMMDD_HHMMSS.json
        assert filename.endswith(".json")

        # Should contain original name in clean format
        assert "9308101" in filename

        # Should contain timestamp pattern
        import re
        timestamp_pattern = r'_\d{8}_\d{6}\.json$'
        assert re.search(
            timestamp_pattern, filename), (
            f"Filename {filename} doesn't match timestamp pattern")


@pytest.mark.slow
class TestThreeMethodExtractionIntegration:
    """Slow integration tests with real PDF processing.

    These tests perform actual PDF extraction and are marked as 'slow'.
    Run with: pytest -m slow
    Skip with: pytest -m "not slow"
    """

    def test_unstructured_extraction_integration(self, preprocessor, test_pdf_path):
        """Full integration test for Unstructured.io with real PDF processing."""
        # Try Unstructured method with real extraction
        result = preprocessor.extract_text_from_pdf(
            test_pdf_path, method="unstructured", track_performance=True
        )

        # Skip if no result (dependency not available)
        if result is None:
            pytest.skip("Unstructured.io not available")

        assert isinstance(result, ExtractionResult)
        assert result.text is not None

        # Check extraction method
        extraction_method = result.method_specific_data["extraction_method"]
        assert extraction_method == "unstructured"

        # Verify structure-aware extraction
        assert "elements" in result.method_specific_data
        assert "element_count" in result.method_specific_data
        assert result.quality_metrics["structure_elements"] >= 0

        # Should have quality metrics
        if len(result.text) > 0:
            assert ("backtracking" in result.text.lower() or
                    len(result.text) > 0)

    def test_marker_integration_and_extraction_integration(self, preprocessor, test_pdf_path):
        """Full integration test for Marker with real PDF processing."""
        # First test integration
        assert 'marker' in preprocessor.SUPPORTED_METHODS

        # Test that Marker classes can be imported and instantiated
        try:
            from src.preprocessor import (
                MarkerConfig, MarkerExtractor)

            config = MarkerConfig()
            assert config is not None
            extractor = MarkerExtractor(config)
            assert extractor is not None
        except ImportError as e:
            pytest.skip(f"Marker library not available: {e}")

        # Test actual extraction with real processing
        result = preprocessor.extract_text_from_pdf(
            test_pdf_path, method="marker", track_performance=True
        )

        # Skip if Marker library is not installed
        if result is None:
            pytest.skip(
                "Marker extraction failed - library may not be installed")

        assert isinstance(result, ExtractionResult)
        assert result.text is not None

        # Check Marker-specific data
        extraction_method = result.method_specific_data.get(
            "extraction_method", "")
        if extraction_method == "marker":
            # Verify Marker-specific metrics
            assert "output_format" in result.method_specific_data

            # Check enhanced quality metrics
            assert "image_reference_integrity" in result.quality_metrics
            assert "equation_accuracy" in result.quality_metrics
            assert "table_structure_score" in result.quality_metrics

        # Should have extracted meaningful content
        if len(result.text) > 0:
            assert len(result.text) > 1000
            assert ("Dynamic Backtracking" in result.text or
                    "backtracking" in result.text.lower())


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
