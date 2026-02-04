# Chunking Strategies Demo - Development Environment

This project demonstrates various chunking strategies for improving vector indexing and retrieval quality in AI-powered search systems.

## 🚀 Getting Started

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Development Environment

1. **Open in Dev Container**:

   ```bash
   # Clone the repository (if not already done)
   git clone <repository-url>
   cd tomm-202509

   # Open in VS Code
   code .
   ```

2. **Launch Dev Container**:

   - VS Code will detect the `.devcontainer` configuration
   - Click "Reopen in Container" when prompted
   - Or use Command Palette: `Dev Containers: Reopen in Container`

3. **Start Services**:

   ````bash
   # Start Typesense service
   docker compose up -d typesense

   # Check if Typesense is running
   curl http://localhost:8108/health
   ```### Project Structure
   ````

```
├── .devcontainer/          # VS Code Dev Container configuration
│   ├── devcontainer.json   # Container configuration
│   ├── Dockerfile          # Development container image
│   └── post-create.sh      # Setup script
├── data/                   # Data storage
│   ├── raw/               # Raw ArXiv papers (PDFs)
│   ├── processed/         # Preprocessed papers (JSON)
│   └── chunks/            # Generated chunks
├── src/                   # Source code
│   ├── preprocessor/      # Modular text extraction system
│   │   ├── base.py       # Foundation classes and interfaces
│   │   ├── utils/        # Shared utilities (performance, quality, metadata)
│   │   ├── extractors/   # Individual extraction methods
│   │   │   ├── pypdf_extractor.py       # PyPDF integration
│   │   │   ├── unstructured_extractor.py # Unstructured.io integration
│   │   │   ├── marker_extractor.py      # Marker AI/ML processing
│   │   │   └── markitdown_extractor.py  # MarkItDown multi-format
│   │   └── document_preprocessor.py     # Main orchestrator
│   ├── chunker/          # Chunking strategy implementations
│   ├── indexer/          # Typesense indexing utilities
│   ├── evaluation/       # Evaluation and metrics
│   └── config.py         # Configuration settings
├── tests/               # Unit tests
├── frontend/            # HTML/CSS/JavaScript with InstantSearch.js
├── backend/            # FastAPI backend (to be created)
└── docker-compose.yml   # Service orchestration
```

## � Modular Architecture

### Document Preprocessing System

The preprocessing system has been designed with a modular, pluggable architecture:

#### Core Components

- **BaseExtractor**: Abstract base class defining the extraction interface
- **DocumentPreprocessor**: Main orchestrator with lazy loading and format detection
- **ExtractionResult**: Standardized result format across all extractors
- **Utilities**: Shared performance tracking, quality analysis, and metadata extraction

#### Extraction Methods

1. **PyPDF Extractor** (`pypdf`)

   - Fast baseline extraction using LangChain's PyPDFParser
   - Good for simple PDFs without complex layouts
   - Minimal dependencies and fast processing

2. **Unstructured Extractor** (`unstructured`)

   - Premium quality with structure awareness
   - Element-based processing (titles, paragraphs, tables)
   - Advanced layout detection and text cleaning

3. **Marker Extractor** (`marker`)

   - AI/ML-enhanced processing with deep learning models
   - Excellent for complex layouts, equations, and figures
   - Layout-aware extraction with image processing

4. **MarkItDown Extractor** (`markitdown`)
   - Multi-format document processing beyond PDFs
   - Supports Office docs (Word, Excel, PowerPoint)
   - Image, audio, video, and web content processing
   - LLM-optimized Markdown output

#### Usage Examples

```python
from src.preprocessor import DocumentPreprocessor

dp = DocumentPreprocessor()

# Direct method selection
result = dp.extract_text_from_file("document.pdf", method="marker")
result = dp.extract_text_from_file("presentation.pptx", method="markitdown")

# Auto-detection based on file format
result = dp.extract_text_from_file("document.docx", method="auto")

# Batch processing with performance tracking
results = dp.process_documents(method="unstructured", track_performance=True)
```

## �🧪 Development Workflow

### 1. Data Preparation

- Download ArXiv papers to `data/raw/`
- Run preprocessor scripts to extract text and metadata using four methods:
  - **pypdf**: Fast extraction using LangChain's PyPDFParser
  - **unstructured**: Premium quality with structure awareness
  - **marker**: AI/ML-enhanced processing with layout detection
  - **markitdown**: Multi-format document processing (Office docs, images, audio, etc.)
- Store processed data in `data/processed/`

### 2. Chunker Strategies

Implement and test different chunker approaches:

- **Fixed-size blocks**: Token-aware splitting using LangChain's `TokenTextSplitter`
- **Sliding windows (LangChain)**: Document-structure aware splitting with `RecursiveCharacterTextSplitter`
- **Sliding windows (Unstructured)**: Element-based chunker with custom overlap
- **Semantic chunker**: Natural breakpoint identification using `SemanticChunker`

### 3. Indexer and Search

- Create separate Typesense collections for each strategy
- Index chunks with metadata and search capabilities
- Implement comparison queries across strategies

### 4. Evaluation

- Define test query sets for different search scenarios
- Measure relevance scores, search speed, and chunk quality
- Generate comparative analysis reports

## 📋 Usage Commands

### Vector Indexing with Typesense

The project includes a complete vector indexing system for semantic search. All commands should be run from within the dev container.

#### Prerequisites

Ensure Typesense is running (run this outside the dev container):

```bash
docker compose up -d typesense

