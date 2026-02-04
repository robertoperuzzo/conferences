"""
Configuration for the indexer module.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class IndexerConfig:
    """Configuration for the Typesense indexer."""

    # Typesense connection
    typesense_host: str = os.getenv('TYPESENSE_HOST', 'localhost')
    typesense_port: int = int(os.getenv('TYPESENSE_PORT', '8108'))
    typesense_protocol: str = os.getenv('TYPESENSE_PROTOCOL', 'http')
    typesense_api_key: str = os.getenv('TYPESENSE_ADMIN_API_KEY', '')

    # Embedding configuration
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    embedding_dimensions: int = 384
    batch_size: int = 100

    # Processing configuration
    max_documents: int = -1  # -1 means all documents
    connection_timeout_seconds: int = 60

    # Data paths
    processed_data_path: str = '/workspace/data/processed'
    chunks_data_path: str = '/workspace/data/chunks'

    # Collection configuration
    collection_prefix: str = ''
    default_sorting_field: str = 'chunk_index'

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_documents == 0:
            raise ValueError("max_documents cannot be 0")

    @property
    def typesense_nodes(self) -> list:
        """Get Typesense nodes configuration."""
        return [{
            'host': self.typesense_host,
            'port': self.typesense_port,
            'protocol': self.typesense_protocol
        }]

    def get_collection_name(self, extraction_method: str,
                            chunking_strategy: str) -> str:
        """Generate collection name for extraction method and strategy."""
        base_name = f"{extraction_method}_{chunking_strategy}"
        if self.collection_prefix:
            return f"{self.collection_prefix}_{base_name}"
        return base_name


# Default collection schema
COLLECTION_SCHEMA_TEMPLATE = {
    "fields": [
        {
            "name": "chunk_id",
            "type": "string",
            "facet": False
        },
        {
            "name": "document_id",
            "type": "string",
            "facet": True
        },
        {
            "name": "document_title",
            "type": "string",
            "facet": True
        },
        {
            "name": "document_filename",
            "type": "string",
            "facet": True
        },
        {
            "name": "extraction_method",
            "type": "string",
            "facet": True
        },
        {
            "name": "chunking_strategy",
            "type": "string",
            "facet": True
        },
        {
            "name": "strategy_name",
            "type": "string",
            "facet": True
        },
        {
            "name": "content",
            "type": "string",
            "facet": False
        },
        {
            "name": "token_count",
            "type": "int32",
            "facet": True
        },
        {
            "name": "chunk_index",
            "type": "int32",
            "facet": True
        },
        {
            "name": "total_chunks",
            "type": "int32",
            "facet": True
        },
        {
            "name": "start_position",
            "type": "int32",
            "facet": False
        },
        {
            "name": "end_position",
            "type": "int32",
            "facet": False
        },
        {
            "name": "authors",
            "type": "string[]",
            "facet": True,
            "optional": True
        },
        {
            "name": "created_at",
            "type": "string",
            "facet": False,
            "optional": True
        },
        {
            "name": "chunk_size",
            "type": "int32",
            "facet": True,
            "optional": True
        },
        {
            "name": "chunk_overlap",
            "type": "int32",
            "facet": True,
            "optional": True
        },
        {
            "name": "encoding_name",
            "type": "string",
            "facet": True,
            "optional": True
        },
        {
            "name": "preprocessing_method",
            "type": "string",
            "facet": True,
            "optional": True
        },
        {
            "name": "content_length",
            "type": "int32",
            "facet": True,
            "optional": True
        },
        {
            "name": "processing_time",
            "type": "float",
            "facet": True,
            "optional": True
        },
        {
            "name": "memory_usage",
            "type": "float",
            "facet": True,
            "optional": True
        },
        {
            "name": "cpu_usage_percent",
            "type": "float",
            "facet": True,
            "optional": True
        },
        {
            "name": "gpu_usage_percent",
            "type": "float",
            "facet": True,
            "optional": True
        },
        {
            "name": "embedding",
            "type": "float[]",
            "num_dim": 384
        }
    ]
}
