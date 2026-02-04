# ADR-005: Integration of Unstructured.io for Enhanced Document Processing

## Status

Accepted

## Context

The current document preprocessing implementation in `src/preprocessor/document_preprocessor.py` faces several challenges:

### Current Implementation Issues

1. **Manual OCR Artifact Handling**: The `_fix_ocr_artifacts()` method uses regex patterns to fix common OCR issues like "JournalofArti(cid:12)cialIntelligenceResearch" → "Journal of Artificial Intelligence Research". This approach is:

   - Fragile and incomplete
   - Requires constant maintenance as new patterns are discovered
   - Cannot handle complex OCR corruption effectively

2. **Multiple PDF Libraries with Fallback Logic**: Currently uses three different PDF processing libraries:

   - `pdfplumber`
   - `PyMuPDF` (fitz)
   - `PyPDF`

   This creates complexity in maintenance and inconsistent results across different extraction methods.

3. **Limited Document Structure Awareness**: The current implementation treats documents as flat text, losing important structural information like:

   - Titles and headings
   - Paragraphs vs. captions
   - Tables and figures
   - Reading order

4. **Basic Metadata Extraction**: Only extracts filename-based metadata, missing rich document properties that could be useful for chunking strategies.

### Why Unstructured.io?

Unstructured.io is already included in our `requirements.txt` as `unstructured[pdf]` and provides:

1. **Advanced OCR Correction**: Built-in text cleaning and OCR artifact correction
2. **Document Structure Detection**: Identifies document elements (titles, paragraphs, tables, lists)
3. **Element-based Processing**: Each document component is processed separately with type information
4. **Unified API**: Single interface replacing multiple PDF processing libraries
5. **Rich Metadata**: Enhanced metadata extraction including element hierarchy and positioning
6. **Better Table Handling**: Improved extraction of tabular data
7. **Extensibility**: Supports various document formats beyond PDF

## Decision

We will refactor the `DocumentPreprocessor` class to use Unstructured.io as the primary document processing engine while maintaining backward compatibility.

## Implementation Plan

### Phase 1: Core Refactoring

1. **Replace PDF Extraction Methods**:

   - Add new `_extract_with_unstructured()` method using `partition_pdf()`
   - Make Unstructured.io the default extraction method
   - Keep existing methods as fallback options for compatibility

2. **Remove Manual OCR Fixing**:

   - Deprecate the `_fix_ocr_artifacts()` method
   - Let Unstructured.io handle OCR correction internally

3. **Enhance Output Format**:
   - Add optional element-based output alongside current flat text format
   - Include document structure information (element types, hierarchy)
   - Maintain backward compatibility with existing JSON schema

### Phase 2: Enhanced Features

1. **Document Structure Preservation**:

   - Add element type information (title, paragraph, table, list)
   - Include hierarchical relationships between elements
   - Preserve reading order and document flow

2. **Improved Metadata Extraction**:

   - Extract document properties beyond filename parsing
   - Include page-level information for each element
   - Add confidence scores where available

3. **Table and Figure Detection**:
   - Better handling of tabular data
   - Image and figure detection capabilities
   - Structured data extraction from tables

### Phase 3: Integration with Chunking Strategies

1. **Element-aware Chunking**:
   - Enable chunking strategies to use document structure
   - Respect element boundaries in chunking decisions
   - Provide element-type metadata to chunking algorithms

## Technical Implementation Details

### New Method Signature

```python
def _extract_with_unstructured(self, pdf_path: Path,
                             strategy: str = "auto",
                             extract_images: bool = False) -> Dict[str, Any]:
    """Extract text and structure using Unstructured.io.

    Args:
        pdf_path: Path to PDF file
        strategy: Processing strategy ("auto", "fast", "ocr_only", "hi_res")
        extract_images: Whether to extract and process images

    Returns:
        Dictionary with elements, metadata, and optionally flat text
    """
```

### Enhanced Output Schema

```json
{
  "file_name": "document.pdf",
  "file_path": "/path/to/document.pdf",
  "source": "arxiv",
  "title": "Document Title",
  "full_text": "Combined text content...",
  "elements": [
    {
      "type": "Title",
      "text": "Document Title",
      "page_number": 1,
      "element_id": "elem_1",
      "metadata": {...}
    },
    {
      "type": "NarrativeText",
      "text": "Paragraph content...",
      "page_number": 1,
      "element_id": "elem_2",
      "metadata": {...}
    }
  ],
  "extraction_method": "unstructured",
  "processing_strategy": "auto",
  "word_count": 5000,
  "element_count": 45,
  "processed_at": "2025-08-27T..."
}
```

### Backward Compatibility

- Existing `full_text` field will remain for compatibility
- Current API methods (`process_document`, `process_documents`) unchanged
- Fallback to existing PDF libraries if Unstructured.io fails
- Configuration option to disable element-based processing

## Benefits

1. **Improved Text Quality**: Better OCR correction without manual pattern maintenance
2. **Rich Document Understanding**: Structure-aware processing enables better chunking
3. **Reduced Complexity**: Single library instead of three PDF processors
4. **Future-proofing**: Foundation for advanced document analysis features
5. **Better Debugging**: Element-level information helps identify processing issues
6. **Enhanced Chunking**: Document structure can inform chunking strategies

## Risks and Mitigations

### Risks

1. **Performance Impact**: Unstructured.io may be slower than simple text extraction
2. **Dependency Risk**: Adding dependency on external library behavior
3. **Output Format Changes**: Element-based output may require adaptation in downstream code
4. **Memory Usage**: Structured processing may use more memory

### Mitigations

1. **Performance**:

   - Keep fast fallback options available
   - Add configuration for processing strategies (fast vs. high-quality)
   - Cache processing results

2. **Dependency Management**:

   - Maintain fallback to existing PDF libraries
   - Pin Unstructured.io version in requirements
   - Add comprehensive error handling

3. **Compatibility**:

   - Make element-based output optional
   - Preserve existing `full_text` format
   - Add feature flags for gradual migration

4. **Resource Management**:
   - Add memory monitoring
   - Implement batch processing limits
   - Provide configuration options for resource usage

## Testing Strategy

1. **Unit Tests**: Test Unstructured.io integration with sample PDFs
2. **Regression Tests**: Ensure existing functionality still works
3. **Performance Tests**: Compare processing speed and memory usage
4. **Quality Tests**: Validate OCR correction improvements
5. **Integration Tests**: Test with downstream chunking strategies

## Migration Path

1. **Phase 1**: Implement Unstructured.io extraction as optional method
2. **Phase 2**: Make it default with fallback to existing methods
3. **Phase 3**: Add element-based features for advanced use cases
4. **Phase 4**: Deprecate manual OCR fixing methods

## Success Criteria

1. Better text quality in processed documents (fewer OCR artifacts)
2. Maintained or improved processing performance
3. Successful backward compatibility
4. Enhanced document structure information available for chunking
5. Reduced maintenance burden for OCR pattern management

## Decision Date

2025-08-27

## Participants

- System Architecture Team
- Document Processing Team
- Chunking Strategy Team

---

_This ADR documents the decision to integrate Unstructured.io for enhanced document processing capabilities while maintaining system reliability and backward compatibility._
