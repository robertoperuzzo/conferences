#!/usr/bin/env python3
"""
Demo script for chunking strategies using real preprocessed data.

This script processes all available preprocessed documents with all chunking
strategies, generating separate output files for each strategy-parser-document
combination and displaying comprehensive performance metrics.

Features:
- Individual files per strategy-parser-document combination
- Performance monitoring (CPU, Memory, GPU)
- Comprehensive metrics display
- CLI filtering options

Usage:
    python scripts/demo_chunking.py
    python scripts/demo_chunking.py --strategies=semantic,fixed_size
    python scripts/demo_chunking.py --methods=pypdf,unstructured
    python scripts/demo_chunking.py --no-metrics
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import psutil
from src.chunker.pipeline import ChunkingPipeline
from src.chunker.models import ProcessedDocument
from src.chunker.config import get_default_config
import argparse
import json
import logging
import sys
import time
import traceback
import statistics as py_statistics
from pathlib import Path

# Add the workspace root to Python path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import chunker modules

# Try to import GPU monitoring libraries
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


# Statistical utilities for enhanced metrics
class StatisticalUtils:
    """Utility class for calculating statistical metrics."""

    @staticmethod
    def safe_divide(numerator: float, denominator: float) -> float:
        """Safely divide two numbers, returning 0 if denominator is 0."""
        return numerator / denominator if denominator != 0 else 0

    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, float]:
        """Calculate comprehensive statistics for a list of values."""
        if not values:
            return {
                'mean': 0, 'median': 0, 'std_dev': 0,
                'min': 0, 'max': 0, 'p25': 0, 'p75': 0
            }

        quartiles = py_statistics.quantiles(
            values, n=4) if len(values) >= 4 else None
        return {
            'mean': py_statistics.mean(values),
            'median': py_statistics.median(values),
            'std_dev': py_statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'p25': quartiles[0] if quartiles else min(values),
            'p75': quartiles[2] if quartiles else max(values)
        }

    @staticmethod
    def format_number(value: float, precision: int = 1) -> str:
        """Format a number with appropriate precision."""
        if value == 0:
            return "0"
        elif value < 0.1:
            return f"{value:.3f}"
        elif value < 1:
            return f"{value:.2f}"
        else:
            return f"{value:.{precision}f}"

    @staticmethod
    def format_size(bytes_value: float) -> str:
        """Format byte values in appropriate units."""
        if bytes_value < 1024:
            return f"{bytes_value:.0f}B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value/1024:.1f}KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value/(1024*1024):.1f}MB"
        else:
            return f"{bytes_value/(1024*1024*1024):.1f}GB"


class TableFormatter:
    """Utility class for creating well-formatted tables."""

    @staticmethod
    def calculate_column_widths(headers: List[str],
                                rows: List[List[str]]) -> List[int]:
        """Calculate optimal column widths based on content."""
        widths = [len(header) for header in headers]

        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        # Add padding
        return [w + 2 for w in widths]

    @staticmethod
    def format_row(values: List[str], widths: List[int],
                   alignments: List[str] = None) -> str:
        """Format a single row with proper alignment."""
        if not alignments:
            alignments = ['<'] * len(values)

        formatted_cells = []
        for value, width, align in zip(values, widths, alignments):
            if align == '>':
                formatted_cells.append(f"{value:>{width}}")
            elif align == '^':
                formatted_cells.append(f"{value:^{width}}")
            else:
                formatted_cells.append(f"{value:<{width}}")

        return "|".join(formatted_cells)

    @staticmethod
    def create_separator(widths: List[int]) -> str:
        """Create a separator line for the table."""
        return "+".join(["-" * width for width in widths])


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance metrics during processing."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.start_cpu_percent = None
        self.start_gpu_util = None
        self.start_gpu_memory = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu_percent = self.process.cpu_percent()

        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    self.start_gpu_util = gpu.load * 100
                    self.start_gpu_memory = gpu.memoryUsed
                else:
                    self.start_gpu_util = 0.0
                    self.start_gpu_memory = 0.0
            except Exception:
                self.start_gpu_util = 0.0
                self.start_gpu_memory = 0.0
        else:
            self.start_gpu_util = 0.0
            self.start_gpu_memory = 0.0

    def get_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = self.process.cpu_percent()

        gpu_util = 0.0
        gpu_memory = 0.0

        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_util = gpu.load * 100
                    gpu_memory = gpu.memoryUsed
            except Exception:
                pass

        return {
            'processing_time': end_time - self.start_time if self.start_time else 0,
            'memory_usage': max(end_memory, self.start_memory or 0),
            'cpu_usage_percent': cpu_percent,
            'gpu_usage_percent': gpu_util,
            'gpu_memory_usage': gpu_memory
        }


def validate_json(file_path: Path) -> Dict[str, Any]:
    """Validate JSON file and load its content without modifying it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully validated JSON file: {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        logger.error(f"Error at line {e.lineno}, column {e.colno}")
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def load_preprocessed_document(file_path: Path) -> ProcessedDocument:
    """Load a preprocessed document from JSON file with error recovery."""
    logger.info(f"Loading preprocessed document: {file_path}")

    try:
        data = validate_json(file_path)

        # Extract document info
        doc_id = data.get('document_id', file_path.stem)
        title = data.get('title', 'Unknown Title')
        content = data.get('full_text', data.get('content', ''))

        # Handle different preprocessing formats
        if isinstance(content, list):
            # If content is list of elements (from unstructured)
            text_content = '\n'.join([
                elem.get('text', str(elem)) if isinstance(elem, dict)
                else str(elem)
                for elem in content
            ])
        else:
            text_content = str(content)

        # Validate we have meaningful content
        if len(text_content.strip()) < 10:
            raise ValueError(
                f"Document content too short: {len(text_content)} characters")

        # Extract elements if available (for unstructured processing)
        elements = None
        if ('method_specific_data' in data and
                'elements' in data['method_specific_data']):
            elements = data['method_specific_data']['elements']
        elif 'elements' in data:
            elements = data['elements']

        # Create ProcessedDocument
        doc = ProcessedDocument(
            document_id=doc_id,
            title=title,
            authors=[],  # Empty list as default
            abstract='',  # Empty string as default
            full_text=text_content,
            elements=elements,
            metadata={
                'source_file': str(file_path),
                'preprocessing_method': file_path.parent.name,
                'original_data_keys': list(data.keys())
            }
        )

        logger.info(
            f"Successfully loaded document '{title}' "
            f"with {len(text_content)} characters")
        return doc

    except Exception as e:
        logger.error(f"Failed to load document from {file_path}: {e}")
        raise


def find_available_files(data_dir: Path,
                         methods_filter: Optional[List[str]] = None) -> List[Path]:
    """Find all available preprocessed files."""
    available_files = []

    # Look for files in different preprocessing methods
    for method_dir in ['pypdf', 'unstructured', 'marker', 'markitdown']:
        if methods_filter and method_dir not in methods_filter:
            continue

        method_path = data_dir / method_dir
        if method_path.exists():
            for file_path in method_path.glob("*.json"):
                available_files.append(file_path)

    return sorted(available_files, key=lambda x: x.stat().st_mtime, reverse=True)


def is_strategy_compatible(strategy_name: str,
                           document: ProcessedDocument) -> bool:
    """Check if strategy is compatible with document's preprocessing method."""
    preprocessing_method = document.metadata.get('preprocessing_method', '')

    # sliding_unstructured requires documents processed with unstructured
    if strategy_name == 'sliding_unstructured':
        return preprocessing_method == 'unstructured'

    # All other strategies work with any preprocessing method
    return True


def process_single_combination(document: ProcessedDocument,
                               strategy_name: str,
                               strategy_config: Dict[str, Any],
                               output_dir: Path) -> Dict[str, Any]:
    """Process a single strategy-parser-document combination."""

    # Create pipeline for single strategy
    config = get_default_config()
    config.strategy_configs[strategy_name] = strategy_config
    config.enabled_strategies = [strategy_name]

    pipeline = ChunkingPipeline(config)

    # Start performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    try:
        # Process document
        results = pipeline.process_document(document)
        result = results.get(strategy_name)

        if not result:
            raise ValueError(f"No results for strategy {strategy_name}")

        # Check if the strategy failed due to missing dependencies
        if not result.success:
            raise ValueError(
                f"Strategy {strategy_name} failed: {result.error_message}"
            )

        # Get performance metrics
        metrics = monitor.get_metrics()

        # Calculate chunk statistics
        chunks = result.chunks if hasattr(result, 'chunks') else []
        chunk_sizes = [len(chunk.content) for chunk in chunks]

        statistics = {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0
        }

        # Prepare output data
        output_data = {
            'document_info': {
                'document_id': document.document_id,
                'title': document.title,
                'content_length': len(document.full_text),
                'source_file': document.metadata.get('source_file', ''),
                'preprocessing_method': document.metadata.get('preprocessing_method', '')
            },
            'strategy_config': {
                'strategy_name': strategy_name,
                'parameters': strategy_config
            },
            'results': {
                'chunks': [
                    {
                        'content': chunk.content,
                        'metadata': chunk.metadata,
                        'start_char': getattr(chunk, 'start_char', None),
                        'end_char': getattr(chunk, 'end_char', None)
                    }
                    for chunk in chunks
                ],
                'statistics': statistics,
                'error': result.error if hasattr(result, 'error') else None
            },
            'processing_metadata': {
                'timestamp': datetime.now().isoformat(),
                'processing_time': metrics['processing_time'],
                'memory_usage': metrics['memory_usage'],
                'cpu_usage_percent': metrics['cpu_usage_percent'],
                'gpu_usage_percent': metrics['gpu_usage_percent'],
                'gpu_memory_usage': metrics['gpu_memory_usage']
            }
        }

        # Save individual file
        preprocessing_method = document.metadata.get(
            'preprocessing_method', 'unknown')
        filename = f"{document.document_id}_{preprocessing_method}_{strategy_name}.json"
        output_file = output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved results to {output_file}")

        # Return performance data for summary
        return {
            'document_id': document.document_id,
            'preprocessing_method': preprocessing_method,
            'strategy_name': strategy_name,
            'filename': filename,
            'metrics': metrics,
            'statistics': statistics,
            'error': result.error if hasattr(result, 'error') else None
        }

    except Exception as e:
        logger.error(
            f"Error processing {strategy_name} on {document.document_id}: {e}")
        error_metrics = monitor.get_metrics()
        return {
            'document_id': document.document_id,
            'preprocessing_method': document.metadata.get('preprocessing_method', 'unknown'),
            'strategy_name': strategy_name,
            'filename': None,
            'metrics': error_metrics,
            'statistics': {'total_chunks': 0, 'avg_chunk_size': 0, 'min_chunk_size': 0, 'max_chunk_size': 0},
            'error': str(e)
        }


def display_performance_summary(results: List[Dict[str, Any]],
                                show_metrics: bool = True):
    """Display comprehensive performance summary with enhanced formatting."""
    if not show_metrics or not results:
        return

    print("\n" + "="*120)
    print("                              ENHANCED PERFORMANCE SUMMARY")
    print("="*120)

    # Separate successful and failed results
    successful_results = [r for r in results if not r.get('error')]
    failed_results = [r for r in results if r.get('error')]

    if successful_results:
        _display_detailed_results(successful_results)
        _display_strategy_comparison(successful_results)
        _display_document_analysis(successful_results)
        _display_resource_utilization(successful_results)

    if failed_results:
        _display_error_analysis(failed_results)

    _display_overall_summary(successful_results, failed_results)


def _display_detailed_results(results: List[Dict[str, Any]]):
    """Display detailed results with enhanced table formatting."""
    print("\n📊 DETAILED PERFORMANCE RESULTS")
    print("-" * 120)

    # Group by document
    documents = {}
    for result in results:
        doc_id = result['document_id']
        if doc_id not in documents:
            documents[doc_id] = []
        documents[doc_id].append(result)

    for doc_id, doc_results in documents.items():
        print(f"\n📄 Document: {doc_id}")

        # Prepare table data
        headers = [
            "Strategy/Method", "Time (s)", "RAM (MB)", "CPU %",
            "GPU %", "GPU Mem", "Chunks", "Avg Size", "Min/Max Size"
        ]

        rows = []
        for result in doc_results:
            metrics = result['metrics']
            stats = result['statistics']

            strategy_method = f"{result['preprocessing_method']}/{result['strategy_name']}"
            time_val = StatisticalUtils.format_number(
                metrics['processing_time'], 2)
            ram_val = StatisticalUtils.format_number(
                metrics['memory_usage'], 1)
            cpu_val = StatisticalUtils.format_number(
                metrics['cpu_usage_percent'], 1)
            gpu_val = StatisticalUtils.format_number(
                metrics['gpu_usage_percent'], 1)
            gpu_mem = StatisticalUtils.format_size(
                metrics['gpu_memory_usage'] * 1024 * 1024) if metrics['gpu_memory_usage'] > 0 else "0"
            chunks_val = str(stats['total_chunks'])
            avg_size = StatisticalUtils.format_number(
                stats['avg_chunk_size'], 0)
            min_max = f"{stats['min_chunk_size']:.0f}/{stats['max_chunk_size']:.0f}"

            rows.append([
                strategy_method, time_val, ram_val, cpu_val,
                gpu_val, gpu_mem, chunks_val, avg_size, min_max
            ])

        # Calculate column widths and display table
        widths = TableFormatter.calculate_column_widths(headers, rows)
        alignments = ['<', '>', '>', '>', '>', '>', '>', '>', '>']

        # Print table
        print("  " + TableFormatter.format_row(headers, widths, alignments))
        print("  " + TableFormatter.create_separator(widths))

        for row in rows:
            print("  " + TableFormatter.format_row(row, widths, alignments))


def _display_strategy_comparison(results: List[Dict[str, Any]]):
    """Display strategy comparison matrix."""
    print("\n🔄 STRATEGY COMPARISON MATRIX")
    print("-" * 120)

    # Group by strategy
    strategies = {}
    for result in results:
        strategy = result['strategy_name']
        if strategy not in strategies:
            strategies[strategy] = []
        strategies[strategy].append(result)

    headers = [
        "Strategy", "Avg Time", "Avg RAM", "Avg Chunks",
        "Avg Size", "Success Rate", "Efficiency", "Best For"
    ]

    rows = []
    for strategy, strategy_results in strategies.items():
        # Calculate averages
        times = [r['metrics']['processing_time'] for r in strategy_results]
        rams = [r['metrics']['memory_usage'] for r in strategy_results]
        chunk_counts = [r['statistics']['total_chunks']
                        for r in strategy_results]
        chunk_sizes = [r['statistics']['avg_chunk_size']
                       for r in strategy_results if r['statistics']['avg_chunk_size'] > 0]

        time_stats = StatisticalUtils.calculate_stats(times)
        ram_stats = StatisticalUtils.calculate_stats(rams)

        avg_time = StatisticalUtils.format_number(time_stats['mean'], 2)
        avg_ram = StatisticalUtils.format_number(ram_stats['mean'], 1)
        avg_chunks = StatisticalUtils.format_number(
            sum(chunk_counts) / len(chunk_counts), 0)
        avg_size = StatisticalUtils.format_number(
            sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0, 0)
        success_rate = "100%"  # All in successful_results

        # Calculate efficiency (chunks per second per MB)
        efficiency = sum(chunk_counts) / (sum(times) * sum(rams)
                                          ) if sum(times) > 0 and sum(rams) > 0 else 0
        efficiency_str = StatisticalUtils.format_number(
            efficiency * 1000, 3)  # Scale for readability

        # Determine best use case
        best_for = _get_strategy_recommendation(
            strategy, time_stats['mean'], chunk_counts)

        rows.append([
            strategy, avg_time + "s", avg_ram + "MB", avg_chunks,
            avg_size, success_rate, efficiency_str, best_for
        ])

    # Display table
    widths = TableFormatter.calculate_column_widths(headers, rows)
    alignments = ['<', '>', '>', '>', '>', '>', '>', '<']

    print("  " + TableFormatter.format_row(headers, widths, alignments))
    print("  " + TableFormatter.create_separator(widths))

    for row in rows:
        print("  " + TableFormatter.format_row(row, widths, alignments))


def _get_strategy_recommendation(strategy: str, avg_time: float, chunk_counts: List[int]) -> str:
    """Get recommendation for strategy based on performance characteristics."""
    recommendations = {
        'fixed_size': 'Speed',
        'sliding_langchain': 'Balance',
        'sliding_unstructured': 'Structure',
        'semantic': 'Quality'
    }

    base_rec = recommendations.get(strategy, 'General')

    if avg_time < 1.0:
        return f"{base_rec}/Fast"
    elif avg_time > 5.0:
        return f"{base_rec}/Thorough"
    else:
        return base_rec


def _display_document_analysis(results: List[Dict[str, Any]]):
    """Display document processing efficiency analysis."""
    print("\n📈 DOCUMENT PROCESSING EFFICIENCY")
    print("-" * 120)

    # Group by document
    docs = {}
    for result in results:
        doc_id = result['document_id']
        if doc_id not in docs:
            docs[doc_id] = []
        docs[doc_id].append(result)

    # Calculate document statistics
    doc_stats = []
    for doc_id, doc_results in docs.items():
        times = [r['metrics']['processing_time'] for r in doc_results]
        rams = [r['metrics']['memory_usage'] for r in doc_results]

        avg_time = sum(times) / len(times)
        avg_ram = sum(rams) / len(rams)

        doc_stats.append({
            'doc_id': doc_id,
            'avg_time': avg_time,
            'avg_ram': avg_ram,
            'strategy_count': len(doc_results)
        })

    # Sort by processing time
    doc_stats.sort(key=lambda x: x['avg_time'])

    print(
        f"  📝 Fastest Document: {doc_stats[0]['doc_id']} ({StatisticalUtils.format_number(doc_stats[0]['avg_time'], 2)}s avg)")
    print(
        f"  🐌 Slowest Document: {doc_stats[-1]['doc_id']} ({StatisticalUtils.format_number(doc_stats[-1]['avg_time'], 2)}s avg)")

    # Memory analysis
    doc_stats.sort(key=lambda x: x['avg_ram'])
    print(
        f"  💾 Most Memory Efficient: {doc_stats[0]['doc_id']} ({StatisticalUtils.format_number(doc_stats[0]['avg_ram'], 1)}MB avg)")
    print(
        f"  🔥 Highest Memory Usage: {doc_stats[-1]['doc_id']} ({StatisticalUtils.format_number(doc_stats[-1]['avg_ram'], 1)}MB avg)")


def _display_resource_utilization(results: List[Dict[str, Any]]):
    """Display resource utilization summary."""
    print("\n⚡ RESOURCE UTILIZATION SUMMARY")
    print("-" * 120)

    # Collect all metrics
    times = [r['metrics']['processing_time'] for r in results]
    rams = [r['metrics']['memory_usage'] for r in results]
    cpus = [r['metrics']['cpu_usage_percent'] for r in results]
    gpus = [r['metrics']['gpu_usage_percent']
            for r in results if r['metrics']['gpu_usage_percent'] > 0]

    time_stats = StatisticalUtils.calculate_stats(times)
    ram_stats = StatisticalUtils.calculate_stats(rams)
    cpu_stats = StatisticalUtils.calculate_stats(cpus)

    print(f"  ⏱️  Processing Time: {StatisticalUtils.format_number(time_stats['mean'], 2)}s avg, "
          f"{StatisticalUtils.format_number(time_stats['median'], 2)}s median "
          f"({StatisticalUtils.format_number(time_stats['min'], 2)}s - {StatisticalUtils.format_number(time_stats['max'], 2)}s)")

    print(f"  💾 Memory Usage: {StatisticalUtils.format_number(ram_stats['mean'], 1)}MB avg, "
          f"{StatisticalUtils.format_number(ram_stats['median'], 1)}MB median "
          f"({StatisticalUtils.format_number(ram_stats['min'], 1)}MB - {StatisticalUtils.format_number(ram_stats['max'], 1)}MB)")

    print(f"  🖥️  CPU Usage: {StatisticalUtils.format_number(cpu_stats['mean'], 1)}% avg, "
          f"{StatisticalUtils.format_number(cpu_stats['median'], 1)}% median")

    if gpus:
        gpu_stats = StatisticalUtils.calculate_stats(gpus)
        print(f"  🎮 GPU Usage: {StatisticalUtils.format_number(gpu_stats['mean'], 1)}% avg, "
              f"{StatisticalUtils.format_number(gpu_stats['median'], 1)}% median")

    # Performance recommendations
    print("\n  💡 OPTIMIZATION RECOMMENDATIONS:")
    if ram_stats['max'] > 1000:
        print(
            "    • Consider processing documents in smaller batches to reduce memory usage")
    if time_stats['max'] > 10:
        print(
            "    • Some documents are slow to process - consider preprocessing optimization")
    if cpu_stats['mean'] < 50:
        print(
            "    • CPU utilization is low - parallel processing could improve performance")


def _display_error_analysis(failed_results: List[Dict[str, Any]]):
    """Display analysis of failed processing attempts."""
    print("\n❌ ERROR ANALYSIS")
    print("-" * 120)

    print(f"  Total Failed Attempts: {len(failed_results)}")

    # Group errors by type
    error_types = {}
    strategy_errors = {}

    for result in failed_results:
        error_msg = str(result.get('error', 'Unknown error'))
        error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg

        if error_type not in error_types:
            error_types[error_type] = 0
        error_types[error_type] += 1

        strategy = result['strategy_name']
        if strategy not in strategy_errors:
            strategy_errors[strategy] = 0
        strategy_errors[strategy] += 1

    # Display error breakdown
    if error_types:
        print("    Error Types:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {error_type}: {count} occurrences")

    if strategy_errors:
        print("    Errors by Strategy:")
        for strategy, count in sorted(strategy_errors.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {strategy}: {count} failures")


def _display_overall_summary(successful_results: List[Dict[str, Any]],
                             failed_results: List[Dict[str, Any]]):
    """Display overall summary statistics."""
    total_combinations = len(successful_results) + len(failed_results)
    success_rate = (len(successful_results) /
                    total_combinations * 100) if total_combinations > 0 else 0

    print(f"\n🎯 OVERALL SUMMARY")
    print("=" * 120)

    if successful_results:
        total_chunks = sum(r['statistics']['total_chunks']
                           for r in successful_results)
        total_time = sum(r['metrics']['processing_time']
                         for r in successful_results)
        peak_ram = max(r['metrics']['memory_usage']
                       for r in successful_results)

        print(
            f"  📊 Total Combinations: {total_combinations} | Success Rate: {StatisticalUtils.format_number(success_rate, 1)}%")
        print(f"  📦 Total Chunks Generated: {total_chunks:,}")
        print(
            f"  ⏱️  Total Processing Time: {StatisticalUtils.format_number(total_time, 2)}s")
        print(
            f"  💾 Peak Memory Usage: {StatisticalUtils.format_number(peak_ram, 1)}MB")
        print(
            f"  ⚡ Average Throughput: {StatisticalUtils.format_number(total_chunks / total_time if total_time > 0 else 0, 1)} chunks/second")
    else:
        print(
            f"  ❌ No successful processing attempts out of {total_combinations} total combinations")

    print("=" * 120)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demo script for chunking strategies with performance monitoring"
    )

    parser.add_argument(
        '--strategies',
        type=str,
        help='Comma-separated list of strategies to run (e.g., semantic,fixed_size)'
    )

    parser.add_argument(
        '--methods',
        type=str,
        help='Comma-separated list of preprocessing methods to include (e.g., pypdf,unstructured)'
    )

    parser.add_argument(
        '--no-metrics',
        action='store_true',
        help='Skip performance metrics display'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    try:
        args = parse_arguments()

        print("🚀 CHUNKING STRATEGIES DEMONSTRATION")
        print("Processing all available documents with individual output files\n")

        # Parse CLI filters
        strategies_filter = None
        if args.strategies:
            strategies_filter = [s.strip() for s in args.strategies.split(',')]

        methods_filter = None
        if args.methods:
            methods_filter = [m.strip() for m in args.methods.split(',')]

        # Find available preprocessed files
        data_dir = Path(__file__).parent.parent / "data" / "processed"
        available_files = find_available_files(data_dir, methods_filter)

        if not available_files:
            logger.error("No preprocessed files found!")
            logger.error(
                "Please run preprocessing first or check data directory.")
            return

        print(f"Found {len(available_files)} preprocessed files")

        # Configure chunking strategies
        strategies_config = {
            "fixed_size": {
                "chunk_size": 1000,
                "chars_per_token": 4.0
            },
            "sliding_langchain": {
                "chunk_size": 1000,
                "chunk_overlap": 80,
                "separators": ["\n\n", "\n", " ", ""],
                "keep_separator": False,
                "is_separator_regex": False
            },
            "sliding_unstructured": {
                "max_elements_per_chunk": 10,
                "overlap_percentage": 0.2,
                "priority_elements": ["Title", "Header", "NarrativeText"],
                "respect_boundaries": True
            },
            "semantic": {
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "similarity_threshold": 0.8,
                "min_chunk_size": 200,
                "max_chunk_size": 2000,
                "batch_size": 32
            }
        }

        # Filter strategies if specified
        if strategies_filter:
            strategies_config = {
                k: v for k, v in strategies_config.items()
                if k in strategies_filter
            }

        # Ensure output directory exists
        output_dir = Path(__file__).parent.parent / "data" / "chunks"
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Output directory: {output_dir}")
        print(f"Strategies to process: {list(strategies_config.keys())}")

        # Process all combinations
        all_results = []
        total_combinations = 0
        successful_combinations = 0

        for file_path in available_files:
            try:
                # Load document
                document = load_preprocessed_document(file_path)
                print(f"\nProcessing document: {document.title}")

                # Process each strategy
                for strategy_name, strategy_config in strategies_config.items():
                    # Check if strategy is compatible with document
                    if not is_strategy_compatible(strategy_name, document):
                        print(f"  - Strategy: {strategy_name} "
                              f"(skipped - incompatible)")
                        continue

                    print(f"  - Strategy: {strategy_name}")
                    total_combinations += 1

                    result = process_single_combination(
                        document, strategy_name, strategy_config, output_dir
                    )
                    all_results.append(result)

                    if not result['error']:
                        successful_combinations += 1

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        # Display summary
        print("\n✅ PROCESSING COMPLETE")
        print(f"Total combinations processed: {total_combinations}")
        print(f"Successful: {successful_combinations}")
        print(f"Failed: {total_combinations - successful_combinations}")

        # Display performance summary
        display_performance_summary(all_results, not args.no_metrics)

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
