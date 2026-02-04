# Federated Search Interface - ADR-012 Implementation

## Overview

This is the implementation of **ADR-012: Federated Search Implementation** - a React-based interface that demonstrates how different chunking strategies produce different results for the same search query.

## Features

✅ **Federated Search**: Queries 4 Typesense collections simultaneously

- `unstructured_fixed_size` (81 documents)
- `unstructured_semantic` (189 documents)
- `unstructured_sliding_langchain` (195 documents)
- `unstructured_sliding_unstructured` (216 documents)

✅ **Side-by-Side Comparison**: Results displayed in 4-column grid layout
✅ **Search Highlighting**: Query terms highlighted in chunk content
✅ **Rich Metadata**: Shows chunk index, token count, and document title
✅ **Professional UI**: Uses Algolia CSS themes with custom styling
✅ **Responsive Design**: Works on desktop and mobile devices

## Architecture

```
frontend/
├── public/
│   └── index.html           # Main HTML with CDN dependencies
├── src/
│   ├── App.js              # React app with federated search logic
│   └── styles/
│       └── main.css        # Custom grid and component styling
├── package.json            # NPM dependencies (serve only)
└── Dockerfile              # Container configuration
```

## Technology Stack

- **React 18** (via CDN)
- **React InstantSearch 7.16.2** (via CDN)
- **Typesense InstantSearch Adapter** (via CDN)
- **Algolia CSS Themes** (reset + satellite)
- **Node.js serve** (static file server)

## Usage

### Via Docker Compose (Recommended)

```bash
# Build and start the frontend
docker compose build frontend
docker compose up frontend

# Access the interface
open http://localhost:3000
```

### Local Development

```bash
cd frontend
npm install
npm start

# Access the interface
open http://localhost:3000
```

## Search Examples

Try these example searches to see strategy differences:

- **"algorithm"** - Shows algorithmic concepts across strategies
- **"backtracking"** - Demonstrates search technique variations
- **"dynamic"** - Shows how dynamic concepts are chunked
- **"search space"** - Illustrates search space discussions

## Interface Layout

```
┌──────────────────────────────────────────────────────────┐
│                Chunking Strategy Comparison              │
├──────────────────────────────────────────────────────────┤
│ Query: [________________________] [Search]               │
├──────────────────────────────────────────────────────────┤
│              Results Comparison Grid                     │
│ ┌──────────────┬──────────────┬──────────────┐           │
│ │ Fixed Size   │  Semantic    │ Sliding (LC) │           │
│ │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │           │
│ │ │Result 1  │ │ │Result 1  │ │ │Result 1  │ │           │
│ │ │#chunk_idx│ │ │#chunk_idx│ │ │#chunk_idx│ │           │
│ │ │512 tokens│ │ │420 tokens│ │ │380 tokens│ │           │
│ │ │highlight │ │ │highlight │ │ │highlight │ │           │
│ │ │content   │ │ │content   │ │ │content   │ │           │
│ │ └──────────┘ │ └──────────┘ │ └──────────┘ │           │
│ └──────────────┴──────────────┴──────────────┘           │
└──────────────────────────────────────────────────────────┘
```

## Configuration

The interface connects to Typesense via Docker network:

```javascript
const typesenseConfig = {
  server: {
    apiKey: "xyz",
    nodes: [{ host: "typesense", port: "8108", protocol: "http" }],
  },
  additionalSearchParameters: {
    highlight_fields: "content,document_title",
    snippet_threshold: 30,
    highlight_affix_num_tokens: 4,
    per_page: 6,
  },
};
```

## Data Sources

The interface searches across indexed chunks from:

- **Document**: `9308101_Dynamic Backtracking.pdf`
- **Extraction Method**: Unstructured.io
- **Chunking Strategies**: Fixed Size, Semantic, Sliding LangChain, Sliding Unstructured

## Performance

- **Search Response**: < 500ms for typical queries
- **Results per Strategy**: Limited to 6 hits for optimal UX
- **Caching**: 2-minute result cache in Typesense
- **Highlighting**: Real-time query highlighting

## Next Steps (ADR-013)

The architecture is designed to support future enhancements:

- [ ] Performance metrics dashboard
- [ ] Extraction method comparison (marker vs pypdf vs unstructured)
- [ ] Strategy selection controls and filtering
- [ ] Advanced comparison features and analytics
- [ ] Use case presets (conceptual, technical, methodological)

## Dependencies

**Required Services:**

- Typesense 29.0 with indexed collections
- Docker network connectivity

**Required Collections:**

- `unstructured_fixed_size`
- `unstructured_semantic`
- `unstructured_sliding_langchain`
- `unstructured_sliding_unstructured`

## Troubleshooting

### Search Not Working

- Verify Typesense is running: `docker compose ps`
- Check collections exist: `curl -H "X-TYPESENSE-API-KEY: xyz" "http://localhost:8108/collections"`

### Empty Results

- Ensure collections are indexed with data
- Check search query syntax
- Verify field names match schema

### Container Issues

- Rebuild frontend: `docker compose build frontend`
- Check logs: `docker compose logs frontend`
- Verify network connectivity between services

## Success Criteria Met

✅ Single search box queries all 4 collections simultaneously  
✅ Results displayed in 4-column grid layout  
✅ Search term highlighting in chunk content  
✅ Chunk metadata display (index, token count, document title)  
✅ Professional UI using Algolia CSS theme  
✅ Search results appear within 500ms  
✅ Responsive grid layout works on desktop and mobile  
✅ Clearly shows different results for same query across strategies  
✅ Professional appearance suitable for stakeholder demos
