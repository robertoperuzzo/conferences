# Demo Implementation Plan

## Objective
The goal of this demo is to showcase the effectiveness of advanced chunking strategies and tools in improving vector indexing and retrieval quality in AI-powered search systems. The demo will highlight the practical application of the concepts described in the `OVERVIEW.md` file.

## Key Components

### 1. Data Preparation
- **Dataset**: Use ArXiv papers dataset (https://arxiv.org/) - scientific papers in PDF format across various fields (CS, Physics, Math, etc.). This provides diverse document structures, complex formatting, figures, tables, and mathematical content, making it ideal for demonstrating chunking strategies.
- **Preprocessing**: Keep it simple for the first PoC - basic text extraction from PDFs, minimal cleaning (remove extra whitespace), and extract basic metadata (title, authors, abstract).
- **Chunking**: Demonstrate various chunking strategies using open source tools:
  - **Fixed-size blocks**: Use `TokenTextSplitter` for token-aware splitting (e.g., 512 or 1024 tokens) - simple and fast baseline
  - **Sliding windows (LangChain)**: Use `RecursiveCharacterTextSplitter` with overlap for document-structure aware splitting
  - **Sliding windows (Unstructured)**: Use Unstructured's `partition_pdf()` with custom overlap implementation for element-based chunking comparison
  - **Semantic chunking**: Use `SemanticChunker` to identify natural breakpoints based on meaning and document structure
  - **Hybrid approaches**: Mention during presentation but not implemented in PoC (future enhancement)

### 2. Tools and Libraries (All Open Source)
- **Unstructured**: Open source library for handling diverse file formats and element-based chunking (Apache 2.0).
- **LangChain**: Text splitters for fixed-size, sliding windows, and semantic chunking strategies (MIT License).
- **Typesense**: For vector indexing and search (GPL v3).
- **InstantSearch.js**: Frontend search UI components for building the conversational interface (MIT License).
- **Typesense InstantSearch Adapter**: Bridge between Typesense and InstantSearch.js for seamless integration (MIT License).

### 3. Workflow
- **Pipeline**:
  1. **Load and preprocess the dataset**: Download ArXiv papers, extract text from PDFs, perform basic cleaning, and store preprocessed data (metadata + full text) as JSON files locally for use in chunking step.
  2. **Apply chunking strategies**: Load preprocessed papers and apply all 4 chunking strategies to the full text of each paper.
  3. **Index the chunks into Typesense**: Create separate Typesense collections for each chunking strategy (chunks_fixed_size, chunks_sliding_langchain, chunks_sliding_unstructured, chunks_semantic) to enable independent comparison.
  4. **Perform retrieval queries to evaluate quality**: Execute test queries against each collection separately to compare retrieval effectiveness across strategies.
- **Evaluation**:
  - **Test Query Set**: Create curated queries representing different search scenarios (technical, conceptual, methodological, abstract).
  - **Quantitative Metrics**: Measure relevance scores, search speed, total results found, and unique papers covered per strategy.
  - **Quality Assessment**: Analyze chunk coherence (clean sentence boundaries), average chunk length, and content completeness.
  - **Comparative Analysis**: Generate performance reports showing which strategies excel for different query types.
  - **Interactive Dashboard**: Side-by-side comparison interface showing results from all strategies for the same query, with performance metrics visualization.

### 4. User Interface
- **Frontend**:
  - **Strategy Comparison Dashboard**: Interactive interface allowing users to select and compare different chunking strategies side-by-side.
  - **Multi-Collection Search**: Use InstantSearch.js with Typesense InstantSearch Adapter to bridge collection switching and query different chunking strategy collections (chunks_fixed_size, chunks_sliding_langchain, etc.).
  - **Performance Metrics Display**: Real-time visualization of search speed, relevance scores, and chunk quality metrics for each strategy.
  - **Chat-like Query Interface**: Conversational interface where users can input queries and see results from all strategies simultaneously.
- **Backend**:
  - **FastAPI/Flask API**: Handle requests for multi-collection searches and evaluation metrics.
  - **Collection Manager**: Route queries to appropriate Typesense collections based on selected chunking strategy.
  - **Metrics Calculator**: Real-time computation of comparison metrics (speed, relevance, coherence) across strategies.

### Advantages of Using Typesense InstantSearch Adapter
- Simplifies the development process with pre-built components for search and filtering.
- Provides flexibility to customize the chatbot's behavior and appearance.
- Ensures high performance and responsiveness for the demo.

### 5. Deployment
- **Local Development Environment**:
  - **VS Code Dev Container**: Pre-configured development environment with all Python dependencies for chunking, preprocessing, and API development.
  - **Docker Compose Setup**: Orchestrate all required services locally including Typesense server, Python backend API, and frontend application.
  - **Service Architecture**: 
    - Typesense container for search engine
    - Python backend container (FastAPI/Flask)
    - Frontend container (Node.js for InstantSearch.js)
    - Shared volumes for data persistence and code development

## Technologies
- **Programming Language**: Python (for backend and preprocessing).
- **Frontend Framework**: React or plain HTML/CSS/JavaScript for simplicity.
- **Search Engine**: Typesense.
- **AI Tools**: Unstructured (open source), LangChain text splitters.
- **Development Environment**: VS Code Dev Container with pre-configured Python dependencies.
- **Deployment**: Docker Compose for local orchestration of all services.

## Next Steps
1. Set up VS Code Dev Container with Python dependencies (Unstructured, LangChain, Typesense client).
2. Create Docker Compose configuration for Typesense, backend API, and frontend services.
3. Implement data preprocessing pipeline for ArXiv papers.
4. Prototype chunking strategies and test individual components.
5. Develop strategy comparison UI with InstantSearch.js and Typesense adapter.
6. Integrate evaluation metrics and side-by-side comparison features.

## Timeline
- **Week 1**: Set up development environment (Dev Container, Docker Compose) and implement data preprocessing pipeline.
- **Week 2**: Implement chunking strategies, create separate Typesense collections, and index chunks.
- **Week 3**: Develop strategy comparison UI with InstantSearch.js and evaluation dashboard.
- **Week 4**: Integrate evaluation metrics, test complete demo locally, and refine presentation.

## Notes
- Focus on simplicity and clarity to make the demo accessible to a broad audience.
- Highlight the impact of chunking strategies on retrieval quality through visualizations and benchmarks.