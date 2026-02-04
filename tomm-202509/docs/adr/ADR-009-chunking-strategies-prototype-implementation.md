# ADR-009: Chunking Strategies Prototype Implementation and Component Testing

## Status

Proposed

## Context

Following the successful implementation of the document preprocessing pipeline (ADR-002, ADR-003, ADR-005, ADR-006, ADR-007, ADR-008), we now need to implement the core chunking strategies module as outlined in the Demo Implementation Plan. This is the critical next phase that will enable comparative analysis of different chunking approaches for RAG applications.

### Current State

The preprocessing system is complete and operational:

- **ArXiv Paper Download**: Functional downloader with async processing (ADR-001)
- **Document Processing**: Generic document processor with pypdf (LangChain) and Unstructured.io methods (ADR-002, ADR-005)
- **Architecture**: Clean separation of concerns with modular design (ADR-003)
- **Testing**: Comprehensive test coverage with pytest framework (ADR-004)
- **PDF Processing**: Standardized extraction methods for optimal quality vs performance trade-offs (ADR-006, ADR-007)

### Implementation Requirements

Per the Demo Implementation Plan, we need to implement **4 distinct chunking strategies** for comparative analysis:

1. **Fixed-size blocks**: Token-aware splitting using `TokenTextSplitter` (512 or 1024 tokens) - simple and fast baseline
2. **Sliding windows (LangChain)**: Document-structure aware splitting using `RecursiveCharacterTextSplitter` with overlap
3. **Sliding windows (Unstructured)**: Element-based chunking using Unstructured's document elements with custom overlap implementation
4. **Semantic chunking**: Natural breakpoint identification using `SemanticChunker` for meaning-preserving chunks

### Technical Challenges

1. **Integration Complexity**: Each strategy requires different input formats and preprocessing approaches
2. **Configuration Management**: Multiple parameters per strategy (chunk size, overlap, semantic thresholds) need systematic management
3. **Performance Optimization**: Large document processing requires efficient batching and memory management
4. **Quality Evaluation**: Need consistent metrics across all strategies for meaningful comparison
5. **Element-Based Processing**: Unstructured sliding windows require custom overlap logic since native overlap isn't available
6. **Semantic Dependency**: SemanticChunker requires embedding models and similarity calculations

### Architectural Considerations

The chunking module must:

- **Be Strategy-Agnostic**: Support multiple chunking approaches without tight coupling
- **Preserve Metadata**: Maintain document metadata and chunk provenance throughout processing
- **Enable Comparison**: Generate consistent output formats for downstream evaluation
- **Scale Efficiently**: Handle batch processing of multiple documents
- **Support Testing**: Provide clear interfaces for unit and integration testing

## Decision

We will implement a comprehensive chunking strategies module with the following architecture:

### 1. Core Architecture Design

```python
# Core abstract base class
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk_document(self, document: ProcessedDocument) -> List[DocumentChunk]:
        pass

    @abstractmethod
    def get_strategy_config(self) -> Dict[str, Any]:
        pass

# Concrete implementations
class FixedSizeChunker(ChunkingStrategy)
class SlidingWindowLangChainChunker(ChunkingStrategy)
class SlidingWindowUnstructuredChunker(ChunkingStrategy)
class SemanticChunker(ChunkingStrategy)

# Orchestration and management
class ChunkingPipeline:
    def process_documents_with_all_strategies(self, documents: List[ProcessedDocument]) -> Dict[str, List[DocumentChunk]]
```

### 2. Strategy Implementations

#### Fixed-Size Chunking Strategy

- **Library**: LangChain `TokenTextSplitter`
- **Configuration**: Chunk size (512/1024 tokens), encoding model (cl100k_base for GPT models)
- **Use Case**: Fast baseline for performance comparison
- **Implementation**: Direct token-based splitting with no overlap

#### Sliding Window LangChain Strategy

- **Library**: LangChain `RecursiveCharacterTextSplitter`
- **Configuration**: Chunk size (1000 chars), overlap (200 chars), separators hierarchy
- **Use Case**: Document structure-aware splitting with context preservation
- **Implementation**: Hierarchical splitting (paragraphs → sentences → words → characters)

#### Sliding Window Unstructured Strategy

