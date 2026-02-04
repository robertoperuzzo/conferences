# Test Execution Guide

This document explains how to run the different types of tests in this project, particularly the PDF processor tests that have been optimized for speed.

## Test Categories

### 1. Fast Tests (Mocked) - ~15 seconds

These tests use mocked dependencies to avoid expensive PDF processing operations. They test all the integration logic without the computational overhead.

### 2. Slow Integration Tests - ~7-8 minutes

These tests perform actual PDF processing using real libraries (Unstructured.io, Marker) and are marked with `@pytest.mark.slow`.

## Commands

### Default Behavior (Fast Tests Only)

By default, pytest is configured to run only fast tests. This provides quick feedback for development:

```bash
# Run all fast tests (default behavior)
python -m pytest tests/

# Same as above - explicitly excluding slow tests
python -m pytest tests/ -m "not slow"

# Run only PDF processor fast tests
python -m pytest tests/processor/test_pdf_processor.py

# Show test durations
python -m pytest tests/ --durations=10
```

### Development (Fast Tests Only)

For regular development and CI/CD pipelines, the default configuration runs only fast tests:

```bash
# Run all fast tests (default behavior - same as just 'python -m pytest tests/')
python -m pytest tests/ -m "not slow"

# Run only PDF processor fast tests
python -m pytest tests/processor/test_pdf_processor.py -m "not slow"

# Show test durations
python -m pytest tests/ -m "not slow" --durations=10
```

### Integration Validation (Slow Tests Only)

For thorough validation with real PDF processing:

```bash
# Run only slow integration tests
python -m pytest tests/ -m "slow"

# Run only PDF processor slow tests
python -m pytest tests/processor/test_pdf_processor.py -m "slow"

# Show detailed timing for slow tests
python -m pytest tests/ -m "slow" --durations=5
```

### Complete Test Suite

To run all tests including slow ones (override default behavior):

```bash
# Run all tests (override default -m "not slow")
python -m pytest tests/ -m ""

# Alternative: explicitly include slow tests
python -m pytest tests/ -m "slow or not slow"

# Run all PDF processor tests (both fast and slow)
python -m pytest tests/processor/test_pdf_processor.py -m ""

# Run with verbose output
python -m pytest tests/ -m "" -v
```

### Specific Test Examples

```bash
# Run specific fast mocked test
python -m pytest tests/processor/test_pdf_processor.py::TestThreeMethodExtraction::test_unstructured_extraction

# Run specific slow integration test
python -m pytest tests/processor/test_pdf_processor.py::TestThreeMethodExtractionIntegration::test_unstructured_extraction_integration

# Run all tests in a specific class
python -m pytest tests/processor/test_pdf_processor.py::TestThreeMethodExtraction
```

## Performance Comparison

| Test Type                            | Execution Time | Use Case                             |
| ------------------------------------ | -------------- | ------------------------------------ |
| Fast Tests (Mocked)                  | ~15 seconds    | Development, CI/CD, Regular testing  |
| Slow Integration Tests               | ~7-8 minutes   | Thorough validation, Release testing |
| Original Tests (Before optimization) | ~7.5 minutes   | N/A (replaced by split approach)     |

**Performance Improvement**: 97% reduction in regular test execution time

## Test Structure

### Fast Tests (`-m "not slow"`)

- `TestThreeMethodExtraction::test_unstructured_extraction` - Mocked Unstructured.io test
- `TestThreeMethodExtraction::test_marker_integration_and_extraction` - Mocked Marker test
- All other existing tests (unchanged)

### Slow Tests (`-m "slow"`)

- `TestThreeMethodExtractionIntegration::test_unstructured_extraction_integration` - Real PDF processing with Unstructured.io
- `TestThreeMethodExtractionIntegration::test_marker_integration_and_extraction_integration` - Real PDF processing with Marker

## Configuration

The pytest configuration in `pyproject.toml` includes:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')"
]
addopts = [
    "-v",
    "--tb=short",
    "-m", "not slow"
]
```

This means:

- **Default behavior**: Fast tests only (`-m "not slow"`)
- **To run slow tests**: Use `-m "slow"`
- **To run all tests**: Use `-m ""` to override the default marker filter

## Recommendations

1. **Daily Development**: Use `python -m pytest tests/` (default fast tests) for quick feedback
2. **Pre-commit/CI**: Default configuration is perfect - fast tests only keep pipelines efficient
3. **Release Validation**: Override default with `python -m pytest tests/ -m ""` to run full test suite
4. **Debugging PDF Issues**: Use slow integration tests `python -m pytest tests/ -m "slow"` to validate real PDF processing behavior
