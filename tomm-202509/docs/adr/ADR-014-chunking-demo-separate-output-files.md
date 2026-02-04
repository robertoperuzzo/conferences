# ADR-014: Chunking Demo Separate Output Files

## Status

Accepted

## Context

The current chunking demo script (`scripts/demo_chunking.py`) processes all available chunking strategies on a single preprocessed document and saves all results into one combined JSON file. This design has the following characteristics:

### Current Behavior

- Loads the first successfully parseable preprocessed document
- Applies all chunking strategies (fixed_size, sliding_langchain, sliding_unstructured, semantic) to that single document
- Saves all strategy results in one file: `chunking_demo_results_{document_id}.json`
- Facilitates easy comparison of strategies on the same document

### Limitations

- No visibility into how different preprocessing methods (pypdf, unstructured, marker) affect chunking outcomes
- No individual files per strategy-parser combination for detailed analysis
- Difficult to track performance characteristics of specific strategy-parser pairs
- Limited scalability when analyzing multiple documents with multiple preprocessing methods

### User Expectation

Users expect to see separate output files for each combination of:

- Chunking strategy (fixed_size, sliding_langchain, sliding_unstructured, semantic)
- Preprocessing method (pypdf, unstructured, marker)
- Source document

This would enable more granular analysis and comparison of preprocessing-chunking pipelines.

## Decision

We will modify the chunking demo script to generate separate output files for each strategy-parser-document combination, replacing the current consolidated approach.

### Proposed Changes

#### 1. File Naming Convention

```
{document_id}_{preprocessing_method}_{chunking_strategy}.json
```

Examples:

- `9308101_DynamicBacktracking_pypdf_fixed_size.json`
- `9308101_DynamicBacktracking_unstructured_semantic.json`
- `9309101_EmpiricalAnalysis_marker_sliding_langchain.json`

#### 2. Processing Logic

- Process all available preprocessed documents (not just the first successful one)
- For each document, apply each chunking strategy individually
- Save results immediately after each strategy-document combination
- Maintain error handling per combination to avoid cascade failures
- Collect performance metrics for each strategy-parser combination
- Display comprehensive performance summary at the end

#### 3. Output Structure

Each individual file will contain:

```json
{
  "document_info": {
    "document_id": "string",
    "title": "string",
    "content_length": "number",
    "source_file": "string",
    "preprocessing_method": "string"
  },
  "strategy_config": {
    "strategy_name": "string",
    "parameters": {}
  },
  "results": {
    "chunks": [],
    "statistics": {},
    "error": null
  },
  "processing_metadata": {
    "timestamp": "ISO-8601",
    "processing_time": "number",
    "memory_usage": "number",
    "cpu_usage_percent": "number",
    "gpu_usage_percent": "number",
    "gpu_memory_usage": "number"
  }
}
```

#### 4. Performance Metrics Display

At the end of script execution, display a comprehensive performance summary table showing:

**Per Strategy-Parser Combination:**

- Memory usage (MB)
- CPU usage (%)
- GPU usage (%)
- GPU memory usage (MB)
- Processing time (seconds)
- Number of chunks generated
- Average chunk size (characters)
- Min/Max chunk sizes

**Aggregate Statistics:**

- Total processing time
- Peak memory usage (RAM + GPU)
- Total chunks generated across all combinations
- Overall average chunk size

**Example Output:**