- **Library**: Custom implementation using Unstructured document elements
- **Configuration**: Max elements per chunk, overlap percentage, element type priorities
- **Use Case**: Element-based chunking respecting document structure
- **Implementation**: Group consecutive elements with intelligent overlap using element boundaries

#### Semantic Chunking Strategy

- **Library**: LangChain `SemanticChunker`
- **Configuration**: Embedding model (sentence-transformers), similarity threshold, min/max chunk sizes
- **Use Case**: Meaning-preserving chunks for complex documents
- **Implementation**: Sentence-level semantic similarity with adaptive breakpoints

### 3. Data Models and Interfaces

```python
@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    strategy_name: str
    content: str
    start_position: int
    end_position: int
    token_count: int
    metadata: Dict[str, Any]
    elements: List[Dict[str, Any]]  # For Unstructured elements
    created_at: datetime

@dataclass
class ChunkingResult:
    strategy_name: str
    total_chunks: int
    processing_time: float
    chunks: List[DocumentChunk]
    statistics: Dict[str, Any]

@dataclass
class ChunkingConfig:
    enabled_strategies: List[str]
    strategy_configs: Dict[str, Dict[str, Any]]
    output_format: str
    batch_size: int
```

### 4. Configuration Management

**Strategy-specific configurations** managed through YAML/JSON:

```yaml
chunking_strategies:
  fixed_size:
    enabled: true
    chunk_size: 1024
    encoding_name: "cl100k_base"

  sliding_langchain:
    enabled: true
    chunk_size: 1000
    chunk_overlap: 200
    separators: ["\n\n", "\n", " ", ""]

  sliding_unstructured:
    enabled: true
    max_elements_per_chunk: 10
    overlap_percentage: 0.2
    priority_elements: ["Title", "Header", "Paragraph"]

  semantic:
    enabled: true
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: 0.8
    min_chunk_size: 200
    max_chunk_size: 2000
```

### 5. Testing Strategy

**Component Testing Approach**:

1. **Unit Tests**: Each strategy implementation with mocked dependencies
2. **Integration Tests**: End-to-end processing with sample documents
3. **Performance Tests**: Benchmarking chunk generation speed and memory usage
4. **Quality Tests**: Chunk coherence, boundary quality, and metadata preservation
5. **Comparative Tests**: Side-by-side strategy comparison with identical inputs

### 6. Output Standardization

All strategies will generate **consistent output formats**:

```json
{
  "document_id": "arxiv_paper_123",
  "strategy": "semantic_chunker",
  "chunks": [
    {
      "chunk_id": "arxiv_paper_123_semantic_001",
      "content": "Abstract. This paper presents...",
      "start_position": 0,
      "end_position": 245,
      "token_count": 52,
      "metadata": {
        "source_elements": ["Title", "Abstract"],
        "page_number": 1,
        "semantic_score": 0.85
      }
    }
  ],
  "statistics": {
    "total_chunks": 15,
    "avg_chunk_size": 867,
    "processing_time": 2.34
  }
}
```

### 7. Implementation Phases

#### Phase 1: Core Infrastructure (Week 1)

- Abstract base classes and interfaces
- Configuration management system
- Basic data models and serialization
- Testing framework setup

#### Phase 2: Strategy Implementation (Week 1-2)

- Fixed-size chunker implementation
- LangChain sliding window chunker
- Unstructured sliding window chunker (custom overlap logic)
- Semantic chunker with embedding integration

#### Phase 3: Integration and Testing (Week 2)

- Pipeline orchestration layer
- Comprehensive test suite
- Performance benchmarking
- Output validation and standardization

#### Phase 4: Evaluation Preparation (Week 2)

- Comparative analysis utilities
- Metrics calculation (chunk quality, processing speed)
- Integration with downstream indexing pipeline

## Consequences

### Positive Outcomes

1. **Modular Design**: Clean separation enables independent strategy development and testing
2. **Comparative Analysis**: Standardized interfaces allow meaningful strategy comparison
3. **Extensibility**: Abstract base class design supports future strategy additions
4. **Production Readiness**: Comprehensive error handling and configuration management
5. **Performance Optimization**: Efficient batch processing and memory management
6. **Quality Assurance**: Extensive testing ensures reliability across all strategies

