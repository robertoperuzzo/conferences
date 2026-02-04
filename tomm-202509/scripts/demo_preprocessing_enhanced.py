#!/usr/bin/env python3
"""
Enhanced PDF Preprocessing Script - ADR-011 Implementation

This script demonstrates the modular extractor architecture by processing 
documents using all four available extraction methods, saving results to JSON,
and providing comprehensive metrics including timing and extraction statistics.
"""

from src.preprocessor import DocumentPreprocessor
import sys
from pathlib import Path
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ProcessingMetrics:
    """Track and calculate processing metrics."""

    def __init__(self):
        self.method_metrics: Dict[str, Dict] = {}

    def start_method(self, method: str):
        """Start timing for a method."""
        if method not in self.method_metrics:
            self.method_metrics[method] = {
                'start_time': None,
                'end_time': None,
                'total_time': 0,
                'documents_processed': 0,
                'total_characters': 0,
                'total_pages': 0,
                'processing_times': [],
                'character_counts': [],
                'errors': 0
            }
        self.method_metrics[method]['start_time'] = time.time()

    def end_method(self, method: str):
        """End timing for a method."""
        if method in self.method_metrics and self.method_metrics[method]['start_time']:
            self.method_metrics[method]['end_time'] = time.time()
            self.method_metrics[method]['total_time'] = (
                self.method_metrics[method]['end_time'] -
                self.method_metrics[method]['start_time']
            )

    def add_document_result(self, method: str, char_count: int, pages: int = 1,
                            processing_time: float = 0, success: bool = True):
        """Add metrics for a processed document."""
        if method not in self.method_metrics:
            return

        metrics = self.method_metrics[method]
        if success:
            metrics['documents_processed'] += 1
            metrics['total_characters'] += char_count
            metrics['total_pages'] += pages
            metrics['character_counts'].append(char_count)
            if processing_time > 0:
                metrics['processing_times'].append(processing_time)
        else:
            metrics['errors'] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        summary = {}

        for method, metrics in self.method_metrics.items():
            avg_chars_per_doc = (
                metrics['total_characters'] / metrics['documents_processed']
                if metrics['documents_processed'] > 0 else 0
            )
            avg_chars_per_page = (
                metrics['total_characters'] / metrics['total_pages']
                if metrics['total_pages'] > 0 else 0
            )
            avg_time_per_doc = (
                sum(metrics['processing_times']) /
                len(metrics['processing_times'])
                if metrics['processing_times'] else metrics['total_time'] / max(1, metrics['documents_processed'])
            )
            avg_time_per_page = (
                metrics['total_time'] / metrics['total_pages']
                if metrics['total_pages'] > 0 else 0
            )

            summary[method] = {
                'total_time': metrics['total_time'],
                'documents_processed': metrics['documents_processed'],
                'total_characters': metrics['total_characters'],
                'total_pages': metrics['total_pages'],
                'errors': metrics['errors'],
                'avg_chars_per_doc': int(avg_chars_per_doc),
                'avg_chars_per_page': int(avg_chars_per_page),
                'avg_time_per_doc': avg_time_per_doc,
                'avg_time_per_page': avg_time_per_page,
                'success_rate': (
                    metrics['documents_processed'] /
                    (metrics['documents_processed'] + metrics['errors']) * 100
                    if (metrics['documents_processed'] + metrics['errors']) > 0 else 0
                )
            }

        return summary


