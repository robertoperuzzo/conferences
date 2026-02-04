"""Configuration settings for the chunker strategies demo."""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATA_CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks"
LOGS_PATH = PROJECT_ROOT / "logs"

# Legacy naming for backwards compatibility
RAW_DATA_DIR = DATA_RAW_PATH
PROCESSED_DATA_DIR = DATA_PROCESSED_PATH

# ArXiv API configuration
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
MAX_CONCURRENT_DOWNLOADS = 5

# Typesense configuration
TYPESENSE_CONFIG = {
    "host": os.getenv("TYPESENSE_HOST", "localhost"),
    "port": int(os.getenv("TYPESENSE_PORT", "8108")),
    "protocol": os.getenv("TYPESENSE_PROTOCOL", "http"),
    "api_key": os.getenv("TYPESENSE_API_KEY", "xyz"),
}

# Chunker strategies configuration
CHUNKER_STRATEGIES = {
    "fixed_size": {
        "chunk_size": int(os.getenv("CHUNK_SIZE_TOKENS", "1000")),
        "chars_per_token": int(os.getenv("CHUNK_OVERLAP", "4")),
        "collection_name": "chunks_fixed_size"
    },
    "sliding_langchain": {
        "chunk_size": 1000,
        "chunk_overlap": 80,
        "collection_name": "chunks_sliding_langchain"
    },
    "sliding_unstructured": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "collection_name": "chunks_sliding_unstructured"
    },
    "semantic": {
        "threshold": float(os.getenv("SEMANTIC_THRESHOLD", "0.8")),
        "collection_name": "chunks_semantic"
    }
}

# Collection schema for Typesense
COLLECTION_SCHEMA = {
    "name": "",  # Will be set dynamically
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "paper_id", "type": "string", "facet": True},
        {"name": "title", "type": "string", "facet": True},
        {"name": "authors", "type": "string[]", "facet": True},
        {"name": "abstract", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "chunk_index", "type": "int32", "facet": True},
        {"name": "chunk_strategy", "type": "string", "facet": True},
        {"name": "chunk_size", "type": "int32"},
        {"name": "created_at", "type": "int64"},
    ]
}
