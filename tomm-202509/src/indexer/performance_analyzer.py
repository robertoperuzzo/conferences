"""
Performance analytics module for analyzing chunking strategy performance.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import typesense

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    strategy: str
    extraction_method: str
    document_count: int
    total_chunks: int
    avg_processing_time: float
    avg_memory_usage: float
    avg_cpu_usage: float
    avg_gpu_usage: float
    avg_chunk_size: float


@dataclass
class PerformanceComparison:
    """Data class for comparing performance between strategies."""
    strategy_a: str
    strategy_b: str
    extraction_method: str
    processing_time_ratio: float
    memory_usage_ratio: float
    faster_strategy: str
    more_memory_efficient: str


class PerformanceAnalyzer:
    """Analyzer for chunking strategy performance metrics."""

    def __init__(self, client: typesense.Client):
        """Initialize performance analyzer."""
        self.client = client

    def get_performance_summary(self, collection_name: str) -> Dict[str, Any]:
        """
        Get a summary of performance metrics for all strategies.

        Args:
            collection_name: Typesense collection name

        Returns:
            Dictionary with performance summary
        """
        try:
            # Simple aggregation query to get basic stats
            search_params = {
                'q': '*',
                'query_by': 'content',
                'per_page': 250,  # Get a sample of documents
                'sort_by': 'processing_time:desc'
            }

            response = self.client.collections[collection_name].documents.search(
                search_params)

            return self._analyze_performance_data(response)

        except Exception as e:
            logger.error("Error getting performance summary: %s", e)
            return {}

    def compare_strategies_simple(self, collection_name: str,
                                  strategy_a: str,
                                  strategy_b: str) -> Optional[Dict[str, Any]]:
        """
        Simple comparison between two strategies.

        Args:
            collection_name: Typesense collection name
            strategy_a: First strategy to compare
            strategy_b: Second strategy to compare

        Returns:
            Comparison results dictionary
        """
        try:
            # Get documents for each strategy
            params_a = {
                'q': '*',
                'query_by': 'content',
                'filter_by': f'chunking_strategy:={strategy_a}',
                'per_page': 100
            }

            params_b = {
                'q': '*',
                'query_by': 'content',
                'filter_by': f'chunking_strategy:={strategy_b}',
                'per_page': 100
            }

            response_a = self.client.collections[collection_name].documents.search(
                params_a)
            response_b = self.client.collections[collection_name].documents.search(
                params_b)

            stats_a = self._calculate_stats(response_a)
            stats_b = self._calculate_stats(response_b)

            if not stats_a or not stats_b:
                return None

            return {
                'strategy_a': strategy_a,
                'strategy_b': strategy_b,
                'stats_a': stats_a,
                'stats_b': stats_b,
                'faster_strategy': (strategy_a if stats_a['avg_processing_time'] <
                                    stats_b['avg_processing_time'] else strategy_b),
                'more_memory_efficient': (strategy_a if stats_a['avg_memory_usage'] <
                                          stats_b['avg_memory_usage'] else strategy_b)
            }

        except Exception as e:
            logger.error("Error comparing strategies: %s", e)
            return None

    def find_optimal_strategy_simple(self, collection_name: str,
                                     optimization_target: str = "processing_time") -> Optional[str]:
        """
        Find optimal strategy based on performance target.

        Args:
            collection_name: Typesense collection name
            optimization_target: 'processing_time' or 'memory_usage'

        Returns:
            Name of optimal strategy
        """
        try:
            summary = self.get_performance_summary(collection_name)

            if not summary.get('by_strategy'):
                return None

            strategy_stats = summary['by_strategy']

            if optimization_target == "processing_time":
                optimal = min(strategy_stats.items(),
                              key=lambda x: x[1]['avg_processing_time'])
            elif optimization_target == "memory_usage":
                optimal = min(strategy_stats.items(),
                              key=lambda x: x[1]['avg_memory_usage'])
            else:
                return None

            return optimal[0]

        except Exception as e:
            logger.error("Error finding optimal strategy: %s", e)
            return None

    def _analyze_performance_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance data from search response."""
        hits = response.get('hits', [])

        if not hits:
            return {}

        # Group by strategy
        by_strategy = {}
        by_extraction = {}

        for hit in hits:
            doc = hit.get('document', {})
            strategy = doc.get('chunking_strategy', 'unknown')
            extraction = doc.get('extraction_method', 'unknown')

            # Add to strategy groups
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(doc)

            # Add to extraction groups
            if extraction not in by_extraction:
                by_extraction[extraction] = []
            by_extraction[extraction].append(doc)

        # Calculate stats for each group
        strategy_stats = {}
        for strategy, docs in by_strategy.items():
            strategy_stats[strategy] = self._calculate_stats_from_docs(docs)

        extraction_stats = {}
        for extraction, docs in by_extraction.items():
            extraction_stats[extraction] = self._calculate_stats_from_docs(
                docs)

        return {
            'total_documents': len(hits),
            'by_strategy': strategy_stats,
            'by_extraction': extraction_stats
        }

    def _calculate_stats(self, response: Dict[str, Any]) -> Dict[str, float]:
        """Calculate statistics from search response."""
        hits = response.get('hits', [])
        return self._calculate_stats_from_docs([hit.get('document', {}) for hit in hits])

    def _calculate_stats_from_docs(self, docs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistics from document list."""
        if not docs:
            return {}

        processing_times = [doc.get('processing_time', 0) for doc in docs]
        memory_usages = [doc.get('memory_usage', 0) for doc in docs]
        cpu_usages = [doc.get('cpu_usage_percent', 0) for doc in docs]
        content_lengths = [len(doc.get('content', '')) for doc in docs]

        return {
            'document_count': len(docs),
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'avg_memory_usage': sum(memory_usages) / len(memory_usages),
            'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages),
            'avg_content_length': sum(content_lengths) / len(content_lengths),
            'min_processing_time': min(processing_times) if processing_times else 0,
            'max_processing_time': max(processing_times) if processing_times else 0,
            'min_memory_usage': min(memory_usages) if memory_usages else 0,
            'max_memory_usage': max(memory_usages) if memory_usages else 0
        }
