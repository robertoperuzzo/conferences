# ADR-006: Standardization of PDF Text Extraction Methods with Performance and Quality Comparison

## Status

Proposed

## Context

The current document preprocessing implementation in `src/preprocessor/document_preprocessor.py` includes multiple PDF extraction methods:

### Current Implementation

1. **Unstructured.io** - Recently implemented as default, provides document structure and excellent OCR correction
2. **pdfplumber** - Currently used as fallback, good for simple text extraction
3. **PyMuPDF (fitz)** - Currently used as fallback, fast but basic
4. **PyPDF** - Currently used as fallback, simple and lightweight

### Problems with Current Approach

1. **Maintenance Complexity**: Multiple extraction libraries with inconsistent APIs
2. **No Performance Metrics**: No systematic comparison of processing speed
3. **No Quality Metrics**: No objective quality assessment between methods
4. **Manual OCR Fixing**: Complex `_fix_ocr_artifacts()` method duplicated across multiple extractors
5. **Inconsistent Fallback Logic**: Complex fallback chains that are hard to debug

## Proposed Solution

Standardize on exactly **three PDF extraction methods** with clear positioning and systematic evaluation:

### Method 1: PyPDF (Baseline/Raw)

- **Library**: `PyPDF` (already in requirements)
- **Positioning**: Fastest, completely raw extraction with no OCR fixing
- **Use Case**: Demonstrate baseline quality without any enhancement
- **Known Limitations**:
  - Struggles with complex layouts
  - No image/table extraction
  - No OCR artifact correction
  - May produce poor quality with scanned PDFs
  - Character spacing issues remain unfixed
- **Design Decision**: **No OCR fixing applied** - Shows raw extraction quality to demonstrate the performance vs. quality trade-off

### Method 2: LangChain PyPDFParser (Balanced)

- **Library**: `langchain-community.document_loaders.parsers.pdf.PyPDFParser`
- **Positioning**: Balanced approach with LangChain ecosystem integration
- **Use Case**: Integration with LangChain workflows, moderate quality needs
- **Benefits**:
  - Native LangChain Document objects
  - Metadata extraction capabilities
  - Consistent with chunking strategies that use LangChain
  - Better than PyPDF for complex layouts

### Method 3: Unstructured.io (Premium/Structured)

- **Library**: `unstructured[pdf]` (already implemented)
- **Positioning**: Highest quality, structure-aware extraction
- **Use Case**: When text quality and document structure are critical
- **Benefits**:
  - Advanced OCR correction
  - Document structure detection (titles, headers, paragraphs)
  - Table and image handling
  - Element-based processing

## Implementation Requirements

### 1. Performance Tracking

Each extraction method must track:

```python
{
    "processing_time_seconds": float,
    "memory_usage_mb": float,  # Peak memory during processing
    "characters_extracted": int,
    "pages_processed": int,
    "extraction_rate": float,  # chars/second
}
```

### 2. Quality Assessment Metrics

Each extraction method must provide:

```python
{
    "text_length": int,
    "word_count": int,
    "unique_words": int,
    "readability_score": float,  # Based on sentence structure
    "ocr_artifact_count": int,  # Estimated artifacts remaining
    "structure_elements": int,  # Headers, titles detected (where applicable)
}
```

### 3. Unified API

All three methods must conform to a consistent interface:

```python
def _extract_with_[method](self, pdf_path: Path,
                          track_performance: bool = True) -> ExtractionResult:
    """Extract text with performance and quality tracking."""

class ExtractionResult:
    text: str
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    method_specific_data: Dict[str, Any]  # Elements for Unstructured, etc.
```

### 4. Comparative Analysis

The system must provide:

- Side-by-side comparison of all three methods on the same document
- Performance benchmarking across document types
- Quality scoring with objective metrics
- Automatic method recommendation based on use case

## Detailed Implementation Plan

### Phase 1: Method Standardization

#### 1.1 Remove Deprecated Methods and Clean Legacy Code

**Methods to Remove Completely:**

- Remove `_extract_with_pdfplumber()` - Replace with LangChain PyPDFParser
- Remove `_extract_with_pymupdf()` - Not needed in new three-method approach
- **Remove `_fix_ocr_artifacts()` method** - Keep pypdf completely raw to demonstrate quality vs. performance trade-offs
- Update PyPDF method to return raw extraction without any OCR correction

**Cleanup Legacy Dependencies:**

- Remove `import pdfplumber` from imports
- Remove `import pymupdf` from imports
- Clean up any references to the old methods in docstrings and comments
- Update method validation logic to only accept the three new methods

