# 🔄 Re-indexing Quick Start

## TL;DR - Just run this:

```bash
# Quick development re-index (5 documents)
./scripts/reindex.sh -a

# Or the manual way:
python -m src.indexer --index-all --force-recreate --max-documents 5
```

## 📚 Full Documentation

- **[Complete Re-indexing Guide](REINDEX_GUIDE.md)** - Detailed instructions, troubleshooting, and all options
- **[Indexing Improvements Summary](INDEXING_IMPROVEMENTS.md)** - What changed and why

## 🚀 Quick Commands

### Use the Helper Script (Recommended)

```bash
./scripts/reindex.sh -a          # Re-index all (5 docs)
./scripts/reindex.sh -a -p       # Re-index all (production, all docs)
./scripts/reindex.sh -q          # Quick mode (3 docs)
./scripts/reindex.sh --stats     # Show collection stats
./scripts/reindex.sh --help      # Show all options
```

### Manual Commands

```bash
# Development (5 docs)
python -m src.indexer --index-all --force-recreate --max-documents 5

# Production (all docs)
python -m src.indexer --index-all --force-recreate --max-documents -1

# Specific method
python -m src.indexer --extraction-method unstructured --chunking-strategy semantic --force-recreate
```

## ✅ After Re-indexing

1. **Refresh your browser** - The frontend will now show:

   - ✅ Proper relevance scores (not 0.000)
   - ✅ No pagination issues
   - ✅ More detailed chunk statistics
   - ✅ Strategy configuration info
   - ✅ Performance analytics data

2. **Test search** - Try searching for terms and verify the document-level results

## ❓ Problems?

Check the [REINDEX_GUIDE.md](REINDEX_GUIDE.md) for troubleshooting common issues.

## 🏗️ What Changed?

The indexer now captures much more data from your chunks:

- Strategy configurations (chunk_size, overlap, encoding)
- Document metadata (authors, total_chunks, created_at)
- **Performance analytics** (processing_time, memory_usage, CPU/GPU usage)
- Better relevance scoring
- Complete chunk information
- Multi-format support (new chunking file format with backward compatibility)

See [INDEXING_IMPROVEMENTS.md](INDEXING_IMPROVEMENTS.md) for details.
