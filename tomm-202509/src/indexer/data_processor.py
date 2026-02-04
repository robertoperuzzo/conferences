"""
Data processor for preparing documents for indexing.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes document data for indexing."""

    def __init__(self, processed_data_path: str, chunks_data_path: str):
        """Initialize data processor."""
        self.processed_data_path = Path(processed_data_path)
        self.chunks_data_path = Path(chunks_data_path)

    def get_available_extraction_methods(self) -> List[str]:
        """Get list of available extraction methods."""
        methods = []
        for item in self.processed_data_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                methods.append(item.name)
        return sorted(methods)

    def get_processed_files(self, extraction_method: str,
                            max_documents: int = -1) -> List[Path]:
        """Get processed files for an extraction method."""
        method_path = self.processed_data_path / extraction_method

        if not method_path.exists():
            logger.warning(f"Path not found: {method_path}")
            return []

        # Get all JSON files
        json_files = list(method_path.glob("*.json"))

        if max_documents > 0:
            json_files = json_files[:max_documents]
            logger.info(f"Limited to {len(json_files)} documents for "
                        f"{extraction_method}")

        return sorted(json_files)

    def get_chunks_file(self, document_id: str, extraction_method: str,
                        chunking_strategy: str) -> Optional[Path]:
        """Get chunks file for a document with the new format."""
        pattern = (f"{document_id}_{extraction_method}_"
                   f"{chunking_strategy}.json")
        chunks_file = self.chunks_data_path / pattern

        if chunks_file.exists():
            return chunks_file

        logger.warning("No chunks file found for %s_%s_%s",
                       document_id, extraction_method, chunking_strategy)
        return None

    def load_processed_document(self, file_path: Path) -> Optional[
            Dict[str, Any]]:
        """Load a processed document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("Error loading processed document %s: %s",
                         file_path, e)
            return None

    def load_chunks_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load chunks data in the new format."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate new format structure
            if 'results' in data and 'chunks' in data['results']:
                return data
            else:
                logger.error("Invalid chunks data format in %s - "
                             "missing 'results.chunks'", file_path)
                return None

        except (IOError, json.JSONDecodeError) as e:
            logger.error("Error loading chunks data %s: %s", file_path, e)
            return None

    def get_available_strategies(self) -> List[str]:
        """Get available chunking strategies by scanning chunk files."""
        strategies = set()

        # Scan all chunk files to find strategies
        for chunk_file in self.chunks_data_path.glob("*.json"):
            # Parse filename: {document_id}_{extraction_method}_{strategy}.json
            # Strategy can contain underscores, so we need to be careful
            filename = chunk_file.stem

            # Try to find extraction method and strategy
            # Known extraction methods to help with parsing
            known_methods = ['pypdf', 'unstructured', 'marker', 'markitdown']

            for method in known_methods:
                if f"_{method}_" in filename:
                    # Find the strategy part after the extraction method
                    method_pos = filename.find(f"_{method}_")
                    strategy_start = method_pos + len(f"_{method}_")
                    strategy = filename[strategy_start:]
                    if strategy:
                        strategies.add(strategy)
                    break

        return sorted(list(strategies))

    def get_available_strategies_for_extraction_method(self,
                                                       extraction_method: str
                                                       ) -> List[str]:
        """Get available strategies for a specific extraction method."""
        strategies = set()

        # Scan chunk files for this extraction method
        pattern = f"*_{extraction_method}_*.json"
        for chunk_file in self.chunks_data_path.glob(pattern):
            # Parse filename: {document_id}_{extraction_method}_{strategy}.json
            filename = chunk_file.stem

            # Find the strategy part after the extraction method
            method_marker = f"_{extraction_method}_"
            method_pos = filename.find(method_marker)
            if method_pos != -1:
                strategy_start = method_pos + len(method_marker)
                strategy = filename[strategy_start:]
                if strategy:
                    strategies.add(strategy)

        return sorted(list(strategies))

    def prepare_documents_for_indexing(self, extraction_method: str,
                                       chunking_strategy: str,
                                       max_documents: int = -1) -> List[
                                           Dict[str, Any]]:
        """Prepare documents for indexing with new format support."""
        documents = []

        # Get processed files
        processed_files = self.get_processed_files(extraction_method,
                                                   max_documents)

        logger.info("Processing %d documents for %s_%s",
                    len(processed_files), extraction_method,
                    chunking_strategy)

        for file_path in processed_files:
            # Load processed document
            processed_doc = self.load_processed_document(file_path)
            if not processed_doc:
                continue

            # Extract document info
            document_id = processed_doc.get('document_id')
            if not document_id:
                logger.warning("No document_id in %s", file_path)
                continue

            # Use strategy-aware file discovery
            chunks_file = self.get_chunks_file(document_id, extraction_method,
                                               chunking_strategy)
            if not chunks_file:
                continue

            chunks_data = self.load_chunks_data(chunks_file)
            if not chunks_data:
                continue

            # Process chunks (same logic as before, but simpler access)
            if ('results' not in chunks_data or
                    'chunks' not in chunks_data['results']):
                logger.warning("No chunks in data for %s", document_id)
                continue

            # Create documents for indexing
            for chunk in chunks_data['results']['chunks']:
                doc = self._create_index_document(
                    processed_doc, chunk, extraction_method,
                    chunking_strategy, chunks_data
                )
                if doc:
                    documents.append(doc)

        logger.info("Prepared %d documents for indexing", len(documents))
        return documents

    def _create_index_document(self, processed_doc: Dict[str, Any],
                               chunk: Dict[str, Any], extraction_method: str,
                               chunking_strategy: str,
                               chunks_data: Dict[str, Any]) -> Optional[
                                   Dict[str, Any]]:
        """Create a document for indexing with enhanced metadata."""
        try:
            # Extract metadata from chunk
            metadata = chunk.get('metadata', {})

            # Get strategy config and processing metadata from chunks_data
            strategy_config = chunks_data.get('strategy_config', {})
            processing_metadata = chunks_data.get('processing_metadata', {})
            doc_info = chunks_data.get('document_info', {})

            # Create the document with all available fields
            doc = {
                "chunk_id": chunk.get('chunk_id', ''),
                "document_id": processed_doc.get('document_id', ''),
                "document_title": (processed_doc.get('title', '') or
                                   metadata.get('title', '')),
                "document_filename": processed_doc.get('file_name', ''),
                "extraction_method": extraction_method,
                "chunking_strategy": chunking_strategy,
                "strategy_name": chunk.get('strategy_name', chunking_strategy),
                "content": chunk.get('content', ''),
                "token_count": chunk.get('token_count', 0),
                "chunk_index": metadata.get('chunk_index', 0),
                "total_chunks": metadata.get('total_chunks', 0),
                "start_position": chunk.get('start_position', 0),
                "end_position": chunk.get('end_position', 0),
                "created_at": chunk.get('created_at', ''),
                "preprocessing_method": doc_info.get(
                    'preprocessing_method', extraction_method),
                "content_length": doc_info.get('content_length', 0),
                "processing_time": processing_metadata.get(
                    'processing_time', 0),
                "memory_usage": processing_metadata.get('memory_usage', 0),
                "cpu_usage_percent": processing_metadata.get(
                    'cpu_usage_percent', 0),
                "gpu_usage_percent": processing_metadata.get(
                    'gpu_usage_percent', 0),
            }

            # Add authors if available
            authors = metadata.get('authors', [])
            if authors:
                doc["authors"] = authors

            # Add strategy parameters from new format
            if 'parameters' in strategy_config:
                params = strategy_config['parameters']
                doc.update({
                    "chunk_size": params.get('chunk_size', 0),
                    "chunk_overlap": params.get('overlap', 0),
                    "encoding_name": params.get('encoding_name', ''),
                })

            return doc

        except (KeyError, TypeError, ValueError) as e:
            logger.error("Error creating index document: %s", e)
            return None
