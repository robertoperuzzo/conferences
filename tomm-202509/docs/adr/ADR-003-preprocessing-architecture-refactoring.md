# ADR-003: Preprocessing Architecture Refactoring to Generic Document Processor

## Date

2025-08-27

## Status

Accepted

## Context

The original `ArxivPreprocessor` violated the separation of concerns principle by combining downloading and processing responsibilities in a single class. This architectural issue made it difficult to:

- Process documents from different sources (ArXiv, PubMed, local files)
- Use different downloaders with the same processor
- Test downloading and processing separately
- Maintain clean, modular code
- Extend the system to handle multiple document sources

The user identified this architectural problem and requested: "I prefer to implement a generic preprocessor instead of a specialized for arxiv, because we can implement different downloaders from different sources and put all the documents in the `data/raw` folder. Then the preprocessor processes the PDF whatever is the source."

## Decision

We refactored the preprocessing architecture to implement a clean separation of concerns:

### New Architecture:

```
Old Architecture (❌ Coupled):
ArxivPreprocessor
├── download_arxiv_papers()     # Download responsibility
├── process_papers()            # Processing responsibility
└── save_processed_papers()     # Storage responsibility

New Architecture (✅ Separated):
src/downloader/
├── arxiv_downloader.py
└── __init__.py

src/preprocessor/
```

### Core Components:

1. **Generic DocumentPreprocessor Class** (`src/preprocessor/document_preprocessor.py`)

   - Source-agnostic PDF processing for any document type
   - Auto-discovery of documents in `data/raw/` directory
   - Smart metadata extraction from filenames with pattern recognition
   - Multiple PDF extraction methods with automatic fallbacks
   - Comprehensive processing statistics and analytics
   - Rich progress tracking and professional console output

2. **Specialized Downloaders** (maintained separately)

   - ArXiv downloader handles ArXiv API specifics
   - Future downloaders for PubMed, Google Scholar, local files
   - Each downloader places files in standardized `data/raw/` location

3. **Migration Strategy**
   - Deprecated ArxivPreprocessor with backward compatibility wrapper
   - Clear deprecation warnings guide users to new approach
   - New demonstration script shows recommended workflow

### Key Features:

- **Source Agnostic**: Processes PDFs regardless of origin
- **Metadata Flexibility**: Handles any document metadata structure
- **Fallback Extraction**: Multiple PDF extraction methods with automatic fallbacks
- **Rich User Experience**: Professional console output with progress tracking
- **Configuration Integration**: Uses existing config system for paths
- **Extensible Design**: Easy to add new document sources without changing processor

### Workflow Integration:

```
data/raw/           # Documents from ANY source
    ├── arxiv_paper.pdf      # From ArXiv downloader
    ├── pubmed_paper.pdf     # From PubMed downloader
    └── local_paper.pdf      # From manual upload
           ↓
    Generic DocumentPreprocessor
           ↓
data/processed/     # Uniform processed JSON
    └── processed_documents.json
```

## Consequences

### What becomes easier:

- **Multi-Source Processing**: Handle documents from ArXiv, PubMed, local files with single processor
- **Modular Development**: Download and processing components can be developed/tested independently
- **Code Reusability**: Generic processor works with any PDF source
- **System Extension**: Adding new document sources doesn't require processor changes
- **Testing**: Can test downloading and processing logic separately
- **Maintenance**: Single responsibility principle makes components easier to maintain

### What becomes more difficult:

- **Initial Complexity**: More files and components to understand initially
- **Coordination**: Need to ensure downloaders and processor work together correctly
- **Migration**: Existing code using old ArxivPreprocessor needs to be updated

### Long-term Benefits:

- **Scalability**: Easy to add new document sources (PubMed, Google Scholar, etc.)
- **Maintainability**: Clean separation of concerns reduces coupling
- **Testability**: Independent components enable focused testing
- **Flexibility**: Can mix documents from multiple sources in single processing run
- **Professional Architecture**: Follows industry best practices for modular design

### Migration Path:

- **Backward Compatibility**: Old ArxivPreprocessor still works with deprecation warnings
- **Clear Documentation**: Migration guide helps users adopt new approach
- **Demonstration Scripts**: New demo shows recommended workflow

The refactoring successfully addresses the architectural concerns while maintaining backward compatibility and significantly improving the system's modularity and extensibility for handling documents from multiple sources.
