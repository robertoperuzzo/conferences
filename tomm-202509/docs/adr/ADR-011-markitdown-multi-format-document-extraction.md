# ADR-011: Integration of MarkItDown for Multi-Format Document Extraction

## Status

**PROPOSED** - This ADR is proposed for discussion

## Context

The current document preprocessing implementation in `src/preprocessor/document_preprocessor.py` provides three specialized PDF extraction methods as established in previous ADRs:

### Current Implementation

1. **LangChain PyPDFParser** (`pypdf`) - Fast baseline extraction using LangChain's PyPDFParser wrapper
2. **Unstructured.io** (`unstructured`) - Premium quality with structure awareness for element-based processing
3. **Marker** (`marker`) - AI/ML-enhanced processing optimized for academic papers with superior layout detection

### Emerging Requirements and Limitations

While the current implementation excels at PDF processing, several new requirements have emerged from user feedback and expanding use cases:

#### Current Gaps

1. **Limited File Format Support**: Current extractors only handle PDF files, but users frequently need to process:

   - Microsoft Office documents (Word, PowerPoint, Excel)
   - Images with text content (screenshots, scanned documents)
   - Audio files with speech content
   - Web content (HTML, URLs)
   - Structured data formats (CSV, JSON, XML)
   - Archive files (ZIP with mixed content)
   - E-books (EPUB format)

2. **Inconsistent Markdown Output**: While Marker produces excellent Markdown for PDFs, we lack a unified approach for converting other document types to the same high-quality Markdown format that's optimal for LLM consumption

3. **Multi-Modal Content Processing**: Need for handling documents with embedded media, OCR capabilities for images, and speech transcription for audio content

4. **Cloud Integration Capabilities**: Requirement for optional integration with cloud services like Azure Document Intelligence for enhanced accuracy

5. **Plugin Architecture**: Need for extensible document processing that can accommodate future format support without core code changes

### Why MarkItDown?

