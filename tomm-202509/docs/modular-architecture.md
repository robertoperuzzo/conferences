# Modular Document Preprocessing Architecture

## Overview

The document preprocessing system has been refactored into a modular, pluggable architecture that supports multiple extraction methods and easy extension for new document formats.

## Architecture Components

### Core Classes

#### BaseExtractor

- **Location**: `src/preprocessor/base.py`
- **Purpose**: Abstract base class defining the extraction interface
- **Key Methods**:
  - `supports_format(file_path)`: Check if extractor can handle the file format
  - `extract(file_path, **kwargs)`: Perform text extraction
  - `get_supported_formats()`: Return list of supported file extensions

#### ExtractionResult

- **Location**: `src/preprocessor/base.py`
- **Purpose**: Standardized result format across all extractors
- **Attributes**:
  - `text`: Extracted text content
  - `metadata`: File metadata (size, type, etc.)
  - `method_specific_data`: Extractor-specific information
  - `processing_time`: Time taken for extraction

#### DocumentPreprocessor

- **Location**: `src/preprocessor/document_preprocessor.py`
- **Purpose**: Main orchestrator with lazy loading and format detection
- **Features**:
  - Lazy loading of extractors (loaded only when needed)
  - Automatic format detection and routing
  - Backward compatibility with deprecated methods
  - Batch processing capabilities

### Extractor Implementations

#### PyPDFExtractor

- **Location**: `src/preprocessor/extractors/pypdf_extractor.py`
- **Formats**: PDF files
- **Features**: Fast baseline extraction using LangChain's PyPDFParser
- **Use Case**: Simple PDFs without complex layouts

#### UnstructuredExtractor

- **Location**: `src/preprocessor/extractors/unstructured_extractor.py`
- **Formats**: PDF files
- **Features**: Premium quality with structure awareness
- **Use Case**: Complex PDFs with tables, headers, and structured content

#### MarkerExtractor

- **Location**: `src/preprocessor/extractors/marker_extractor.py`
- **Formats**: PDF files
- **Features**: AI/ML-enhanced processing with layout detection
- **Use Case**: Complex academic papers with equations and figures

#### MarkItDownExtractor

- **Location**: `src/preprocessor/extractors/markitdown_extractor.py`
- **Formats**: Office docs, images, audio, video, HTML, and more
- **Features**: Multi-format processing with LLM-optimized output
- **Use Case**: Non-PDF documents and multimedia content

### Utility Modules

#### PerformanceTracker

- **Location**: `src/preprocessor/utils/performance_tracker.py`
- **Purpose**: Performance monitoring and metrics collection
- **Metrics**: Processing time, extraction rate, memory usage

#### QualityAnalyzer

- **Location**: `src/preprocessor/utils/quality_analyzer.py`
- **Purpose**: Text quality assessment
- **Metrics**: Text length, readability score, content structure

#### MetadataExtractor

- **Location**: `src/preprocessor/utils/metadata_extractor.py`
- **Purpose**: File metadata extraction and filename generation
- **Features**: File size, type detection, standardized naming

## Usage Examples

### Basic Usage

```python
from src.preprocessor import DocumentPreprocessor

dp = DocumentPreprocessor()

# Direct method selection
result = dp.extract_text_from_file("document.pdf", method="marker")
result = dp.extract_text_from_file("presentation.pptx", method="markitdown")

# Auto-detection based on file format
result = dp.extract_text_from_file("document.docx", method="auto")
```

### Batch Processing

```python
# Process multiple documents
results = dp.process_documents(method="unstructured")

# Process with performance tracking
results = dp.process_documents(
    method="markitdown",
    track_performance=True
)
```

### Custom Configuration

```python
# Access specific extractor
markitdown_extractor = dp._get_extractor("markitdown")
result = markitdown_extractor.extract(file_path, custom_option=True)

# Check supported formats
formats = dp.get_supported_formats()
print(f"Supported formats: {formats}")
```

## Backward Compatibility

The architecture maintains backward compatibility through:

1. **Deprecated Methods**: Legacy methods are preserved with deprecation warnings
2. **Method Mapping**: Old method names are mapped to new extractors
3. **Result Format**: Consistent result structure across versions

### Deprecated Methods

```python
# These methods work but show deprecation warnings
result = dp.extract_text_from_pdf(file_path, method="pypdf")  # Deprecated
filename = dp._generate_output_filename(file_path)  # Deprecated

# Use these instead
result = dp.extract_text_from_file(file_path, method="pypdf")
filename = MetadataExtractor.generate_output_filename(file_path)
```

## Adding New Extractors

To add a new extractor:

1. **Create Extractor Class**:

   ```python
   from src.preprocessor.base import BaseExtractor, ExtractionResult

   class MyExtractor(BaseExtractor):
       def supports_format(self, file_path: Path) -> bool:
           return file_path.suffix.lower() in ['.xyz']

       def extract(self, file_path: Path, **kwargs) -> ExtractionResult:
           # Implement extraction logic
           pass
   ```

2. **Register in DocumentPreprocessor**:

   ```python
   # Add to SUPPORTED_METHODS and _extractor_map
   SUPPORTED_METHODS = ['pypdf', 'unstructured', 'marker', 'markitdown', 'myextractor']
   ```

3. **Add Lazy Loading**:
   ```python
   def _get_extractor(self, method: str):
       if method == 'myextractor' and 'myextractor' not in self._extractors:
           from .extractors.my_extractor import MyExtractor
           self._extractors['myextractor'] = MyExtractor()
   ```

## Performance Considerations

- **Lazy Loading**: Extractors are loaded only when first used
- **Memory Efficiency**: Each extractor manages its own dependencies
- **Caching**: Results can be cached at the application level
- **Parallel Processing**: Multiple extractors can run in parallel

## Testing

The architecture includes comprehensive tests:

- **Unit Tests**: Individual extractor functionality
- **Integration Tests**: End-to-end processing workflows
- **Backward Compatibility**: Legacy method preservation
- **Performance Tests**: Extraction speed and quality metrics

## Configuration

Extractors can be configured through:

- **Environment Variables**: Global settings
- **Configuration Files**: Per-extractor settings
- **Runtime Parameters**: Method-specific options

## Error Handling

The system provides robust error handling:

- **Graceful Degradation**: Falls back to alternative methods
- **Detailed Logging**: Comprehensive error reporting
- **Exception Propagation**: Clear error messages for debugging

## Future Extensions

The modular architecture supports future enhancements:

- **New Document Formats**: Easy addition of new extractors
- **Cloud Processing**: Remote extraction services
- **Streaming Processing**: Large file handling
- **Plugin System**: Third-party extractor integration
