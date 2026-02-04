"""Tests for the refactored extractors and MarkItDown integration.

This test file validates the new modular extractor architecture
and MarkItDown functionality per ADR-011.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.preprocessor import (
    DocumentPreprocessor,
    ExtractionResult,
    MarkItDownExtractor
)


class TestRefactoredArchitecture:
    """Test the refactored modular extractor architecture."""

    def test_extractor_lazy_loading(self, tmp_path):
        """Test that extractors are loaded only when needed."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        # Initially no extractors loaded
        assert len(preprocessor._loaded_extractors) == 0

        # Load one extractor
        extractor = preprocessor.get_extractor('pypdf')
        assert len(preprocessor._loaded_extractors) == 1
        assert 'pypdf' in preprocessor._loaded_extractors

        # Same extractor instance returned on subsequent calls
        extractor2 = preprocessor.get_extractor('pypdf')
        assert extractor is extractor2

    def test_format_detection_routing(self, tmp_path):
        """Test automatic format detection and extractor routing."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        # Test PDF routing
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        method = preprocessor.detect_optimal_extractor(pdf_path)
        assert method == 'unstructured'  # Default for PDFs

        # Test Office document routing
        docx_path = tmp_path / "test.docx"
        docx_path.touch()
        method = preprocessor.detect_optimal_extractor(docx_path)
        assert method == 'markitdown'

        # Test image routing
        jpg_path = tmp_path / "test.jpg"
        jpg_path.touch()
        method = preprocessor.detect_optimal_extractor(jpg_path)
        assert method == 'markitdown'

    def test_unsupported_method_error(self, tmp_path):
        """Test error handling for unsupported methods."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        with pytest.raises(ValueError, match="Unknown extraction method"):
            preprocessor.get_extractor('nonexistent')

    def test_four_methods_supported(self, tmp_path):
        """Verify all four methods are supported per ADR-011."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        expected_methods = ['pypdf', 'unstructured', 'marker', 'markitdown']
        assert set(preprocessor.SUPPORTED_METHODS) == set(expected_methods)
        assert len(preprocessor.SUPPORTED_METHODS) == 4


class TestMarkItDownExtractor:
    """Test MarkItDown extractor functionality."""

    @patch('src.preprocessor.extractors.markitdown_extractor.MarkItDown')
    def test_markitdown_extraction(self, mock_markitdown, tmp_path):
        """Test MarkItDown extraction with mocked library."""
        # Setup mock
        mock_result = Mock()
        mock_result.text_content = "# Test Document\n\nThis is a test."
        mock_instance = Mock()
        mock_instance.convert.return_value = mock_result
        mock_markitdown.return_value = mock_instance

        # Create test file
        test_file = tmp_path / "test.docx"
        test_file.write_text("dummy content")

        # Test extraction
        extractor = MarkItDownExtractor()
        result = extractor.extract(test_file)

        assert isinstance(result, ExtractionResult)
        assert result.text == "# Test Document\n\nThis is a test."
        assert result.method_specific_data['extraction_method'] == 'markitdown'
        assert result.method_specific_data['file_format'] == '.docx'

    def test_markitdown_supported_formats(self):
        """Test that MarkItDown supports expected formats."""
        try:
            extractor = MarkItDownExtractor()

            supported = extractor.supported_formats
            expected_formats = [
                '.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.png',
                '.mp3', '.wav', '.html', '.csv', '.json', '.xml'
            ]

            for fmt in expected_formats:
                assert fmt in supported

        except ImportError:
            pytest.skip("MarkItDown not available")

    def test_markitdown_format_support_check(self, tmp_path):
        """Test format support checking."""
        try:
            extractor = MarkItDownExtractor()

            # Supported format
            docx_file = tmp_path / "test.docx"
            docx_file.touch()
            assert extractor.supports_format(docx_file)

            # Unsupported format
            unknown_file = tmp_path / "test.unknown"
            unknown_file.touch()
            assert not extractor.supports_format(unknown_file)

        except ImportError:
            pytest.skip("MarkItDown not available")


class TestBackwardCompatibility:
    """Test backward compatibility with old API."""

    def test_extract_text_from_pdf_deprecated(self, tmp_path):
        """Test that legacy method still works but shows deprecation warning."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy")

        with pytest.warns(DeprecationWarning, match="extract_text_from_pdf is deprecated"):
            with patch.object(preprocessor, 'extract_text_from_file') as mock_extract:
                mock_extract.return_value = Mock()
                preprocessor.extract_text_from_pdf(pdf_path)
                mock_extract.assert_called_once()

    def test_generate_output_filename_deprecated(self, tmp_path):
        """Test deprecated filename generation method."""
        preprocessor = DocumentPreprocessor(
            raw_path=tmp_path / "raw",
            processed_path=tmp_path / "processed"
        )

        test_file = tmp_path / "test.pdf"
        test_file.touch()

        with pytest.warns(DeprecationWarning, match="generate_output_filename instead"):
            filename = preprocessor._generate_output_filename(test_file)
            assert filename.endswith('.json')
            assert 'test' in filename