# Verify Typesense is healthy
curl http://localhost:8108/health  # Should return {"ok":true}
```

#### Available Commands

```bash
# 1. List available extraction methods
python -m src.indexer --list-methods

# 2. Index a specific extraction method + chunking strategy (fast testing)
python -m src.indexer --extraction-method marker --chunking-strategy fixed_size --max-documents 2

# 3. Index all combinations (development mode - recommended)
python -m src.indexer --index-all --max-documents 5

# 4. Index all combinations (production mode - all documents)
python -m src.indexer --index-all --max-documents -1

# 5. Show collection statistics and document counts
python -m src.indexer --stats

# 6. Force recreate existing collections
python -m src.indexer --index-all --max-documents 5 --force-recreate

# 7. Enable debug logging for troubleshooting
python -m src.indexer --index-all --max-documents 2 --log-level DEBUG
```

#### Available Extraction Methods

- `pypdf`: Fast extraction using LangChain's PyPDFParser
- `unstructured`: Premium quality with structure awareness
- `marker`: AI/ML-enhanced processing with layout detection
- `markitdown`: Multi-format document processing (Office docs, images, audio, etc.)
- `comparative_analysis`: Analysis results from method comparisons

#### Available Chunking Strategies

- `fixed_size`: Token-aware splitting (512 tokens, no overlap)
- `sliding_langchain`: Document-structure aware (1000 chars, 100 overlap)
- `sliding_unstructured`: Element-based chunking (800 chars, 80 overlap)
- `semantic`: Natural breakpoint identification (200-1500 chars)

#### Performance Guidelines

- **Development/Testing**: Use `--max-documents 2-10` for fast iteration (2-5 minutes)
- **Full Dataset**: Use `--max-documents -1` for production indexing (may take hours)
- **Model Download**: First run downloads `sentence-transformers/all-MiniLM-L6-v2` (~91MB)
- **Memory Usage**: Ensure 4GB+ RAM available for embedding generation

#### Troubleshooting

```bash
# Connection issues
curl http://typesense:8108/health  # From within dev container

# Collection issues
python -m src.indexer --stats  # Check existing collections

# Reset collections
python -m src.indexer --extraction-method marker --chunking-strategy fixed_size --max-documents 2 --force-recreate

# Check logs
tail -f /workspace/logs/indexer.log
```

## 🛠️ Available Tools and Libraries

### Python Dependencies

- **MarkItDown**: Multi-format document processing (Office docs, images, audio, etc.)
- **Unstructured**: Premium PDF processing and element-based chunking
- **LangChain**: Text splitters, semantic chunking, and PDF parsing (PyPDFParser)
- **Marker**: AI/ML-enhanced PDF processing with layout detection
- **Typesense**: Vector indexing and search engine
- **FastAPI**: Backend API framework

### Development Tools

- **Black**: Code formatting
- **Flake8/Pylint**: Code linting
- **pytest**: Testing framework

## 🎯 Next Implementation Steps

1. ✅ **Set up VS Code Dev Container** (COMPLETED)
2. 🔄 **Create Docker Compose configuration** (COMPLETED)
3. ⏳ **Implement data preprocessing pipeline**
4. ⏳ **Prototype chunking strategies**
5. ⏳ **Develop strategy comparison UI**
6. ⏳ **Integrate evaluation metrics**

## 📊 Services

### Typesense Search Engine

- **URL**: http://localhost:8108
- **API Key**: `xyz` (development only)
- **Health Check**: `curl http://localhost:8108/health`

### Backend API (Future)

- **URL**: http://localhost:8000
- **Framework**: FastAPI with automatic OpenAPI docs

### Frontend (Future)

- **URL**: http://localhost:3000
- **Framework**: Plain HTML/CSS/JavaScript with InstantSearch.js

## 🐛 Troubleshooting

### Container Issues

```bash
# Rebuild dev container
# Command Palette: "Dev Containers: Rebuild Container"

# Check container logs
docker compose logs dev

# Reset everything
docker compose down -v
docker system prune -f
```

### Typesense Issues

```bash
# Check Typesense status
docker compose logs typesense

# Reset Typesense data
docker compose down
docker volume rm tomm-202509_typesense-data
docker compose up -d typesense
```

### Python Dependencies

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Update packages
pip install --upgrade -r requirements.txt
```

## 📚 Documentation

- **[Architecture Decision Records (ADR)](docs/adr/README.md)**: Key architectural decisions and their rationale
- **[Implementation Progress](docs/adr/)**: Detailed documentation of system components and design choices

## 📚 Resources

- [Unstructured Documentation](https://unstructured-io.github.io/unstructured/)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [Typesense Documentation](https://typesense.org/docs/)
- [InstantSearch.js Guide](https://www.algolia.com/doc/guides/building-search-ui/what-is-instantsearch/js/)

---

**Ready to start developing!** 🎉
