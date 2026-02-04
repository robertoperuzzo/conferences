# ADR-010: Typesense Vector Indexing Implementation for Document Chunks

## Status

**PROPOSED** - This ADR is proposed for discussion

## Context

Based on the Demo Implementation Plan, we need to implement vector indexing in Typesense to enable semantic search and comparison between different chunking strategies and extraction methods. Currently, we have:

1. **Processed documents** from multiple extraction methods (pypdf, unstructured, marker) stored in `/data/processed/`
2. **Chunked data** from multiple strategies (fixed_size, sliding_langchain, sliding_unstructured, semantic) stored in `/data/chunks/`
3. **Need** to convert these chunks into vector embeddings and store them in Typesense for semantic search capabilities

## Decision

We propose to implement a **Typesense Vector Indexing System** that:

### 1. Collection Structure Design

Create separate Typesense collections for each **extraction method + chunking strategy** combination to enable comparative analysis:

**Collection Naming Convention**: `{extraction_method}_{chunking_strategy}`

Examples:

- `marker_fixed_size`
- `marker_sliding_langchain`
- `marker_sliding_unstructured`
- `marker_semantic`
- `unstructured_fixed_size`
- `unstructured_sliding_langchain`
- `pypdf_fixed_size`
- etc.

### 2. Document Schema Design

Each collection will contain documents with the following schema:

```json
{
  "name": "marker_fixed_size",
  "fields": [
    {
      "name": "chunk_id",
      "type": "string",
      "facet": false
    },
    {
      "name": "document_id",
      "type": "string",
      "facet": true
    },
    {
      "name": "document_title",
      "type": "string",
      "facet": true
    },
    {
      "name": "document_filename",
      "type": "string",
      "facet": true
    },
    {
      "name": "extraction_method",
      "type": "string",
      "facet": true
    },
    {
      "name": "chunking_strategy",
      "type": "string",
      "facet": true
    },
    {
      "name": "content",
      "type": "string",
      "facet": false
    },
    {
      "name": "token_count",
      "type": "int32",
      "facet": true
    },
    {
      "name": "chunk_index",
      "type": "int32",
      "facet": true
    },
    {
      "name": "start_position",
      "type": "int32",
      "facet": false
    },
    {
      "name": "end_position",
      "type": "int32",
      "facet": false
    },
    {
      "name": "embedding",
      "type": "float[]",
      "num_dim": 384
    }
  ],
  "default_sorting_field": "chunk_index"
}
```

### 3. Embedding Generation Strategy

- **Model**: Use `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) for consistency with the Typesense showcase example
- **Input**: Combine chunk content with document metadata for richer embeddings:
  ```python
  embedding_text = f"{document_title}. {chunk_content}"
  ```
- **Processing**: Batch process embeddings to optimize performance

### 4. Data Pipeline Architecture

#### Phase 1: Data Extraction and Preparation

1. **Source**: Read processed JSON files from `/data/processed/{extraction_method}/`
2. **Document Limiting**: Apply `--max-documents` parameter to limit processing scope
   - Development/Testing: `--max-documents 5-10` (5-10 minutes processing)
   - Production: `--max-documents -1` (all documents)
3. **Chunk Source**: Read chunking results from `/data/chunks/`
4. **Combine**: Merge document metadata with chunk data

#### Phase 2: Embedding Generation

1. **Load Model**: Initialize `sentence-transformers/all-MiniLM-L6-v2`
2. **Batch Processing**: Process chunks in batches of 100-500 for efficiency
3. **Generate Embeddings**: Create 384-dimensional vectors for each chunk

#### Phase 3: Typesense Indexing

1. **Collection Management**: Create/recreate collections as needed
2. **Document Preparation**: Format documents according to schema
3. **Bulk Import**: Use Typesense bulk import API for efficient indexing
4. **Validation**: Verify successful indexing with sample queries

### 5. Implementation Components

#### A. Indexer Module (`src/indexer/`)

```
src/indexer/
├── __init__.py
├── base.py                 # Base indexer interface
├── typesense_indexer.py    # Main Typesense indexer implementation
├── embedding_generator.py  # Handles embedding generation
├── collection_manager.py   # Manages Typesense collections
├── data_processor.py      # Processes and formats data
└── config.py              # Indexer configuration
```

#### B. Configuration Management

- **Environment Variables**: Typesense connection details
- **Model Configuration**: Embedding model settings
- **Batch Configuration**: Processing batch sizes
- **Collection Configuration**: Schema definitions per strategy
- **Document Limits**: Configurable limits for development/testing vs production

#### C. CLI Interface

```bash
# Index all extraction methods and strategies (limit to 5 documents for testing)
python -m src.indexer --index-all --max-documents 5

# Index specific combination with document limit
python -m src.indexer --extraction-method marker --chunking-strategy fixed_size --max-documents 10

# Index all documents (production mode)
python -m src.indexer --index-all --max-documents -1

