"""Chunking pipeline orchestration module.

This module provides the main ChunkingPipeline class that coordinates
chunking across multiple strategies and manages the overall process.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

from .models import (
    ProcessedDocument, ChunkingResult, ChunkingConfig
)
from .config import get_default_config
from .strategies import get_strategy_class
from .utils import validate_chunk_quality


logger = logging.getLogger(__name__)


class ChunkingPipeline:
    """Main pipeline for coordinating chunking strategies.

    This class orchestrates the chunking process across multiple strategies,
    handles batch processing, and manages output generation.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        """Initialize the chunking pipeline.

        Args:
            config: Optional chunking configuration.
                   Uses defaults if not provided.
        """
        self.config = config or get_default_config()
        self._strategies = {}

        # Initialize enabled strategies
        self._initialize_strategies()

        logger.info(
            f"Initialized chunking pipeline with strategies: "
            f"{list(self._strategies.keys())}"
        )

    def _initialize_strategies(self):
        """Initialize all enabled chunking strategies."""
        for strategy_name in self.config.enabled_strategies:
            try:
                strategy_class = get_strategy_class(strategy_name)
                strategy_config = self.config.get_strategy_config(
                    strategy_name
                )

                strategy = strategy_class(strategy_config)
                self._strategies[strategy_name] = strategy

                logger.info(f"Initialized strategy: {strategy_name}")

            except Exception as e:
                logger.error(
                    f"Failed to initialize strategy {strategy_name}: {e}"
                )
                # Continue with other strategies
                continue

    def process_document(
        self,
        document: ProcessedDocument,
        strategies: Optional[List[str]] = None
    ) -> Dict[str, ChunkingResult]:
        """Process a single document with specified strategies.

        Args:
            document: The document to process
            strategies: Optional list of strategy names to use.
                       Uses all enabled strategies if not provided.

        Returns:
            Dictionary mapping strategy names to chunking results
        """
        if strategies is None:
            strategies = list(self._strategies.keys())

        results = {}

        for strategy_name in strategies:
            if strategy_name not in self._strategies:
                logger.warning(
                    f"Strategy {strategy_name} not available, skipping"
                )
                continue

            try:
                strategy = self._strategies[strategy_name]
                result = strategy.process_document_with_stats(document)

                # Update total_chunks in metadata for successful results
                if result.success:
                    for chunk in result.chunks:
                        chunk.metadata['total_chunks'] = len(result.chunks)

                results[strategy_name] = result

                if result.success:
                    logger.info(
                        f"Processed document {document.document_id} with "
                        f"{strategy_name}: {len(result.chunks)} chunks"
                    )
                else:
                    logger.info(
                        f"Processed document {document.document_id} with "
                        f"{strategy_name}: 0 chunks (failed: "
                        f"{result.error_message})"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to process document {document.document_id} "
                    f"with strategy {strategy_name}: {e}"
                )
                continue

        return results

    def process_documents_batch(
        self,
        documents: List[ProcessedDocument],
        strategies: Optional[List[str]] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, Dict[str, ChunkingResult]]:
        """Process multiple documents in parallel.

        Args:
            documents: List of documents to process
            strategies: Optional list of strategy names to use
            max_workers: Maximum number of parallel workers

        Returns:
            Nested dictionary: {document_id: {strategy_name: ChunkingResult}}
        """
        if not documents:
            return {}

        max_workers = max_workers or self.config.max_workers
        strategies = strategies or list(self._strategies.keys())

        results = {}

        logger.info(
            f"Processing {len(documents)} documents with "
            f"{len(strategies)} strategies using {max_workers} workers"
        )

        # Process documents in batches
        batch_size = self.config.batch_size
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Process batch
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit jobs for each document
                future_to_doc = {
                    executor.submit(
                        self._process_document_with_strategies,
                        doc, strategies
                    ): doc for doc in batch
                }

                # Collect results
                for future in as_completed(future_to_doc):
                    document = future_to_doc[future]
                    try:
                        doc_results = future.result()
                        results[document.document_id] = doc_results

                    except Exception as e:
                        logger.error(
                            f"Failed to process document "
                            f"{document.document_id}: {e}"
                        )
                        results[document.document_id] = {}

            logger.info(f"Completed batch {i//batch_size + 1}")

        return results

    def _process_document_with_strategies(
        self,
        document: ProcessedDocument,
        strategies: List[str]
    ) -> Dict[str, ChunkingResult]:
        """Process a document with multiple strategies (for multiprocessing).

        This method is designed to be called from process pool workers.

        Args:
            document: Document to process
            strategies: List of strategy names

        Returns:
            Dictionary of strategy results
        """
        # Re-initialize strategies in worker process
        self._initialize_strategies()

        return self.process_document(document, strategies)

    def save_results(
        self,
        results: Dict[str, Dict[str, ChunkingResult]],
        output_directory: Optional[Path] = None,
        include_quality_metrics: bool = True
    ) -> Dict[str, Path]:
        """Save chunking results to files.

        Args:
            results: Nested dictionary of chunking results
            output_directory: Directory to save results
            include_quality_metrics: Whether to include quality analysis

        Returns:
            Dictionary mapping strategy names to output file paths
        """
        output_dir = output_directory or self.config.output_directory
        if not output_dir:
            output_dir = Path("./chunks")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Group results by strategy
        strategy_results = {}
        for doc_id, doc_results in results.items():
            for strategy_name, result in doc_results.items():
                if strategy_name not in strategy_results:
                    strategy_results[strategy_name] = []
                strategy_results[strategy_name].append(result)

        # Save each strategy's results
        for strategy_name, strategy_chunk_results in strategy_results.items():
            output_file = output_dir / \
                f"{strategy_name}_chunks_{timestamp}.json"

            # Compile all chunks and metadata
            all_chunks = []
            processing_stats = {
                'total_documents': len(strategy_chunk_results),
                'total_chunks': 0,
                'total_processing_time': 0,
                'successful_documents': 0,
                'failed_documents': 0,
                'quality_metrics': {} if include_quality_metrics else None
            }

            for result in strategy_chunk_results:
                if result.success:
                    processing_stats['successful_documents'] += 1
                    processing_stats['total_chunks'] += len(result.chunks)
                    processing_stats['total_processing_time'] += (
                        result.statistics.processing_time
                    )

                    for chunk in result.chunks:
                        chunk_data = chunk.to_dict()

                        # Add quality metrics if requested
                        if include_quality_metrics:
                            quality = validate_chunk_quality(chunk)
                            chunk_data['quality_metrics'] = quality

                        all_chunks.append(chunk_data)
                else:
                    processing_stats['failed_documents'] += 1

            # Calculate quality statistics
            if include_quality_metrics and all_chunks:
                quality_scores = [
                    chunk['quality_metrics']['quality_score']
                    for chunk in all_chunks
                ]
                processing_stats['quality_metrics'] = {
                    'avg_quality_score': sum(quality_scores) / len(quality_scores),
                    'min_quality_score': min(quality_scores),
                    'max_quality_score': max(quality_scores),
                    'chunks_with_issues': sum(
                        1 for chunk in all_chunks
                        if chunk['quality_metrics']['issues']
                    )
                }

            # Prepare output data
            output_data = {
                'strategy': strategy_name,
                'config': self.config.get_strategy_config(strategy_name),
                'processing_stats': processing_stats,
                'chunks': all_chunks,
                'generated_at': timestamp
            }

            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            saved_files[strategy_name] = output_file
            logger.info(
                f"Saved {len(all_chunks)} chunks for strategy "
                f"{strategy_name} to {output_file}"
            )

        return saved_files

    def generate_comparison_report(
        self,
        results: Dict[str, Dict[str, ChunkingResult]],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate a comparative analysis report across strategies.

        Args:
            results: Nested dictionary of chunking results
            output_path: Optional path to save the report

        Returns:
            Dictionary containing comparison metrics
        """
        if not results:
            return {}

        # Calculate metrics for each strategy
        strategy_metrics = {}

        for doc_id, doc_results in results.items():
            for strategy_name, result in doc_results.items():
                if strategy_name not in strategy_metrics:
                    strategy_metrics[strategy_name] = {
                        'total_documents': 0,
                        'successful_documents': 0,
                        'total_chunks': 0,
                        'total_processing_time': 0,
                        'chunk_sizes': [],
                        'token_counts': []
                    }

                metrics = strategy_metrics[strategy_name]
                metrics['total_documents'] += 1

                if result.success:
                    metrics['successful_documents'] += 1
                    metrics['total_chunks'] += len(result.chunks)
                    metrics['total_processing_time'] += (
                        result.statistics.processing_time
                    )

                    for chunk in result.chunks:
                        metrics['chunk_sizes'].append(len(chunk.content))
                        metrics['token_counts'].append(chunk.token_count)

        # Calculate comparative statistics
        comparison_report = {
            'generated_at': datetime.now().isoformat(),
            'total_documents_processed': len(results),
            'strategies_compared': list(strategy_metrics.keys()),
            'strategy_performance': {}
        }

        for strategy_name, metrics in strategy_metrics.items():
            if metrics['chunk_sizes']:
                avg_chunk_size = sum(
                    metrics['chunk_sizes']) / len(metrics['chunk_sizes'])
                avg_tokens = sum(metrics['token_counts']) / \
                    len(metrics['token_counts'])
            else:
                avg_chunk_size = 0
                avg_tokens = 0

            comparison_report['strategy_performance'][strategy_name] = {
                'success_rate': (
                    metrics['successful_documents'] /
                    metrics['total_documents']
                    if metrics['total_documents'] > 0 else 0
                ),
                'avg_chunks_per_document': (
                    metrics['total_chunks'] / metrics['successful_documents']
                    if metrics['successful_documents'] > 0 else 0
                ),
                'avg_processing_time_per_document': (
                    metrics['total_processing_time'] /
                    metrics['successful_documents']
                    if metrics['successful_documents'] > 0 else 0
                ),
                'avg_chunk_size': avg_chunk_size,
                'avg_token_count': avg_tokens,
                'total_chunks': metrics['total_chunks']
            }

        # Save report if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comparison_report, f, indent=2)

            logger.info(f"Saved comparison report to {output_path}")

        return comparison_report

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())

    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for a specific strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Strategy configuration dictionary
        """
        if strategy_name not in self._strategies:
            raise ValueError(f"Strategy {strategy_name} not available")

        return self._strategies[strategy_name].get_strategy_config()