def save_processed_documents(preprocessor: DocumentPreprocessor,
                             processed_docs: List[Dict],
                             method: str) -> str:
    """Save processed documents to method-specific JSON files."""

    # Create method-specific directory
    method_dir = preprocessor.processed_path / method
    method_dir.mkdir(parents=True, exist_ok=True)

    # Save each document individually
    saved_files = []
    for doc_result in processed_docs:
        if doc_result.get('status') == 'success':
            file_path = Path(doc_result['file_path'])

            # Generate output filename
            doc_id = file_path.stem.replace(' ', '_').replace('.', '')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{doc_id}_{timestamp}.json"
            output_path = method_dir / output_filename

            # Prepare document data for saving
            extraction_result = doc_result['extraction_result']

            # Extract title from filename (since it's not in metadata)
            title = file_path.stem.replace('_', ' ').replace('.pdf', '')

            save_data = {
                'document_id': doc_id,
                'original_filename': file_path.name,
                'processed_at': datetime.now().isoformat(),
                'extraction_method': method,
                'title': title,
                'authors': [],  # Default empty list
                'full_text': extraction_result.text,
                'text_length': len(extraction_result.text),
                'metadata': doc_result.get('metadata', {}),
                'performance_metrics': extraction_result.performance_metrics,
                'quality_metrics': extraction_result.quality_metrics,
                'method_specific_data': extraction_result.method_specific_data
            }

            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            saved_files.append(str(output_path))
            print(f"  💾 Saved: {output_path.name}")

    return f"Saved {len(saved_files)} files to {method_dir}"


