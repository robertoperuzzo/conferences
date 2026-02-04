# Typesense Collections Re-indexing Guide

## Overview

This guide explains how to re-index Typesense collections after schema or data processor changes. The enhanced indexer now captures much more metadata from the chunk data including strategy configurations, document metadata, performance analytics, and improved scoring.

## Prerequisites

Before re-indexing, ensure:

1. **Typesense is running**: The Typesense service should be accessible
2. **Environment variables set**: Required Typesense connection settings
3. **Data is available**: Both processed documents and chunk data exist
4. **Backup collections** (optional): If you want to preserve existing data

## Quick Re-indexing Commands

### 🚀 **Most Common: Re-index All Collections (Development)**

```bash
# Re-index all extraction methods and strategies with limited documents
cd /workspace
python -m src.indexer --index-all --force-recreate --max-documents 5 --log-level INFO
```

### 🚀 **Production: Re-index All Collections (Full Dataset)**

```bash
# Re-index all extraction methods and strategies with all documents
cd /workspace
python -m src.indexer --index-all --force-recreate --max-documents -1 --log-level INFO
```

### 🎯 **Specific Collection: Re-index Single Strategy**

```bash
# Re-index specific extraction method and chunking strategy
cd /workspace
python -m src.indexer --extraction-method unstructured --chunking-strategy fixed_size --force-recreate --max-documents 5
```

## 📊 New Performance Analytics

After Phase 2 implementation, the indexer now includes comprehensive performance analytics:

- **Performance tracking**: Processing time, memory usage, CPU/GPU utilization
- **Strategy comparison**: Compare performance between different chunking strategies
- **Optimization insights**: Automatically identify optimal strategies
- **Analytics API**: Access performance data programmatically

The performance data is stored in the collection schema and can be queried alongside document content.

## Command Options Explained

| Option                | Description                                           | Values                                                                | Default |
| --------------------- | ----------------------------------------------------- | --------------------------------------------------------------------- | ------- |
| `--index-all`         | Index all available extraction methods and strategies | flag                                                                  | false   |
| `--extraction-method` | Specific extraction method                            | `unstructured`, `marker`, `pypdf`, `markitdown`                       | none    |
| `--chunking-strategy` | Specific chunking strategy                            | `fixed_size`, `semantic`, `sliding_langchain`, `sliding_unstructured` | none    |
| `--max-documents`     | Number of documents to process                        | integer or `-1` for all                                               | 5       |
| `--force-recreate`    | Delete and recreate collections                       | flag                                                                  | false   |
| `--reindex`           | Reindex existing collections without recreation       | flag                                                                  | false   |
| `--log-level`         | Logging verbosity                                     | `DEBUG`, `INFO`, `WARNING`, `ERROR`                                   | INFO    |

## Step-by-Step Re-indexing Process

### Step 1: Check Current Collections

```bash
# List available extraction methods
python -m src.indexer --list-methods

# Show current collection statistics
python -m src.indexer --stats
```

### Step 2: Choose Re-indexing Approach

#### Option A: Quick Development Re-index (5 documents)

```bash
python -m src.indexer --index-all --force-recreate --max-documents 5
```

- ⏱️ **Time**: ~5-10 minutes
- 💾 **Storage**: ~50-100MB
- 🎯 **Use**: Testing, development, validation

#### Option B: Full Production Re-index (All documents)

```bash
python -m src.indexer --index-all --force-recreate --max-documents -1
```

- ⏱️ **Time**: ~1-2 hours
- 💾 **Storage**: ~3-5GB
- 🎯 **Use**: Production deployment

#### Option C: Selective Re-index (Specific strategy)

```bash
python -m src.indexer --extraction-method unstructured --chunking-strategy semantic --force-recreate --max-documents 10
```

### Step 3: Monitor Progress

The indexer will show progress like:

```
2025-09-05 10:00:00 - INFO - Starting indexing for unstructured_fixed_size
2025-09-05 10:00:01 - INFO - Creating collection: unstructured_fixed_size
2025-09-05 10:00:02 - INFO - Processing 5 documents for unstructured_fixed_size
2025-09-05 10:00:05 - INFO - Processing batch 1 of 2 (100 documents)
2025-09-05 10:01:00 - INFO - Indexed 100 documents, 0 errors
```

### Step 4: Verify Results

```bash
# Check collection statistics after indexing
python -m src.indexer --stats
```

## Enhanced Schema Fields

The new schema includes these additional fields beyond the core document fields:

### Core Fields