**Fallback Logic Changes:**

- Remove complex fallback chains between deprecated methods
- Implement simple fallback: `unstructured` → `langchain` → `PyPDF`
- Log deprecation warnings for users still calling old method names

#### 1.2 Implement Directory Structure

```python
def _get_method_output_path(self, method: str) -> Path:
    """Get output directory for specific extraction method."""
    method_dir = self.processed_path / method
    method_dir.mkdir(parents=True, exist_ok=True)
    return method_dir

def _generate_output_filename(self, pdf_path: Path) -> str:
    """Generate filename based on original PDF name and timestamp."""
    import re
    from datetime import datetime

    # Convert original filename to lowercase, remove spaces and special chars
    original_name = pdf_path.stem.lower()
    clean_name = re.sub(r'[^a-z0-9]', '', original_name)

    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{clean_name}_{timestamp}.json"
```

#### 1.3 Implement PyPDF Method (Raw/No OCR Fixing)

```python
def _extract_with_pypdf(self, pdf_path: Path,
                        track_performance: bool = True) -> ExtractionResult:
    """Raw PyPDF extraction with NO OCR fixing - demonstrates baseline quality."""
```

#### 1.4 Implement LangChain PyPDFParser Method

```python
def _extract_with_langchain(self, pdf_path: Path,
                           track_performance: bool = True) -> ExtractionResult:
    """LangChain PyPDFParser extraction with Document objects."""
```

#### 1.5 Enhance Unstructured Method

- Add performance tracking to existing implementation
- Add quality metrics calculation
- Ensure consistent return format

### Phase 2: Performance and Quality Tracking

#### 2.1 Performance Monitoring

```python
class PerformanceTracker:
    def __init__(self):
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        # Start tracking

    def __exit__(self):
        # Calculate metrics
```

#### 2.2 Quality Assessment

```python
class QualityAnalyzer:
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        return {
            "readability_score": ...,
            "ocr_artifact_count": ...,
            "structure_quality": ...,
        }
```

### Phase 3: Comparative Analysis

#### 3.1 Benchmarking Suite

```python
class ExtractionBenchmark:
    def compare_all_methods(self, pdf_path: Path) -> ComparisonResult:
        """Compare all three methods on the same document."""

    def benchmark_performance(self, documents: List[Path]) -> BenchmarkReport:
        """Performance benchmark across document corpus."""
```

#### 3.2 Method Selection Logic

```python
def recommend_extraction_method(self,
                               use_case: str,
                               performance_priority: float,
                               quality_priority: float) -> str:
    """Recommend best method based on requirements."""
```

## Output Directory Structure

To enable easy comparison between extraction methods, processed documents will be organized into method-specific subdirectories:

```
data/processed/
├── pypdf/
│   └── <original_lowercase_without_spaces_and_specialchars_only_underscores>.json
├── langchain/
│   └── <original_lowercase_without_spaces_and_specialchars_only_underscores>.json
├── unstructured/
│   └── <original_lowercase_without_spaces_and_specialchars_only_underscores>.json
└── comparative_analysis/
    └── comparison_report_YYYYMMDD_HHMMSS.json
```

### Benefits of Separate Directories

1. **Direct Comparison**: Easy side-by-side comparison of JSON outputs
2. **Quality Assessment**: Visual inspection of text quality differences
3. **Performance Isolation**: Each method's outputs are clearly separated
4. **Historical Tracking**: Multiple processing runs can be compared over time
5. **Debugging**: Issues with specific methods can be isolated quickly

### Filename Convention

Each processed document follows the naming pattern:

- **Format**: `<original_lowercase_without_spaces_and_specialchars_only_underscores>.json`
- **Original**: Derived from the source PDF filename, converted to lowercase with spaces and special characters removed

**Examples**:

- `9308101_Dynamic Backtracking.pdf` → `9308101_dynamic_backtracking.json`
- `A Market-Oriented Programming Environment.pdf` → `a_market_oriented_programming_environment.json`

### Comparative Analysis Directory

The `comparative_analysis/` folder serves specific purposes:

- **Cross-method Reports**: Aggregate comparison data across all three extraction methods
- **Performance Benchmarks**: Processing speed and memory usage comparisons
- **Quality Metrics Summary**: Side-by-side quality assessment reports
- **Method Recommendations**: Automated suggestions based on document characteristics
- **Historical Analysis**: Trend analysis across multiple processing runs