### Implementation Benefits

1. **Development Efficiency**: Clear interfaces reduce implementation complexity
2. **Debugging Capability**: Strategy isolation simplifies troubleshooting
3. **Configuration Flexibility**: YAML-based configs enable easy experimentation
4. **Testing Confidence**: Comprehensive test coverage ensures system reliability
5. **Demo Preparation**: Standardized outputs facilitate frontend integration

### Technical Trade-offs

1. **Initial Complexity**: Abstract architecture requires upfront design investment
2. **Dependency Management**: Multiple chunking libraries increase dependency complexity
3. **Memory Usage**: Parallel strategy execution may increase memory requirements
4. **Configuration Overhead**: Multiple strategy configs require careful management

### Risk Mitigation

1. **Semantic Chunker Performance**: Embedding model loading and similarity calculations may be slow
   - _Mitigation_: Implement caching and batch processing for embeddings
2. **Unstructured Overlap Logic**: Custom overlap implementation adds complexity
   - _Mitigation_: Thorough testing and clear documentation of overlap algorithms
3. **Memory Management**: Processing large documents with multiple strategies
   - _Mitigation_: Implement streaming processing and memory monitoring

### Integration Requirements

1. **Preprocessing Integration**: Seamless handoff from document_preprocessor.py
2. **Indexing Preparation**: Output format compatible with Typesense indexing
3. **Evaluation Framework**: Metrics calculation for strategy comparison
4. **Frontend Integration**: JSON output format for web interface consumption

### Success Metrics

1. **Functional Completeness**: All 4 strategies successfully implemented
2. **Processing Performance**: <10 seconds per document per strategy
3. **Test Coverage**: >90% code coverage across all components
4. **Output Quality**: Consistent chunk boundaries and metadata preservation
5. **Comparative Capability**: Side-by-side strategy evaluation working

## Dependencies

### Required Libraries

```python
# Core chunking libraries
langchain-text-splitters>=0.0.1    # TokenTextSplitter, RecursiveCharacterTextSplitter, SemanticChunker
unstructured[pdf]>=0.10.0          # Document element processing
sentence-transformers>=2.2.0       # Semantic embeddings for SemanticChunker
tiktoken>=0.5.0                    # Token counting for GPT models

# Data processing and utilities
pydantic>=2.0.0                    # Data models and validation
pyyaml>=6.0                        # Configuration management
rich>=13.0.0                       # Progress tracking and logging
```

### Integration Points

1. **Document Preprocessor**: Input from `src/preprocessor/document_preprocessor.py`
2. **Configuration System**: Extends `src/config.py`
3. **Testing Framework**: Integrates with existing pytest setup
4. **Future Indexer**: Output format designed for Typesense integration

### File Structure

```
src/chunker/
├── __init__.py
├── base.py                        # Abstract base classes and interfaces
├── strategies/
│   ├── __init__.py
│   ├── fixed_size.py             # FixedSizeChunker implementation
│   ├── sliding_langchain.py      # SlidingWindowLangChainChunker
│   ├── sliding_unstructured.py   # SlidingWindowUnstructuredChunker
│   └── semantic.py               # SemanticChunker implementation
├── pipeline.py                    # ChunkingPipeline orchestration
├── models.py                      # Data models (DocumentChunk, ChunkingResult)
├── config.py                      # Configuration management
└── utils.py                       # Utility functions (overlap logic, metrics)

tests/chunker/
├── __init__.py
├── test_strategies.py             # Unit tests for all strategies
├── test_pipeline.py               # Integration tests
├── test_performance.py            # Performance benchmarks
└── fixtures/                      # Test data and mocks
    ├── sample_documents.json
    └── expected_outputs.json
```

## Participants

- **Document Processing Team**: Integration with existing preprocessor
- **System Architecture Team**: Design review and architectural guidance
- **Demo Implementation Team**: Requirements validation and testing support
- **Frontend Development Team**: Output format requirements and integration planning

---

_This ADR establishes the foundation for chunking strategies implementation, enabling the comparative analysis that is central to the Demo Implementation Plan's objectives. The modular design ensures both immediate demo requirements and future extensibility._