def estimate_pages(file_path: Path) -> int:
    """Estimate number of pages based on file size (rough approximation)."""
    try:
        # Rough estimation: average PDF page is ~50-100KB
        file_size_kb = file_path.stat().st_size / 1024
        estimated_pages = max(1, int(file_size_kb / 75))  # Use 75KB average
        return estimated_pages
    except:
        return 1  # Default fallback


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def main():
    """Process documents with all available methods and comprehensive metrics."""
    print("Enhanced Document Preprocessing Demo - ADR-011 Implementation")
    print("=" * 65)

    # Initialize preprocessor and metrics tracker
    preprocessor = DocumentPreprocessor()
    metrics = ProcessingMetrics()

    print(f"Available extraction methods: {preprocessor.SUPPORTED_METHODS}")

    # Discover documents
    documents = preprocessor.discover_documents()
    if not documents:
        print("No documents found in data/raw/ directory")
        return

    print(f"\nFound {len(documents)} files:")
    total_estimated_pages = 0
    for doc in documents:
        pages = estimate_pages(doc)
        total_estimated_pages += pages
        print(f"  - {doc.name}")

    print(f"\nTotal estimated pages: {total_estimated_pages}")

    # Process with all available methods
    methods = preprocessor.SUPPORTED_METHODS
    all_results = {}

    for method in methods:
        print(f"\n{'-' * 50}")
        print(f"Processing with {method.upper()} method...")
        print(f"{'-' * 50}")

        try:
            # Start timing
            metrics.start_method(method)

            processed_docs = preprocessor.process_documents(
                method=method,
                track_performance=True
            )

            # End timing
            metrics.end_method(method)

            all_results[method] = processed_docs

            if processed_docs:
                print(f"✓ Successfully processed {len(processed_docs)} docs")

                # Calculate metrics for all processed documents
                total_chars = 0
                successful_docs = 0

                for doc_result in processed_docs:
                    if doc_result.get('status') == 'success':
                        extraction_result = doc_result['extraction_result']
                        char_count = len(extraction_result.text)
                        total_chars += char_count
                        successful_docs += 1

                        # Estimate pages for this document
                        file_path = Path(doc_result['file_path'])
                        pages = estimate_pages(file_path)

                        # Add to metrics
                        metrics.add_document_result(
                            method, char_count, pages, success=True
                        )
                    else:
                        metrics.add_document_result(
                            method, 0, 0, success=False
                        )

                # Save processed documents to JSON files
                save_result = save_processed_documents(
                    preprocessor, processed_docs, method)
                print(f"  {save_result}")

                # Show stats
                avg_chars = total_chars / successful_docs if successful_docs > 0 else 0
                method_time = metrics.method_metrics[method]['total_time']
                print(f"  ⏱️  Processing time: {format_time(method_time)}")
                print(f"  📊 Total characters: {total_chars:,}")
                print(f"  📄 Average per doc: {int(avg_chars):,} characters")

            else:
                print(f"❌ No documents processed with {method}")

        except Exception as e:
            print(f"❌ Error with {method}: {e}")
            all_results[method] = []
            metrics.add_document_result(method, 0, 0, success=False)

    # Comprehensive metrics summary
    print(f"\n{'=' * 65}")
    print("COMPREHENSIVE PROCESSING METRICS")
    print(f"{'=' * 65}")

    summary = metrics.get_summary()

    # Overall statistics
    total_time = sum(m['total_time'] for m in summary.values())
    total_docs = sum(m['documents_processed'] for m in summary.values())
    total_chars = sum(m['total_characters'] for m in summary.values())
    total_errors = sum(m['errors'] for m in summary.values())

    print(f"📈 OVERALL SUMMARY:")
    print(f"   Total processing time: {format_time(total_time)}")
    print(f"   Documents processed: {total_docs}")
    print(f"   Total characters extracted: {total_chars:,}")
    print(f"   Total errors: {total_errors}")
    print(
        f"   Success rate: {(total_docs / (total_docs + total_errors) * 100):.1f}%")

    # Method-specific metrics
    print(f"\n📊 METHOD-SPECIFIC METRICS:")
    print(f"{'Method':<12} {'Time':<8} {'Docs':<5} {'Chars':<10} {'Avg/Doc':<10} {'Avg/Page':<10} {'Time/Doc':<10}")
    print("-" * 75)

    for method, stats in summary.items():
        print(f"{method.upper():<12} "
              f"{format_time(stats['total_time']):<8} "
              f"{stats['documents_processed']:<5} "
              f"{stats['total_characters']:>9,} "
              f"{stats['avg_chars_per_doc']:>9,} "
              f"{stats['avg_chars_per_page']:>9,} "
              f"{format_time(stats['avg_time_per_doc']):<10}")

    # Performance comparison
    print(f"\n⚡ PERFORMANCE RANKING (by speed):")
    speed_ranking = sorted(
        summary.items(), key=lambda x: x[1]['avg_time_per_doc'])
    for i, (method, stats) in enumerate(speed_ranking, 1):
        print(
            f"   {i}. {method.upper()}: {format_time(stats['avg_time_per_doc'])}/doc")

    print(f"\n📝 EXTRACTION EFFICIENCY (by characters/second):")
    efficiency_ranking = sorted(
        summary.items(),
        key=lambda x: x[1]['total_characters'] / max(x[1]['total_time'], 0.1),
        reverse=True
    )
    for i, (method, stats) in enumerate(efficiency_ranking, 1):
        chars_per_sec = stats['total_characters'] / \
            max(stats['total_time'], 0.1)
        print(f"   {i}. {method.upper()}: {chars_per_sec:,.0f} chars/sec")

    # Save metrics to JSON
    metrics_file = preprocessor.processed_path / \
        f"processing_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'total_documents': len(documents),
            'total_estimated_pages': total_estimated_pages,
            'processing_summary': {
                'total_time': total_time,
                'total_docs_processed': total_docs,
                'total_characters': total_chars,
                'total_errors': total_errors,
                'overall_success_rate': (total_docs / (total_docs + total_errors) * 100) if (total_docs + total_errors) > 0 else 0
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Metrics saved to: {metrics_file}")

    print(f"\n{'=' * 65}")
    print("📁 PROCESSED FILES LOCATIONS:")
    print(f"{'=' * 65}")

    for method in methods:
        method_dir = preprocessor.processed_path / method
        if method_dir.exists():
            json_files = list(method_dir.glob("*.json"))
            print(f"{method.upper():<12}: {len(json_files)} files in {method_dir}")
        else:
            print(f"{method.upper():<12}: No files saved")

    print(f"\nDemo complete! Processed JSON files are saved in data/processed/")


if __name__ == "__main__":
    main()