```
╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                           PERFORMANCE SUMMARY                                               ║
╠═════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ Document: 9308101_DynamicBacktracking                                                                       ║
╠═════════════════╦══════════╦══════════╦══════════╦═══════════╦═══════════╦═══════════╦══════════╦═══════════╣
║ Strategy/Parser ║ RAM      ║ CPU %    ║ GPU %    ║ GPU Mem   ║ Time (s)  ║ Chunks    ║ Avg Size ║ Min/Max   ║
║                 ║ (MB)     ║          ║          ║ (MB)      ║           ║           ║ (chars)  ║ (chars)   ║
╠═════════════════╬══════════╬══════════╬══════════╬═══════════╬═══════════╬═══════════╬══════════╬═══════════╣
║ pypdf/fixed     ║ 45.2     ║ 12.3     ║ 0.0      ║ 0.0       ║ 2.14      ║ 89        ║ 512      ║ 450/512   ║
║ pypdf/semantic  ║ 67.8     ║ 34.7     ║ 78.4     ║ 2,340     ║ 8.92      ║ 23        ║ 1,247    ║ 234/1,500 ║
║ unstr/sliding   ║ 52.1     ║ 18.6     ║ 0.0      ║ 0.0       ║ 3.45      ║ 67        ║ 743      ║ 612/800   ║
║ marker/semantic ║ 71.3     ║ 41.2     ║ 82.1     ║ 2,456     ║ 12.67     ║ 19        ║ 1,389    ║ 298/1,500 ║
╚═════════════════╩══════════╩══════════╩══════════╩═══════════╩═══════════╩═══════════╩══════════╩═══════════╝

TOTALS: 198 chunks | 27.18s total | 71.3MB peak RAM | 2.5GB peak GPU | 901 avg chars/chunk
```

#### 5. CLI Options

Add command-line arguments for filtering:

```bash
python scripts/demo_chunking.py --strategies=semantic,fixed_size  # Specific strategies
python scripts/demo_chunking.py --methods=pypdf,unstructured     # Specific preprocessing methods
python scripts/demo_chunking.py --no-metrics                     # Skip performance display
```

## Consequences

### Positive

- **Granular Analysis**: Enables detailed analysis of specific strategy-parser combinations
- **Scalability**: Supports processing multiple documents and preprocessing methods
- **Traceability**: Each combination has its own traceable output file
- **Simplicity**: Single, focused output format without mode complexity
- **Research Support**: Better supports comparative research on chunking strategies
- **Error Isolation**: Failures in one combination don't affect others
- **Performance Visibility**: Clear performance metrics for optimization and comparison
- **GPU Utilization Tracking**: Visibility into GPU usage for ML-based chunking strategies

### Negative

- **Increased File Count**: Will generate many more output files
- **Storage Usage**: Higher disk space usage due to multiple files
- **Processing Time**: Longer execution time due to comprehensive processing and monitoring
- **No Built-in Comparison**: Users need to aggregate results manually for comparison
- **Resource Overhead**: Additional CPU/memory usage for performance monitoring
- **GPU Dependency**: Some metrics may not be available on systems without GPU support

### Neutral

- **File Organization**: Straightforward flat structure in chunks directory

## Implementation Notes

### Directory Structure

```
data/chunks/
├── 9308101_DynamicBacktracking_pypdf_fixed_size.json
├── 9308101_DynamicBacktracking_pypdf_semantic.json
├── 9308101_DynamicBacktracking_unstructured_sliding_langchain.json
├── 9309101_EmpiricalAnalysis_marker_semantic.json
└── ...
```

### Error Handling Strategy

- Continue processing other combinations if one fails
- Log detailed error information
- Include error summary in final report
- Provide partial results when possible

### Performance Considerations

- Process combinations in parallel where possible
- Implement progress tracking for long-running operations
- Add comprehensive memory, CPU, and GPU monitoring for each combination
- Include cleanup between combinations to ensure accurate measurements
- Consider chunked processing for large document sets
- Collect detailed timing metrics for performance analysis
- Handle GPU availability gracefully (fallback to CPU-only metrics if no GPU)

## Alternatives Considered

### Alternative 1: Maintain Current Single-File Approach

**Rejected**: Does not address the core requirement for granular analysis of strategy-parser combinations.

### Alternative 2: Separate Scripts per Strategy

**Rejected**: Would lead to code duplication and maintenance overhead.

### Alternative 3: Database-Based Storage

**Rejected**: Adds complexity and external dependencies; JSON files are more portable and easier to analyze.

### Alternative 4: Maintain Consolidated Summary with Individual Files

**Rejected**: Adds unnecessary complexity; users can create their own aggregations as needed.

## References

- Current implementation: `scripts/demo_chunking.py`
- Related ADRs: ADR-009 (Chunking Strategies Prototype Implementation)
- Chunking pipeline: `src/chunker/pipeline.py`
- Configuration system: `src/chunker/config.py`
