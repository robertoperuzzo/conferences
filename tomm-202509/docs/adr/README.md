# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records for the Chunking Strategies Demo project. ADRs document important architectural and design decisions made during the development process.

## ADR Index

| ADR                                                                  | Title                                                                | Date       | Status   |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------- | -------- |
| [ADR-001](ADR-001-arxiv-download-implementation.md)                  | ArXiv Paper Download Implementation                                  | 2025-08-27 | Accepted |
| [ADR-002](ADR-002-preprocessing-pipeline-implementation.md)          | ArXiv Preprocessing Pipeline Implementation                          | 2025-08-27 | Accepted |
| [ADR-003](ADR-003-preprocessing-architecture-refactoring.md)         | Preprocessing Architecture Refactoring to Generic Document Processor | 2025-08-27 | Accepted |
| [ADR-004](ADR-004-unit-testing-implementation.md)                    | Unit Testing Implementation with pytest Framework                    | 2025-08-27 | Accepted |
| [ADR-005](ADR-005-unstructured-io-integration.md)                    | Unstructured.io Integration for Enhanced Document Processing         | 2025-08-27 | Accepted |
| [ADR-006](ADR-006-pdf-extraction-standardization.md)                 | PDF Extraction Method Standardization                                | 2025-08-27 | Accepted |
| [ADR-007](ADR-007-remove-redundant-pypdf-method.md)                  | Remove Redundant PyPDF Extraction Method                             | 2025-08-28 | Accepted |
| [ADR-008](ADR-008-marker-integration-for-enhanced-pdf-processing.md) | Integration of Marker Library for Enhanced PDF Processing            | 2025-08-28 | Accepted |
| [ADR-009](ADR-009-chunking-strategies-prototype-implementation.md)   | Chunking Strategies Prototype Implementation and Component Testing   | 2025-08-28 | Proposed |
| [ADR-010](ADR-010-typesense-vector-indexing-implementation.md)       | Typesense Vector Indexing Implementation                             | 2025-08-28 | Accepted |
| [ADR-011](ADR-011-markitdown-multi-format-document-extraction.md)    | MarkItDown Integration with Modular Architecture Refactoring         | 2025-09-04 | Accepted |

## ADR Template

We use the following template for all ADRs:

```markdown
# Title

## Date

## Status

What is the status, such as proposed, accepted, rejected, deprecated, superseded, etc.?

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

## Decision Flow

The ADRs represent the evolution of the preprocessing system:

1. **ADR-001**: Established ArXiv paper download capabilities with async processing
2. **ADR-002**: Implemented comprehensive preprocessing pipeline for text extraction
3. **ADR-003**: Refactored to generic document processor following separation of concerns
4. **ADR-004**: Added comprehensive unit testing with pytest framework
5. **ADR-005**: Integrated Unstructured.io for enhanced document processing capabilities
6. **ADR-006**: Standardized PDF extraction methods with performance vs quality trade-offs
7. **ADR-007**: Removed redundant PyPDF method, keeping LangChain PyPDFParser
8. **ADR-008**: Integrated Marker library for AI/ML-enhanced PDF processing
9. **ADR-009**: (Proposed) Chunking strategies prototype implementation for comparative analysis
10. **ADR-010**: Implemented Typesense vector indexing for semantic search capabilities
11. **ADR-011**: **Major architectural refactoring** - Modular extractor architecture with MarkItDown integration

Each decision builds upon previous ones while addressing specific architectural needs and user feedback.
