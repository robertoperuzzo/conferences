"""
Main Typesense indexer implementation.
"""

import logging
from typing import List, Dict, Any, Optional
import typesense
from .base import BaseIndexer
from .config import IndexerConfig, COLLECTION_SCHEMA_TEMPLATE
from .embedding_generator import EmbeddingGenerator
from .collection_manager import CollectionManager
from .data_processor import DataProcessor
from .performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)


class TypesenseIndexer(BaseIndexer):
    """Main Typesense indexer for document chunks."""

    def __init__(self, config: Optional[IndexerConfig] = None):
        """Initialize Typesense indexer."""
        self.config = config or IndexerConfig()

        # Initialize Typesense client
        typesense_config = {
            'nodes': self.config.typesense_nodes,
            'api_key': self.config.typesense_api_key,
            'connection_timeout_seconds': self.config.connection_timeout_seconds
        }

        # Debug output
        logger.debug(f"Typesense config: {typesense_config}")

        self.client = typesense.Client(typesense_config)

        # Initialize components
        self.embedding_generator = EmbeddingGenerator(
            self.config.embedding_model
        )
        self.collection_manager = CollectionManager(
            self.client, COLLECTION_SCHEMA_TEMPLATE
        )
        self.data_processor = DataProcessor(
            self.config.processed_data_path,
            self.config.chunks_data_path
        )

        # Initialize performance analyzer
        self.performance_analyzer = PerformanceAnalyzer(self.client)

    def create_collection(self, collection_name: str,
                          schema: Dict[str, Any]) -> bool:
        """Create a new collection with the given schema."""
        try:
            self.client.collections.create(schema)
            return True
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        return self.collection_manager.delete_collection(collection_name)

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        return self.collection_manager.collection_exists(collection_name)

    def index_documents(self, collection_name: str,
                        documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index a batch of documents."""
        try:
            if not documents:
                return {"success": True, "indexed": 0}

            # Use Typesense's import endpoint for bulk indexing
            results = self.client.collections[collection_name].documents.import_(
                documents, {'action': 'create'}
            )

            # Parse results
            success_count = 0
            error_count = 0

            for result in results:
                if result.get('success', False):
                    success_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Failed to index document: {result}")

            logger.info(f"Indexed {success_count} documents, "
                        f"{error_count} errors")

            return {
                "success": error_count == 0,
                "indexed": success_count,
                "errors": error_count
            }

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {"success": False, "indexed": 0, "errors": len(documents)}

    def search(self, collection_name: str,
               query: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a search query."""
        try:
            return self.client.collections[collection_name].documents.search(query)
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return {"hits": [], "found": 0}

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        stats = self.collection_manager.get_collection_stats(collection_name)
        return stats or {}

    def index_extraction_method_strategy(self, extraction_method: str,
                                         chunking_strategy: str,
                                         max_documents: int = -1,
                                         force_recreate: bool = False) -> bool:
        """Index documents for a specific extraction method and strategy."""
        collection_name = self.config.get_collection_name(
            extraction_method, chunking_strategy
        )

        logger.info(f"Starting indexing for {collection_name}")

        try:
            # Create or verify collection
            embedding_dims = self.embedding_generator.get_embedding_dimensions()
            success = self.collection_manager.create_collection(
                collection_name, extraction_method, chunking_strategy,
                embedding_dims, force_recreate
            )

            if not success:
                logger.error(f"Failed to create collection: {collection_name}")
                return False

            # Prepare documents
            documents = self.data_processor.prepare_documents_for_indexing(
                extraction_method, chunking_strategy, max_documents
            )

            if not documents:
                logger.warning(f"No documents found for {collection_name}")
                return True

            # Generate embeddings and index in batches
            total_indexed = 0
            batch_size = self.config.batch_size

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} of "
                            f"{(len(documents) - 1)//batch_size + 1} "
                            f"({len(batch)} documents)")

                # Generate embeddings for batch
                texts = [
                    self.embedding_generator.create_embedding_text(
                        doc['document_title'], doc['content']
                    )
                    for doc in batch
                ]

                embeddings = self.embedding_generator.generate_embeddings(
                    texts)

                # Add embeddings to documents
                for doc, embedding in zip(batch, embeddings):
                    doc['embedding'] = embedding

                # Index batch
                result = self.index_documents(collection_name, batch)
                if result['success']:
                    total_indexed += result['indexed']
                else:
                    logger.error(f"Failed to index batch {i//batch_size + 1}")
                    return False

            logger.info(f"Successfully indexed {total_indexed} documents "
                        f"in collection {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error indexing {collection_name}: {e}")
            return False

    def index_all_combinations(self, max_documents: int = -1,
                               force_recreate: bool = False) -> Dict[str, bool]:
        """Index all extraction method and chunking strategy combinations."""
        results = {}

        # Get available extraction methods
        extraction_methods = self.data_processor.get_available_extraction_methods()
        logger.info(f"Found extraction methods: {extraction_methods}")

        for extraction_method in extraction_methods:
            # Get available strategies for this extraction method
            strategies = (
                self.data_processor
                .get_available_strategies_for_extraction_method(
                    extraction_method))

            if not strategies:
                logger.warning("No strategies found for %s", extraction_method)
                continue

            logger.info(
                "Found strategies for %s: %s", extraction_method, strategies)

            # Index each combination
            for strategy in strategies:
                combination = f"{extraction_method}_{strategy}"
                logger.info("Indexing combination: %s", combination)

                success = self.index_extraction_method_strategy(
                    extraction_method, strategy, max_documents, force_recreate
                )
                results[combination] = success

        return results

    # Performance Analysis Methods

    def get_performance_summary(self, collection_name: str) -> Dict[str, Any]:
        """
        Get performance summary for a collection.

        Args:
            collection_name: Name of the collection to analyze

        Returns:
            Dictionary with performance metrics
        """
        return self.performance_analyzer.get_performance_summary(
            collection_name)

    def compare_strategies(self, collection_name: str, strategy_a: str,
                           strategy_b: str) -> Optional[Dict[str, Any]]:
        """
        Compare performance between two chunking strategies.

        Args:
            collection_name: Name of the collection
            strategy_a: First strategy to compare
            strategy_b: Second strategy to compare

        Returns:
            Comparison results or None if comparison fails
        """
        return self.performance_analyzer.compare_strategies_simple(
            collection_name, strategy_a, strategy_b)

    def find_optimal_strategy(self, collection_name: str,
                              optimization_target: str = "processing_time"):
        """
        Find the optimal chunking strategy.

        Args:
            collection_name: Name of the collection
            optimization_target: Target to optimize
                ('processing_time' or 'memory_usage')

        Returns:
            Name of optimal strategy or None
        """
        return self.performance_analyzer.find_optimal_strategy_simple(
            collection_name, optimization_target)

    def analyze_strategy_performance(self, extraction_method: str,
                                     chunking_strategy: str):
        """
        Analyze performance for a specific strategy-extraction combination.

        Args:
            extraction_method: Extraction method to analyze
            chunking_strategy: Chunking strategy to analyze

        Returns:
            Performance analysis results
        """
        collection_name = self.config.get_collection_name(
            extraction_method, chunking_strategy)

        try:
            # Check if collection exists
            self.client.collections[collection_name].retrieve()
        except typesense.exceptions.ObjectNotFound:
            logger.error("Collection %s not found", collection_name)
            return {}

        return self.get_performance_summary(collection_name)
