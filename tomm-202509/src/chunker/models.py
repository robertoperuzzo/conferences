"""Data models for the chunking strategies module.

This module defines the core data structures used throughout the chunking
pipeline to ensure consistency and type safety across all strategies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class ProcessedDocument:
    """Represents a document that has been preprocessed and is ready for
    chunking.
    
    This is the input format that all chunking strategies expect.
    """
    document_id: str
    title: str
    authors: List[str]
    abstract: str
    full_text: str
    metadata: Dict[str, Any]
    file_path: Optional[Path] = None
    # For Unstructured elements
    elements: Optional[List[Dict[str, Any]]] = None
    processing_method: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_id': self.document_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'full_text': self.full_text,
            'metadata': self.metadata,
            'file_path': str(self.file_path) if self.file_path else None,
            'elements': self.elements,
            'processing_method': self.processing_method,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedDocument':
        """Create from dictionary loaded from JSON."""
        # Handle datetime parsing
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        # Handle file_path
        file_path = data.get('file_path')
        if file_path:
            file_path = Path(file_path)
        
        return cls(
            document_id=data['document_id'],
            title=data['title'],
            authors=data['authors'],
            abstract=data['abstract'],
            full_text=data['full_text'],
            metadata=data.get('metadata', {}),
            file_path=file_path,
            elements=data.get('elements'),
            processing_method=data.get('processing_method', 'unknown'),
            created_at=created_at
        )


@dataclass
class DocumentChunk:
    """Represents a single chunk created from a document.
    
    Contains all necessary information for indexing and retrieval.
    """
    chunk_id: str
    document_id: str
    strategy_name: str
    content: str
    start_position: int
    end_position: int
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    # For Unstructured elements
    elements: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'strategy_name': self.strategy_name,
            'content': self.content,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'token_count': self.token_count,
            'metadata': self.metadata,
            'elements': self.elements,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """Create from dictionary loaded from JSON."""
        # Handle datetime parsing
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            chunk_id=data['chunk_id'],
            document_id=data['document_id'],
            strategy_name=data['strategy_name'],
            content=data['content'],
            start_position=data['start_position'],
            end_position=data['end_position'],
            token_count=data['token_count'],
            metadata=data.get('metadata', {}),
            elements=data.get('elements', []),
            created_at=created_at
        )


@dataclass
class ChunkingStatistics:
    """Statistics about the chunking process."""
    total_chunks: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    avg_token_count: float
    min_token_count: int
    max_token_count: int
    processing_time: float
    memory_usage_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_chunks': self.total_chunks,
            'avg_chunk_size': self.avg_chunk_size,
            'min_chunk_size': self.min_chunk_size,
            'max_chunk_size': self.max_chunk_size,
            'avg_token_count': self.avg_token_count,
            'min_token_count': self.min_token_count,
            'max_token_count': self.max_token_count,
            'processing_time': self.processing_time,
            'memory_usage_mb': self.memory_usage_mb
        }


@dataclass
class ChunkingResult:
    """Result of chunking a single document with a specific strategy."""
    strategy_name: str
    document_id: str
    chunks: List[DocumentChunk]
    statistics: ChunkingStatistics
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'strategy_name': self.strategy_name,
            'document_id': self.document_id,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'statistics': self.statistics.to_dict(),
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkingResult':
        """Create from dictionary loaded from JSON."""
        # Handle datetime parsing
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        # Parse chunks
        chunks = [
            DocumentChunk.from_dict(chunk_data)
            for chunk_data in data['chunks']
        ]
        
        # Parse statistics
        stats_data = data['statistics']
        statistics = ChunkingStatistics(**stats_data)
        
        return cls(
            strategy_name=data['strategy_name'],
            document_id=data['document_id'],
            chunks=chunks,
            statistics=statistics,
            success=data.get('success', True),
            error_message=data.get('error_message'),
            created_at=created_at
        )


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies."""
    enabled_strategies: List[str] = field(default_factory=list)
    strategy_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    output_format: str = "json"
    batch_size: int = 10
    max_workers: int = 4
    save_intermediate: bool = True
    output_directory: Optional[Path] = None
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for a specific strategy."""
        return self.strategy_configs.get(strategy_name, {})
    
    def is_strategy_enabled(self, strategy_name: str) -> bool:
        """Check if a strategy is enabled."""
        return strategy_name in self.enabled_strategies
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkingConfig':
        """Create from dictionary loaded from configuration file."""
        output_directory = data.get('output_directory')
        if output_directory:
            output_directory = Path(output_directory)
        
        return cls(
            enabled_strategies=data.get('enabled_strategies', []),
            strategy_configs=data.get('strategy_configs', {}),
            output_format=data.get('output_format', 'json'),
            batch_size=data.get('batch_size', 10),
            max_workers=data.get('max_workers', 4),
            save_intermediate=data.get('save_intermediate', True),
            output_directory=output_directory
        )
