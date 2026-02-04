"""Chunking strategies module for document processing.

This module provides a comprehensive set of chunking strategies and utilities
for breaking down documents into meaningful chunks for vector indexing and
retrieval applications.

Main Components:
- ChunkingPipeline: Main orchestration class
- ChunkingStrategy: Abstract base class for all strategies
- Individual strategy implementations (Fixed-size, Sliding window, Semantic)
- Configuration management and utilities

Usage Example:
    from src.chunker import ChunkingPipeline
    from src.chunker.config import get_default_config
    
    # Initialize pipeline
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    # Process a document
    results = pipeline.process_document(document)
"""

from .pipeline import ChunkingPipeline
from .base import ChunkingStrategy, ChunkingError, TokenCounter
from .models import (
    ProcessedDocument, DocumentChunk,
    ChunkingResult, ChunkingConfig
)
from .config import (
    get_default_config, load_config_from_file,
    ChunkingConfigManager
)
from .strategies import (
    FixedSizeChunker, SlidingLangChainChunker,
    SlidingUnstructuredChunker, SemanticChunker
)

__version__ = "1.0.0"

__all__ = [
    # Main classes
    'ChunkingPipeline',
    'ChunkingStrategy',
    'ChunkingError',
    'TokenCounter',

    # Data models
    'ProcessedDocument',
    'DocumentChunk',
    'ChunkingResult',
    'ChunkingConfig',

    # Configuration
    'get_default_config',
    'load_config_from_file',
    'ChunkingConfigManager',

    # Strategies
    'FixedSizeChunker',
    'SlidingLangChainChunker',
    'SlidingUnstructuredChunker',
    'SemanticChunker'
]
