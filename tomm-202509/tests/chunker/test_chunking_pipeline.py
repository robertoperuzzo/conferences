"""Tests for the chunking pipeline and strategies.

This module tests the complete chunking pipeline functionality including:
- Pipeline initialization and configuration
- All chunking strategies (fixed-size, sliding, semantic)
- Document processing and output formats
- Strategy comparison and reporting
"""

import pytest

from src.chunker import ChunkingPipeline, ProcessedDocument
from src.chunker.config import get_default_config


def create_test_document():
    """Create a test document for chunking."""
    return ProcessedDocument(
        document_id="test_doc_001",
        title="Test Document for Chunking Strategies",
        authors=["Test Author"],
        abstract="This is a test abstract for our chunking demonstration.",
        full_text="""
        This is a test document for demonstrating chunking strategies.
        
        Introduction
        
        Chunking is a critical component of RAG systems. It determines how
        documents are split into retrievable segments. Different strategies
        have different advantages and trade-offs.
        
        Fixed-Size Chunking
        
        Fixed-size chunking splits text into chunks of a predetermined size.
        This approach is simple and fast, making it suitable for baseline
        implementations. However, it may cut across sentence boundaries.
        
        Sliding Window Approaches
        
        Sliding window techniques create overlapping chunks to preserve
        context across boundaries. This helps maintain coherence and
        improves retrieval quality.
        
        Semantic Chunking
        
        Semantic chunking analyzes the meaning of text to identify natural
        breakpoints. This approach creates more coherent chunks but requires
        additional computational resources.
        
        Conclusion
        
        Each chunking strategy has its place depending on the specific
        requirements of the application. The choice depends on factors
        such as processing speed, chunk quality, and computational resources.
        """,
        metadata={
            "source": "test",
            "created_date": "2025-08-28"
        }
    )


def test_chunking_pipeline_initialization():
    """Test that the chunking pipeline initializes correctly."""
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    # Check that strategies are initialized
    available_strategies = pipeline.get_available_strategies()
    assert len(available_strategies) > 0
    
    # Check that expected strategies are available
    expected_strategies = {
        'fixed_size', 'sliding_langchain',
        'sliding_unstructured', 'semantic'
    }
    available_set = set(available_strategies)
    
    # At least some strategies should be available
    assert len(available_set.intersection(expected_strategies)) > 0


def test_single_document_processing():
    """Test processing a single document with all strategies."""
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    document = create_test_document()
    results = pipeline.process_document(document)
    
    # Check that we got results
    assert len(results) > 0
    
    # Check that each result has chunks
    for strategy_name, result in results.items():
        assert result.success is True, (
            f"Strategy {strategy_name} failed: {result.error_message}"
        )
        assert len(result.chunks) > 0, (
            f"Strategy {strategy_name} produced no chunks"
        )
        
        # Check chunk properties
        for chunk in result.chunks:
            assert chunk.document_id == document.document_id
            assert chunk.strategy_name == strategy_name
            assert len(chunk.content.strip()) > 0
            assert chunk.token_count > 0
            
        print(f"Strategy {strategy_name}: {len(result.chunks)} chunks")


def test_chunking_output_format():
    """Test that chunk output format is correct."""
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    document = create_test_document()
    results = pipeline.process_document(document)
    
    for strategy_name, result in results.items():
        for chunk in result.chunks:
            # Test serialization
            chunk_dict = chunk.to_dict()
            
            # Check required fields
            required_fields = [
                'chunk_id', 'document_id', 'strategy_name',
                'content', 'start_position', 'end_position',
                'token_count', 'metadata', 'created_at'
            ]
            
            for field in required_fields:
                assert field in chunk_dict, f"Missing field {field} in chunk"


def test_strategy_comparison():
    """Test that different strategies produce different results."""
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    document = create_test_document()
    results = pipeline.process_document(document)
    
    if len(results) < 2:
        pytest.skip("Need at least 2 strategies for comparison")
    
    strategy_names = list(results.keys())
    first_strategy = results[strategy_names[0]]
    second_strategy = results[strategy_names[1]]
    
    # Strategies should produce different numbers of chunks
    # or different content
    chunks_different = (
        len(first_strategy.chunks) != len(second_strategy.chunks)
    )
    
    if not chunks_different and len(first_strategy.chunks) > 0:
        # Check if chunk content is different
        first_content = [chunk.content for chunk in first_strategy.chunks]
        second_content = [chunk.content for chunk in second_strategy.chunks]
        chunks_different = first_content != second_content
    
    assert chunks_different, (
        "Different strategies should produce different results"
    )


def test_comparison_report():
    """Test generation of comparison reports."""
    config = get_default_config()
    pipeline = ChunkingPipeline(config)
    
    document = create_test_document()
    results = {document.document_id: pipeline.process_document(document)}
    
    # Generate comparison report
    report = pipeline.generate_comparison_report(results)
    
    # Check report structure
    assert 'generated_at' in report
    assert 'total_documents_processed' in report
    assert 'strategies_compared' in report
    assert 'strategy_performance' in report
    
    # Check performance metrics
    for strategy_name in report['strategies_compared']:
        performance = report['strategy_performance'][strategy_name]
        
        required_metrics = [
            'success_rate', 'avg_chunks_per_document',
            'avg_processing_time_per_document', 'avg_chunk_size',
            'avg_token_count', 'total_chunks'
        ]
        
        for metric in required_metrics:
            assert metric in performance, (
                f"Missing metric {metric} for strategy {strategy_name}"
            )


if __name__ == "__main__":
    # Run basic tests
    print("Testing chunking pipeline initialization...")
    test_chunking_pipeline_initialization()
    print("✓ Pipeline initialization test passed")
    
    print("\nTesting single document processing...")
    test_single_document_processing()
    print("✓ Single document processing test passed")
    
    print("\nTesting chunk output format...")
    test_chunking_output_format()
    print("✓ Chunk output format test passed")
    
    print("\nTesting strategy comparison...")
    test_strategy_comparison()
    print("✓ Strategy comparison test passed")
    
    print("\nTesting comparison report generation...")
    test_comparison_report()
    print("✓ Comparison report test passed")
    
    print(
        "\n🎉 All tests passed! Chunking strategies implementation "
        "is working correctly."
    )