MarkItDown (https://github.com/microsoft/markitdown) is Microsoft's open-source utility specifically designed to convert various file formats to clean Markdown for LLM consumption. It addresses our multi-format processing gaps:

#### Key Advantages

1. **Comprehensive Format Support**: Native support for:

   - **Office Documents**: Word (DOCX), PowerPoint (PPTX), Excel (XLSX/XLS)
   - **PDF Files**: High-quality PDF to Markdown conversion
   - **Images**: OCR with EXIF metadata extraction
   - **Audio**: Speech transcription with metadata
   - **Web Content**: HTML parsing and YouTube transcription
   - **Data Formats**: CSV, JSON, XML with structure preservation
   - **Archives**: ZIP file iteration and content extraction
   - **E-books**: EPUB format support

2. **LLM-Optimized Output**: Specifically designed to produce Markdown that mainstream LLMs "natively speak" with:

   - Minimal markup while preserving document structure
   - Token-efficient formatting
   - Consistent heading hierarchies, lists, tables, and links

3. **Advanced Features**:

   - **Azure Document Intelligence**: Optional integration for premium accuracy
   - **LLM-Enhanced Descriptions**: Uses OpenAI models for intelligent image descriptions
   - **Plugin Architecture**: Extensible system for custom format converters
   - **OCR Capabilities**: Built-in text extraction from images
   - **Speech Processing**: Audio transcription for multimedia content

4. **Production-Ready**:
   - Lightweight with optional dependencies for specific formats
   - CLI and Python API support
   - Docker container available
   - Actively maintained by Microsoft AutoGen team

#### Performance Characteristics

- **Memory Efficient**: Processes files as streams without creating temporary files
- **Scalable**: Designed for batch processing workflows
- **Flexible**: Optional dependencies allow minimal installation for specific use cases
- **Robust**: Comprehensive error handling and fallback mechanisms

#### Technical Integration Benefits

1. **Complementary to Existing Stack**: Works alongside current PDF extractors without conflicts
2. **Unified Output Format**: All extractors can output consistent Markdown for downstream processing
3. **Future-Proof**: Plugin system allows adding new formats without core changes
4. **Cloud-Ready**: Optional Azure integration for enterprise deployments

## Decision

We will integrate MarkItDown as a **fourth extraction method** to provide comprehensive multi-format document processing capabilities, positioning it as the **"Universal/Multi-Format"** extraction method.

### Prerequisites: Architectural Refactoring

Before implementing MarkItDown integration, we must address the current architectural debt in the preprocessor module. The current `document_preprocessor.py` file has grown to **1,367 lines** and contains multiple extraction methods in a single monolithic file, which creates several issues:

#### Current Architectural Problems

1. **Code Maintainability**: Single file with multiple extraction implementations makes maintenance difficult
2. **Testing Complexity**: Hard to test individual extractors in isolation
3. **Dependency Management**: All extractor dependencies are loaded even when only one method is used
4. **Code Reusability**: Common functionality is tightly coupled with specific extractors
5. **Development Workflow**: Multiple developers working on different extractors create merge conflicts
6. **Performance Impact**: All extraction libraries are imported regardless of usage

#### Proposed Modular Architecture

We will refactor the preprocessor module into a clean, modular structure:

```
src/preprocessor/
├── __init__.py                     # Module interface
├── document_preprocessor.py        # Main orchestrator class (significantly reduced)
├── base.py                        # Base classes and common functionality
├── extractors/                    # Individual extractor implementations
│   ├── __init__.py
│   ├── base_extractor.py          # Abstract base extractor
│   ├── pypdf_extractor.py         # LangChain PyPDF implementation
│   ├── unstructured_extractor.py  # Unstructured.io implementation
│   ├── marker_extractor.py        # Marker implementation
│   └── markitdown_extractor.py    # MarkItDown implementation (new)
├── utils/                         # Shared utilities
│   ├── __init__.py
│   ├── performance_tracker.py     # Performance monitoring
│   ├── quality_analyzer.py        # Text quality analysis
│   └── metadata_extractor.py      # Metadata extraction utilities
└── models.py                      # Shared data models and types
```

#### Refactoring Benefits

1. **Separation of Concerns**: Each extractor is self-contained with its own dependencies
2. **Lazy Loading**: Dependencies only loaded when specific extractor is used
3. **Independent Testing**: Each extractor can be tested in isolation
4. **Parallel Development**: Multiple developers can work on different extractors without conflicts
5. **Plugin Architecture**: Easy to add new extractors without modifying existing code
6. **Performance Optimization**: Reduced memory footprint and startup time

### Implementation Strategy

#### Phase 0: Architectural Refactoring (Prerequisite)

Before integrating MarkItDown, we must refactor the current monolithic structure:

##### Step 1: Extract Base Classes and Utilities

```python
# src/preprocessor/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass
class ExtractionResult:
    """Result of document text extraction with performance and quality metrics."""
    text: str
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    method_specific_data: Dict[str, Any]

class BaseExtractor(ABC):
    """Abstract base class for all document extractors."""

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        pass

    @abstractmethod
    def extract(self, file_path: Path, **kwargs) -> ExtractionResult:
        """Extract text from the given file."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this extractor."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions."""
        pass
```

##### Step 2: Create Individual Extractor Classes

```python
# src/preprocessor/extractors/pypdf_extractor.py
from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

class PyPDFExtractor(BaseExtractor):
    """LangChain PyPDF-based PDF extractor."""

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            from langchain_community.document_loaders.parsers.pdf import PyPDFParser
            self.parser_class = PyPDFParser
        except ImportError:
            raise ImportError("LangChain dependencies not available for PyPDF extraction")

    @property
    def name(self) -> str:
        return "pypdf"

    @property
    def supported_formats(self) -> List[str]:
        return [".pdf"]

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_formats

    def extract(self, file_path: Path, track_performance: bool = True) -> ExtractionResult:
        """Extract text using LangChain PyPDF parser."""
        # Implementation moved from document_preprocessor.py
        pass
```

##### Step 3: Refactor Main DocumentPreprocessor

```python
# src/preprocessor/document_preprocessor.py (significantly reduced)
from typing import Dict, List, Optional, Type
from pathlib import Path

from .base import BaseExtractor, ExtractionResult
from .extractors.pypdf_extractor import PyPDFExtractor
from .extractors.unstructured_extractor import UnstructuredExtractor
from .extractors.marker_extractor import MarkerExtractor
from .extractors.markitdown_extractor import MarkItDownExtractor

class DocumentPreprocessor:
    """Main document preprocessor with pluggable extractors."""

    def __init__(self, raw_path: Optional[Path] = None, processed_path: Optional[Path] = None):
        self.raw_path = raw_path or DATA_RAW_PATH
        self.processed_path = processed_path or DATA_PROCESSED_PATH

        # Initialize available extractors with lazy loading
        self._available_extractors: Dict[str, Type[BaseExtractor]] = {
            'pypdf': PyPDFExtractor,
            'unstructured': UnstructuredExtractor,
            'marker': MarkerExtractor,
            'markitdown': MarkItDownExtractor,
        }
        self._loaded_extractors: Dict[str, BaseExtractor] = {}

    def get_extractor(self, method: str) -> BaseExtractor:
        """Get extractor instance with lazy loading."""
        if method not in self._loaded_extractors:
            if method not in self._available_extractors:
                raise ValueError(f"Unknown extraction method: {method}")

            try:
                self._loaded_extractors[method] = self._available_extractors[method]()
            except ImportError as e:
                raise ImportError(f"Dependencies for {method} extractor not available: {e}")

        return self._loaded_extractors[method]

    def detect_optimal_extractor(self, file_path: Path) -> str:
        """Recommend optimal extractor based on file type."""
        # Implementation for intelligent routing
        pass

    def extract_text_from_file(self, file_path: Path, method: str = "auto", **kwargs) -> ExtractionResult:
        """Extract text using specified or auto-detected method."""
        if method == "auto":
            method = self.detect_optimal_extractor(file_path)

        extractor = self.get_extractor(method)

        if not extractor.supports_format(file_path):
            raise ValueError(f"Extractor {method} does not support format {file_path.suffix}")

        return extractor.extract(file_path, **kwargs)
```

#### Method 4: MarkItDown (Universal/Multi-Format)

- **Library**: `markitdown[all]` (to be added to requirements.txt)
- **Positioning**: Universal document converter optimized for LLM-ready Markdown output
- **Use Case**: When processing non-PDF documents or when consistent Markdown output is required across all file types
- **Target Documents**: Office files, images, audio, web content, mixed archives, and PDFs requiring universal format consistency

#### Integration Architecture

```python
class MarkItDownExtractor:
    """MarkItDown-based multi-format extraction with performance tracking."""

    def __init__(self,
                 enable_plugins: bool = False,
                 llm_client: Optional[Any] = None,
                 llm_model: Optional[str] = None,
                 docintel_endpoint: Optional[str] = None):
        """Initialize MarkItDown converter with optional enhancements."""

    def extract_text(self, file_path: Path) -> ExtractionResult:
        """Extract text using MarkItDown with full performance metrics."""

    def supports_format(self, file_path: Path) -> bool:
        """Check if file format is supported by MarkItDown."""

    def extract_with_llm_enhancement(self, file_path: Path) -> ExtractionResult:
        """Extract with LLM-enhanced image descriptions."""

    def batch_extract(self, file_paths: List[Path]) -> List[ExtractionResult]:
        """Batch processing for multiple documents of various formats."""
```

#### Document Preprocessor Integration

Update `DocumentPreprocessor.SUPPORTED_METHODS` to include `markitdown`:

```python
# Updated supported extraction methods
SUPPORTED_METHODS = ['pypdf', 'unstructured', 'marker', 'markitdown']
```

### File Format Detection Strategy

Implement intelligent format detection and routing:

```python
def detect_optimal_extractor(self, file_path: Path) -> str:
    """Recommend optimal extractor based on file type and requirements."""

    file_extension = file_path.suffix.lower()

    # Route non-PDF files to MarkItDown
    if file_extension in ['.docx', '.pptx', '.xlsx', '.jpg', '.png', '.mp3', '.wav', '.html', '.epub']:
        return 'markitdown'

    # For PDFs, allow user choice or default to existing methods
    elif file_extension == '.pdf':
        return 'unstructured'  # or user preference

    # Fallback for unknown formats
    else:
        return 'markitdown'
```

## Implementation Requirements

### 0. Architectural Refactoring (Prerequisite)

#### Dependencies Reorganization

Each extractor will manage its own dependencies:

```python
# src/preprocessor/extractors/pypdf_extractor.py
try:
    from langchain_community.document_loaders.parsers.pdf import PyPDFParser
    from langchain_core.documents import Document
    from langchain_core.document_loaders import Blob
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# src/preprocessor/extractors/unstructured_extractor.py
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import Element
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

# src/preprocessor/extractors/marker_extractor.py
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

# src/preprocessor/extractors/markitdown_extractor.py
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
```

#### Migration Strategy

1. **Backward Compatibility**: Maintain existing API during transition
2. **Gradual Migration**: Move extractors one by one to new structure
3. **Deprecation Warnings**: Add warnings for direct method calls on old API
4. **Test Preservation**: Ensure all existing tests continue to pass

#### Shared Utilities Extraction

```python
# src/preprocessor/utils/performance_tracker.py
class PerformanceTracker:
    """Context manager for tracking performance metrics during extraction."""
    # Moved from document_preprocessor.py

# src/preprocessor/utils/quality_analyzer.py
class QualityAnalyzer:
    """Analyzer for assessing text extraction quality."""
    # Moved from document_preprocessor.py

# src/preprocessor/utils/metadata_extractor.py
class MetadataExtractor:
    """Utility for extracting metadata from filenames and documents."""
    # Moved from document_preprocessor.py
```

### 1. Core Integration (Post-Refactoring)

#### Dependencies

```python
# Add to requirements.txt
markitdown[all]>=0.1.3

# Optional cloud enhancement
# azure-ai-documentintelligence>=1.0.0  # For Azure Document Intelligence integration
```

#### Core Extractor Implementation

```python
# src/preprocessor/extractors/markitdown_extractor.py
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..base import BaseExtractor, ExtractionResult
from ..utils.performance_tracker import PerformanceTracker
from ..utils.quality_analyzer import QualityAnalyzer

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

class MarkItDownExtractor(BaseExtractor):
    """MarkItDown-based multi-format document extractor."""

    def __init__(self,
                 enable_plugins: bool = False,
                 llm_client: Optional[Any] = None,
                 llm_model: Optional[str] = None,
                 docintel_endpoint: Optional[str] = None):
        """Initialize MarkItDown extractor with optional enhancements."""
        if not MARKITDOWN_AVAILABLE:
            raise ImportError("MarkItDown is not available")

        self.enable_plugins = enable_plugins
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.docintel_endpoint = docintel_endpoint

    @property
    def name(self) -> str:
        return "markitdown"

    @property
    def supported_formats(self) -> List[str]:
        return [
            ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp",
            ".mp3", ".wav", ".html", ".epub", ".zip",
            ".csv", ".json", ".xml"
        ]

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_formats

    def extract(self, file_path: Path,
               track_performance: bool = True,
               enable_llm: bool = False) -> ExtractionResult:
        """Extract text using MarkItDown with performance tracking."""

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
                    "llm_enhanced": enable_llm,
                    "plugins_enabled": self.enable_plugins
                }
            )
```

### 2. Configuration Updates

#### Environment Variables

```bash
# Optional configuration for enhanced features
MARKITDOWN_ENABLE_PLUGINS=false
MARKITDOWN_LLM_MODEL=gpt-4o
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
```

#### Config Class Extensions

```python
# src/config.py additions
MARKITDOWN_ENABLE_PLUGINS = os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").lower() == "true"
MARKITDOWN_LLM_MODEL = os.getenv("MARKITDOWN_LLM_MODEL", "gpt-4o")
AZURE_DOC_INTEL_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
```

### 3. Enhanced CLI Support

#### Updated Method Selection

```python
# scripts/demo_preprocessing.py updates
parser.add_argument(
    "--method",
    choices=["pypdf", "unstructured", "marker", "markitdown"],
    default="unstructured",
    help="Extraction method to use"
)

parser.add_argument(
    "--auto-detect",
    action="store_true",
    help="Automatically select optimal extractor based on file type"
)

parser.add_argument(
    "--markitdown-llm",
    action="store_true",
    help="Enable LLM enhancement for MarkItDown (images/presentations)"
)
```

### 4. Testing Strategy

#### Refactoring Tests

```python
# tests/processor/test_extractors/test_base_extractor.py
class TestBaseExtractor:
    """Test suite for base extractor functionality."""

# tests/processor/test_extractors/test_pypdf_extractor.py
class TestPyPDFExtractor:
    """Test suite for PyPDF extractor."""

# tests/processor/test_extractors/test_unstructured_extractor.py
class TestUnstructuredExtractor:
    """Test suite for Unstructured extractor."""

# tests/processor/test_extractors/test_marker_extractor.py
class TestMarkerExtractor:
    """Test suite for Marker extractor."""

# tests/processor/test_extractors/test_markitdown_extractor.py
class TestMarkItDownExtractor:
    """Test suite for MarkItDown extractor."""

    def test_pdf_extraction(self):
        """Test PDF processing with MarkItDown."""

    def test_office_document_extraction(self):
        """Test Word/PowerPoint/Excel processing."""

    def test_image_ocr_extraction(self):
        """Test image OCR capabilities."""

    def test_audio_transcription(self):
        """Test audio file transcription."""

    def test_unsupported_format_handling(self):
        """Test graceful handling of unsupported formats."""

    def test_llm_enhancement_integration(self):
        """Test LLM-enhanced extraction features."""
```

#### Integration Tests

```python
# tests/processor/test_document_preprocessor_refactored.py
class TestDocumentPreprocessorRefactored:
    """Test the refactored DocumentPreprocessor with modular extractors."""

    def test_extractor_lazy_loading(self):
        """Test that extractors are loaded only when needed."""

    def test_format_detection_routing(self):
        """Test automatic format detection and extractor routing."""

    def test_comparative_extraction_methods(self):
        """Compare extraction results across different methods."""

    def test_backward_compatibility(self):
        """Ensure refactored API maintains backward compatibility."""

    def test_dependency_isolation(self):
        """Test that missing dependencies only affect specific extractors."""
```

## Benefits

### 1. Architectural Improvements

- **Modular Design**: Clean separation of concerns with each extractor as an independent module
- **Maintainability**: Reduced complexity with focused, single-responsibility classes
- **Testability**: Independent testing of extractors without cross-contamination
- **Performance**: Lazy loading of dependencies reduces memory footprint and startup time
- **Developer Experience**: Parallel development on different extractors without merge conflicts

### 2. Expanded Capabilities

- **Universal Format Support**: Process documents beyond PDFs including Office files, images, audio, and web content
- **Consistent Output**: Unified Markdown format across all document types optimized for LLM consumption
- **Future-Proof Architecture**: Plugin system allows adding new formats without core changes

### 2. Enhanced User Experience

- **Simplified Workflow**: Single tool for processing diverse document collections
- **Intelligent Routing**: Automatic selection of optimal extractor based on file type
- **Rich Media Handling**: OCR for images, transcription for audio, enhanced descriptions via LLM

### 3. Technical Advantages

- **Complementary Integration**: Works alongside existing PDF extractors without conflicts
- **Memory Efficient**: Stream-based processing without temporary files
- **Cloud-Ready**: Optional Azure Document Intelligence integration for enterprise use

### 4. Strategic Positioning

- **Microsoft Ecosystem**: Leverages Microsoft's investment in document processing and AutoGen
- **LLM Optimization**: Purpose-built for modern AI workflows and token efficiency
- **Open Source**: Transparent, actively maintained, and extensible

## Risks and Mitigations

### 1. Refactoring Risks

**Risk**: Breaking existing functionality during architectural refactoring
**Mitigation**:

- Maintain backward compatibility during transition period
- Comprehensive test coverage before and after refactoring
- Gradual migration with deprecation warnings
- Feature flags to enable/disable new architecture

### 2. Dependency Management

**Risk**: Additional dependencies and potential conflicts
**Mitigation**:

- Use optional dependencies with feature flags
- Comprehensive testing across dependency combinations
- Fallback mechanisms for missing dependencies

### 2. Performance Considerations

**Risk**: Performance impact for simple PDF processing
**Mitigation**:

- Keep existing PDF extractors as optimized options
- Performance benchmarking and comparison
- User choice in extractor selection

### 3. Output Consistency

**Risk**: Different Markdown formatting across extractors
**Mitigation**:

- Standardized post-processing pipeline
- Configurable output formatting
- Comprehensive quality metrics

## Success Criteria

1. **Functional Integration**: MarkItDown successfully processes all supported file formats with error handling
2. **Performance Benchmarks**: Processing times and memory usage within acceptable ranges compared to format-specific tools
3. **Quality Metrics**: Markdown output quality meets or exceeds existing PDF extractors for PDF files
4. **User Adoption**: Positive feedback on multi-format processing capabilities
5. **Test Coverage**: Comprehensive test suite covering all supported formats and edge cases

## Implementation Timeline

### Phase 0: Architectural Refactoring (Week 1-3)

- **Week 1**: Extract base classes and shared utilities
- **Week 2**: Create individual extractor classes with dependency isolation
- **Week 3**: Refactor main DocumentPreprocessor class and ensure backward compatibility

### Phase 1: MarkItDown Integration (Week 4-5)

- Add MarkItDown dependency and basic extractor implementation
- Implement format detection and routing logic
- Basic CLI integration and testing

### Phase 2: Enhanced Features (Week 6-7)

- LLM enhancement integration
- Advanced format detection and routing logic
- Comprehensive test suite development for all extractors

### Phase 3: Production Readiness (Week 8-9)

- Performance optimization and benchmarking across all extractors
- Documentation updates and examples
- Azure Document Intelligence integration (optional)
- Migration guide and deprecation timeline

## Conclusion

Integrating MarkItDown as the fourth extraction method will significantly expand our document processing capabilities while maintaining the quality and performance of our existing PDF-focused extractors. This addition positions our system as a comprehensive document processing solution capable of handling diverse file formats with consistent, LLM-optimized output.

The complementary nature of MarkItDown ensures that users can choose the optimal extractor for their specific needs:

- **pypdf**: Fast baseline PDF extraction
- **unstructured**: Structure-aware PDF processing
- **marker**: AI-enhanced academic paper processing
- **markitdown**: Universal multi-format processing with LLM-optimized output

This multi-extractor approach provides flexibility, redundancy, and specialized optimization for different use cases while maintaining a unified API and output format.