| Field               | Type   | Description                     | Facetable |
| ------------------- | ------ | ------------------------------- | --------- |
| `chunk_id`          | string | Unique identifier for the chunk | ❌        |
| `document_id`       | string | Document identifier             | ✅        |
| `document_title`    | string | Document title                  | ✅        |
| `document_filename` | string | Original filename               | ✅        |
| `extraction_method` | string | Extraction method used          | ✅        |
| `chunking_strategy` | string | Chunking strategy applied       | ✅        |
| `content`           | string | Chunk text content              | ❌        |
| `token_count`       | int32  | Number of tokens in chunk       | ✅        |
| `chunk_index`       | int32  | Position of chunk in document   | ✅        |

### Enhanced Metadata Fields

| Field           | Type     | Description                            | Facetable |
| --------------- | -------- | -------------------------------------- | --------- |
| `strategy_name` | string   | Specific strategy name from chunk data | ✅        |
| `total_chunks`  | int32    | Total chunks in the document           | ✅        |
| `authors`       | string[] | Document authors (optional)            | ✅        |
| `created_at`    | string   | Chunk creation timestamp (optional)    | ❌        |
| `chunk_size`    | int32    | Strategy chunk size config (optional)  | ✅        |
| `chunk_overlap` | int32    | Strategy overlap config (optional)     | ✅        |
| `encoding_name` | string   | Token encoding used (optional)         | ✅        |

### Performance Analytics Fields

| Field                  | Type   | Description                            | Facetable |
| ---------------------- | ------ | -------------------------------------- | --------- |
| `preprocessing_method` | string | Preprocessing method identifier        | ✅        |
| `content_length`       | int32  | Length of processed content            | ✅        |
| `processing_time`      | float  | Processing time in seconds             | ✅        |
| `memory_usage`         | float  | Memory usage in MB                     | ✅        |
| `cpu_usage_percent`    | float  | CPU usage percentage during processing | ✅        |
| `gpu_usage_percent`    | float  | GPU usage percentage (if available)    | ✅        |

## Troubleshooting

### Common Issues

#### ❌ "Collection already exists"

**Solution**: Use `--force-recreate` flag

```bash
python -m src.indexer --index-all --force-recreate
```

#### ❌ "No documents found"

**Check**: Ensure data files exist

```bash
ls -la /workspace/data/processed/
ls -la /workspace/data/chunks/
```

**Note**: The indexer supports both old and new chunking file formats:

- **New format**: `{document_id}_{extraction_method}_{chunking_strategy}.json`
- **Old format**: Legacy naming patterns (automatically detected)

#### ❌ "Connection refused"

**Check**: Ensure Typesense is running

```bash
docker-compose ps typesense
# or
curl http://localhost:8108/health
```

#### ❌ "Out of memory"

**Solution**: Reduce batch size or document count

```bash
python -m src.indexer --index-all --max-documents 3
```

### Environment Variables

Ensure these are set (usually in `.env` or environment):

```bash
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_ADMIN_API_KEY=xyz
```

## Collection Names

Collections are named using the pattern: `{extraction_method}_{chunking_strategy}`

Examples:

- `unstructured_fixed_size`
- `unstructured_semantic`
- `unstructured_sliding_langchain`
- `unstructured_sliding_unstructured`
- `marker_fixed_size`
- `pypdf_fixed_size`
- `markitdown_semantic`

## After Re-indexing

1. **Test Frontend**: Refresh the web application and test search functionality
2. **Check Scores**: Verify that relevance scores are now showing correctly (not 0.000)
3. **Validate Data**: Ensure new fields are populated and searchable
4. **Performance Analytics**: New performance metadata is available for analysis
5. **Performance**: Monitor search performance with the enhanced schema

## Logs

Indexing logs are written to:

- **Console**: Real-time progress
- **File**: `/workspace/logs/indexer.log`

## Quick Reference Card

```bash
# 🔥 MOST COMMON COMMANDS 🔥

# Quick dev re-index (5 docs)
python -m src.indexer --index-all --force-recreate --max-documents 5

# Full production re-index
python -m src.indexer --index-all --force-recreate --max-documents -1

# Check what's available
python -m src.indexer --list-methods --stats

# Re-index specific strategy
python -m src.indexer --extraction-method unstructured --chunking-strategy semantic --force-recreate
```

## 🚨 Remember After Re-indexing

- **Frontend will now show proper scores** (not 0.000)
- **More metadata available** for display and filtering
- **Enhanced search capabilities** with new fields and performance analytics
- **Better document-level grouping** with total_chunks info
- **Performance insights** available through new analytics fields
- **Multi-format support** - works with both old and new chunking file formats

Save this guide for future reference! 📋