# Reindex existing collections
python -m src.indexer --reindex --collection marker_fixed_size --max-documents 5
```

### 6. Query and Search Capabilities

Once indexed, users can:

1. **Semantic Search**: Find relevant chunks across documents

   ```json
   {
     "q": "*",
     "vector_query": "embedding:([...], k:10)",
     "filter_by": "extraction_method:marker AND chunking_strategy:fixed_size"
   }
   ```

2. **Cross-Strategy Comparison**: Compare results from different strategies for the same query

3. **Document-Specific Search**: Find similar chunks within or across documents

   ```json
   {
     "q": "*",
     "vector_query": "embedding:([], id: chunk_id_123)",
     "filter_by": "document_id:9308101_Dynamic_Backtracking"
   }
   ```

4. **Multi-Collection Federated Search**: Query multiple collections simultaneously

## Rationale

### Why Separate Collections per Strategy?

- **Performance**: Dedicated indexes for each strategy optimize query speed
- **Comparison**: Easy to compare results from different extraction/chunking combinations
- **Flexibility**: Different strategies may benefit from different search parameters
- **Isolation**: Issues with one collection don't affect others

### Why sentence-transformers/all-MiniLM-L6-v2?

- **Proven**: Used successfully in Typesense showcase examples
- **Balanced**: Good balance of quality vs. speed (384 dimensions)
- **Open Source**: No API dependencies or costs
- **Multilingual**: Supports various languages

### Why Include Metadata in Embeddings?

- **Context**: Document title provides additional context for semantic matching
- **Quality**: Richer embeddings improve search relevance
- **Consistency**: Follows patterns from successful implementations

## Consequences

### Positive

- **Semantic Search**: Enables powerful semantic search across document chunks
- **Strategy Comparison**: Quantitative comparison of chunking strategy effectiveness
- **Scalability**: Typesense handles large-scale vector operations efficiently
- **Speed**: Fast nearest neighbor search with HNSW indexing
- **Flexibility**: Multiple collections allow tailored search strategies

### Negative

- **Storage**: Multiple collections increase storage requirements
  - Development: ~50-100MB for 5-10 documents
  - Production: ~3-5GB for full dataset
- **Complexity**: More complex than single-collection approach
- **Maintenance**: Multiple collections require more maintenance overhead
- **Processing Time**:
  - Development: 5-10 minutes for limited documents
  - Production: Initial full indexing will take 2-4 hours

### Risks

- **Collection Proliferation**: Could lead to too many collections if not managed properly
- **Memory Usage**: Embedding generation requires significant memory (4GB+ for development, 8GB+ for production)
- **Model Dependency**: Reliance on specific embedding model version
- **Development Cycles**: Need to balance document limits for meaningful testing vs processing time

## Alternatives Considered

### 1. Single Collection with Strategy Fields

- **Pros**: Simpler management, single schema
- **Cons**: Less optimized queries, harder strategy comparison
- **Decision**: Rejected due to comparison requirements

### 2. Different Embedding Models

- **OpenAI Embeddings**: Higher quality but API costs and dependencies
- **BGE Models**: Good performance but larger size
- **Decision**: Chose all-MiniLM-L6-v2 for balance and proven track record

### 3. Combined Metadata Approach

- **Store metadata separately**: Link collections to document metadata
- **Embed everything**: Include all metadata in embeddings
- **Decision**: Chose selective metadata inclusion for balance

## Implementation Timeline

### Phase 1: Core Infrastructure

- [ ] Create indexer module structure
- [ ] Implement embedding generator
- [ ] Create collection manager
- [ ] Basic Typesense integration

### Phase 2: Data Processing Pipeline

- [ ] Data extraction from processed files
- [ ] Chunk data integration
- [ ] Batch processing implementation
- [ ] Error handling and validation

### Phase 3: Indexing Implementation

- [ ] Collection schema creation
- [ ] Bulk import functionality
- [ ] Progress tracking and logging
- [ ] CLI interface

### Phase 4: Testing and Optimization

- [ ] Performance testing
- [ ] Query optimization
- [ ] Documentation
- [ ] Integration with demo frontend

## Success Criteria

1. **Functional**: All extraction method + chunking strategy combinations successfully indexed
2. **Performance**: Sub-100ms vector search queries for typical use cases
3. **Quality**: Relevant semantic search results validated manually on test queries
4. **Scalability**: System handles configurable document limits efficiently
   - Development: 5-10 documents in <5 minutes
   - Production: 10,000+ chunks per collection efficiently
5. **Reliability**: 99%+ successful indexing rate with proper error handling
6. **Flexibility**: Easy switching between development (limited) and production (full) modes

## Notes

- This ADR focuses on the indexing infrastructure; search interface design will be covered in a separate ADR
- **Development Mode**: Use `--max-documents 10` for fast iteration (<5 minutes processing)
- **Production Mode**: Use `--max-documents -1` for full dataset (<2 hours processing)
- Estimated storage requirements:
  - Development: 50-100MB for 5-10 documents
  - Production: 3-5GB for complete dataset
- Monitoring and alerting for collection health should be implemented in production

## Next Steps for Discussion:

1. **Collection Naming**: Is the `{extraction_method}_{chunking_strategy}` format appropriate?
2. **Schema**: Are there additional fields needed for your specific use cases?
3. **Embedding Strategy**: Should we include more document metadata in the embeddings?
4. **Document Limits**: What's the ideal number of documents for development testing (5, 10, 20)?
5. **Resource Requirements**: Are the updated estimates acceptable?
   - Development: 50-100MB storage, <5 minutes processing
   - Production: 3-5GB storage, <2 hours processing
6. **Implementation Priority**: Which extraction method + chunking strategy combinations should we prioritize first?

---

**Author**: Assistant  
**Date**: 2025-08-28  
**Reviewers**: [To be assigned]  
**Next Review**: [To be scheduled]
