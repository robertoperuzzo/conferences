#!/usr/bin/env python3
"""
PDF Preprocessing Script - ADR-011 Implementation

This script demonstrates the modular extractor architecture by processing 
documents using all four available extraction methods.
"""

from src.preprocessor import DocumentPreprocessor
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Process documents with all available methods."""
    print("Document Preprocessing Demo - ADR-011 Implementation")
    print("=" * 55)

    # Initialize preprocessor
    preprocessor = DocumentPreprocessor()

    print(f"Available extraction methods: {preprocessor.SUPPORTED_METHODS}")

    # Discover documents
    documents = preprocessor.discover_documents()
    if not documents:
        print("No documents found in data/raw/ directory")
        return

    print(f"\nFound {len(documents)} files:")
    for doc in documents:
        print(f"  - {doc.name}")

    # Process with all available methods
    methods = preprocessor.SUPPORTED_METHODS
    all_results = {}

    for method in methods:
        print(f"\n{'-' * 40}")
        print(f"Processing with {method.upper()} method...")
        print(f"{'-' * 40}")

        try:
            processed_docs = preprocessor.process_documents(
                method=method,
                track_performance=True
            )

            all_results[method] = processed_docs

            if processed_docs:
                print(f"✓ Successfully processed {len(processed_docs)} docs")

                # Show stats for first document
                first_doc = processed_docs[0]
                status = first_doc.get('status', 'unknown')
                print(f"  Status: {status}")

                if status == 'success':
                    result = first_doc['extraction_result']
                    text_len = len(result.text)
                    method_used = first_doc.get('method_used', method)
                    print(f"  Text length: {text_len:,} characters")
                    print(f"  Method used: {method_used}")

                    # Show metadata if available
                    metadata = first_doc.get('metadata', {})
                    if metadata:
                        print(f"  File info: {metadata}")
            else:
                print(f"❌ No documents processed with {method}")

        except Exception as e:
            print(f"❌ Error with {method}: {e}")
            all_results[method] = []

    # Summary
    print(f"\n{'=' * 50}")
    print("PROCESSING SUMMARY")
    print(f"{'=' * 50}")

    total_processed = 0
    for method, results in all_results.items():
        count = len(results)
        total_processed += count
        status = "✓ Success" if count > 0 else "❌ Failed"
        print(f"{method.upper():<12}: {count:>3} documents {status}")

    print(f"\nTotal processed: {total_processed} documents")
    print("\nProcessed files are available through the DocumentPreprocessor API")
    print("or can be saved using the extract_text_from_file method")

    # Demonstrate individual extraction
    if documents:
        print(f"\n{'-' * 40}")
        print("INDIVIDUAL EXTRACTION DEMO")
        print(f"{'-' * 40}")

        first_doc = documents[0]
        print(f"Testing extraction methods on: {first_doc.name}")

        for method in methods[:2]:  # Test first two methods
            try:
                print(f"\nTesting {method.upper()}:")
                result = preprocessor.extract_text_from_file(
                    first_doc, method=method
                )
                print(
                    f"  ✓ Success - {len(result.text):,} characters extracted")
                print(
                    f"  Method: {result.method_specific_data.get('extraction_method', method)}")

            except Exception as e:
                print(f"  ❌ Failed: {e}")

    print(f"\n{'=' * 55}")
    print("Demo complete! Use DocumentPreprocessor for more operations.")


if __name__ == "__main__":
    main()