### Quality Improvements Expected

1. **Raw vs. Enhanced Comparison**: Clear demonstration of PyPDF raw quality vs. Unstructured.io enhanced quality
2. **Objective Metrics**: Quantified comparison instead of subjective assessment
3. **Method Selection**: Data-driven choice based on use case requirements
4. **Output Separation**: Easy comparison via separate JSON files per method

### Performance Characteristics (Estimated)

1. **PyPDF**: ~3-5x faster than Unstructured, raw baseline quality with OCR artifacts
2. **LangChain**: ~1.5-3x faster than Unstructured, good quality with LangChain ecosystem benefits
3. **Unstructured**: Slowest but highest quality with structure awareness and OCR correction

## Expected Outcomes

### Developer Experience

1. **Simplified API**: Three clear choices instead of complex fallback chains
2. **Performance Insights**: Visibility into processing characteristics
3. **Quality Feedback**: Understanding of extraction quality trade-offs

## Migration Strategy

### Backward Compatibility

1. **Default Method**: Keep "unstructured" as default for highest quality
2. **Method Names**: Map old method names to new standardized methods:
   - `"pdfplumber"` → `"langchain"` (with deprecation warning)
   - `"pymupdf"` → `"langchain"` (with deprecation warning)
   - `"pypdf"` → `"pypdf"` (raw version, no OCR fixing)
   - `"unstructured"` → `"unstructured"` (enhanced with metrics)

### Gradual Migration

1. **Phase 1**: Add new methods alongside existing ones, add deprecation warnings
2. **Phase 2**: Remove deprecated method implementations but keep compatibility layer
3. **Phase 3**: **Complete removal of deprecated methods and cleanup**:
   - Remove `_extract_with_pdfplumber()` and `_extract_with_pymupdf()` methods
   - Remove `pdfplumber` and `pymupdf` import statements
   - Remove `_fix_ocr_artifacts()` method entirely
   - Clean up all references to deprecated methods
   - Update documentation to reflect only the three supported methods

### Legacy Code Cleanup Strategy

**Files to Modify:**

- `src/preprocessor/document_preprocessor.py`: Remove deprecated extraction methods
- `requirements.txt`: Consider removing `pdfplumber` and `pymupdf` dependencies
- Documentation: Update all references to use only the three new methods

**Breaking Changes:**

- Direct calls to `_extract_with_pdfplumber()` or `_extract_with_pymupdf()` will raise exceptions
- `_fix_ocr_artifacts()` method will no longer be available
- Raw PyPDF output will contain OCR artifacts (by design)

## Testing Strategy

### Unit Tests

- Each extraction method with sample PDFs
- Performance tracking accuracy
- Quality metrics calculation

### Integration Tests

- Comparative analysis across methods
- Benchmarking suite functionality
- Method recommendation logic

### Performance Tests

- Processing speed benchmarks
- Memory usage profiling
- Scalability testing with large documents

## Risks and Mitigations

### Risks

1. **LangChain Dependency**: Adding new dependency
2. **Performance Overhead**: Metrics collection may slow processing
3. **Quality Metrics**: Subjective nature of "quality" assessment
4. **Breaking Changes**: API modifications for existing users

### Mitigations

1. **Dependencies**: LangChain already in requirements.txt
2. **Performance**: Make metrics tracking optional via parameter
3. **Quality**: Use objective, measurable criteria where possible
4. **Compatibility**: Maintain backward compatibility during transition

## Success Criteria

1. **Three Methods Only**: Exactly PyPDF, LangChain, and Unstructured.io
2. **Performance Data**: All methods provide processing time and memory metrics
3. **Quality Metrics**: Objective quality scores for text extraction
4. **Comparative Analysis**: Side-by-side comparison functionality
5. **No Regression**: Existing functionality preserved during migration
6. **Documentation**: Clear guidance on method selection for different use cases

## Decision Timeline

- **Discussion Period**: 2 days for feedback and refinement
- **Implementation Start**: After approval
- **Completion Target**: 2 weeks from approval
- **Migration Complete**: 4 weeks from approval

---

**Questions for Discussion:**

1. Are the three selected methods (PyPDF, LangChain, Unstructured.io) the right choice?
2. What additional performance/quality metrics would be valuable?
3. Should we maintain any existing methods during transition?
4. What are the most important quality metrics for your use case?
5. How important is processing speed vs. text quality for your applications?

---

_This ADR proposes a systematic approach to PDF extraction standardization with data-driven method selection based on performance and quality metrics._
