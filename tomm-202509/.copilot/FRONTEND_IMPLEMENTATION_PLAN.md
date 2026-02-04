# Frontend Implementation Plan

## Overview

Implement a chunking strategy comparison UI that demonstrates how different strategies produce different results for the same query. The implementation follows a two-phase approach:

1. **Phase 1 (ADR-012)**: Simple federated search across collections
2. **Phase 2 (ADR-013)**: Advanced comparison features and metrics

## Phase 1: Federated Search Foundation

### Goal

Create a minimal working search interface using vanilla InstantSearch.js that queries multiple Typesense collections simultaneously and displays results side-by-side.

### Technical Stack

- **InstantSearch.js 4.67+** (vanilla, not React)
- **typesense-instantsearch-adapter 2.9.0**
- **Webpack 5** for bundling
- **Algolia CSS Theme** for styling

### Architecture

```
frontend/
├── src/
│   ├── index.html                        # Main HTML structure
│   ├── index.js                          # InstantSearch.js setup
│   ├── typesenseClient.js                # Typesense adapter config
│   └── styles.css                        # Algolia CSS + custom styles
├── package.json                          # Simple dependencies
├── webpack.config.js                     # Basic webpack setup
└── Dockerfile                            # Container setup
```

### UI Layout

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

### Implementation Steps

#### Step 1: Project Setup

```bash
# Create package.json with dependencies
npm init -y
npm install instantsearch.js typesense-instantsearch-adapter
npm install --save-dev webpack webpack-cli webpack-dev-server html-webpack-plugin css-loader style-loader
```

#### Step 2: Typesense Client Configuration

```javascript
// src/typesenseClient.js
import TypesenseInstantSearchAdapter from "typesense-instantsearch-adapter";

const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({
  server: {
    apiKey: "xyz",
    nodes: [{ host: "typesense", port: "8108", protocol: "http" }],
    cacheSearchResultsForSeconds: 2 * 60,
  },
  additionalSearchParameters: {
    highlight_fields: "content",
    snippet_threshold: 30,
    highlight_affix_num_tokens: 4,
  },
  collectionSpecificSearchParameters: {
    marker_fixed_size: { query_by: "content,document_title" },
    marker_semantic: { query_by: "content,document_title" },
    marker_sliding_langchain: { query_by: "content,document_title" },
    marker_sliding_unstructured: { query_by: "content,document_title" },
  },
});

export const searchClient = typesenseInstantsearchAdapter.searchClient;
```

#### Step 3: Main Application

```javascript
// src/index.js
import instantsearch from "instantsearch.js";
import { searchBox, hits, index } from "instantsearch.js/es/widgets";
import { searchClient } from "./typesenseClient.js";

const search = instantsearch({
  indexName: "marker_fixed_size",
  searchClient,
});

// Add shared search box
search.addWidgets([
  searchBox({
    container: "#searchbox",
    placeholder: "Search across chunking strategies...",
  }),
]);

// Add federated search for each strategy
search.addWidgets([
  // Fixed Size Strategy
  index({ indexName: "marker_fixed_size" }).addWidgets([
    hits({
      container: "#hits-fixed",
      templates: {
        item: `
          <div class="hit">
            <div class="hit-header">
              <span class="chunk-id">#{{chunk_index}}</span>
              <span class="token-count">{{token_count}} tokens</span>
            </div>
            <div class="hit-content">
              {{#helpers.highlight}}{ "attribute": "content" }{{/helpers.highlight}}
            </div>
            <div class="hit-meta">
              <span class="document-title">{{document_title}}</span>
            </div>
          </div>
        `,
      },
    }),
  ]),
  // ... repeat for other strategies
]);

search.start();
```

#### Step 4: HTML Structure

```html
<!-- src/index.html -->
<!DOCTYPE html>
<html>
  <head>
    <title>Chunking Strategy Comparison</title>
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/instantsearch.css@8.0.0/themes/algolia-min.css"
    />
  </head>
  <body>
    <div class="search-container">
      <header>
        <h1>Chunking Strategy Comparison</h1>
      </header>
      <div id="searchbox"></div>
      <div class="results-grid">
        <div class="strategy-column">
          <h3>Fixed Size</h3>
          <div id="hits-fixed"></div>
        </div>
        <div class="strategy-column">
          <h3>Semantic</h3>
          <div id="hits-semantic"></div>
        </div>
        <div class="strategy-column">
          <h3>Sliding (LangChain)</h3>
          <div id="hits-sliding-langchain"></div>
        </div>
        <div class="strategy-column">
          <h3>Sliding (Unstructured)</h3>
          <div id="hits-sliding-unstructured"></div>
        </div>
      </div>
    </div>
  </body>
</html>
```

#### Step 5: Docker Setup

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### Collections Used (Phase 1)

Focus on marker\_\* collections (4 strategies):

- `marker_fixed_size` - Fixed chunk size strategy
- `marker_semantic` - Semantic chunking strategy
- `marker_sliding_langchain` - LangChain sliding window
- `marker_sliding_unstructured` - Unstructured sliding window

### Success Criteria Phase 1

- ✅ Single search box queries all 4 collections simultaneously
- ✅ Results displayed in 4-column responsive grid
- ✅ Search term highlighting in chunk content
- ✅ Professional UI using Algolia CSS theme
- ✅ Docker containerized and accessible at localhost:3000

---

## Phase 2: Advanced Comparison Features

### Goal

Extend Phase 1 with performance metrics, extraction method selection, strategy controls, and advanced analytics.

### Additional Features

1. **Performance Metrics Dashboard**

   - Real-time response times per strategy
   - Result count comparisons
   - Quality score calculations
   - Visual charts and indicators

2. **Extraction Method Selection**

   - Dropdown to switch between marker/pypdf/unstructured
   - Dynamic collection loading based on selection
   - All 12 collections support

3. **Strategy Selection Controls**

   - Checkboxes to enable/disable strategies
   - Dynamic grid layout adjustment
   - Color-coded strategy identification

4. **Use Case Presets**
   - Predefined scenarios (Conceptual, Technical, Methodological)
   - Optimized search parameters per use case
   - Strategy performance indicators per use case

### Enhanced UI Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Chunking Strategy Comparison                         │
├──────────────────────────────────────────────────────────────────────────┤
│ Query: [_________________________________] [Search]                      │
│ Extraction: [Dropdown: marker▼] Use Case: [Dropdown: Conceptual▼]        │
│ Strategies: [☑ Fixed] [☑ Semantic] [☑ Sliding LC] [☑ Sliding Unstr]      │
├──────────────────────────────────────────────────────────────────────────┤
│                        Performance Overview                              │
│ ┌─Strategy─────┬─Speed─┬─Results─┬─Avg Tokens─┬─Quality Score─┐           │
│ │ Fixed Size   │ 120ms │   47    │    450     │     0.82      │           │
│ │ Semantic     │  95ms │   52    │    380     │     0.91      │           │
│ │ Sliding LC   │ 140ms │   41    │    420     │     0.87      │           │
│ └──────────────┴───────┴─────────┴────────────┴───────────────┘           │
├──────────────────────────────────────────────────────────────────────────┤
│                      Results Comparison Grid                            │
│ [Enhanced side-by-side results with metrics and controls]                │
└──────────────────────────────────────────────────────────────────────────┘
```

### Implementation Approach Phase 2

- Build on Phase 1 foundation (no architectural changes)
- Add React components for complex interactions
- Integrate performance metrics API
- Implement responsive design enhancements

---

## Development Workflow

### Local Development

1. **Start Services**

   ```bash
   docker compose up typesense -d
   # Ensure collections are indexed
   ```

2. **Frontend Development**

   ```bash
   cd frontend
   npm install
   npm start
   # Access at http://localhost:3000
   ```

3. **Container Development**
   ```bash
   docker compose build frontend
   docker compose up frontend
   ```

### Testing Strategy

- **Functional Testing**: Verify search across all collections
- **Performance Testing**: Monitor response times with multiple queries
- **UI Testing**: Responsive design across devices
- **Integration Testing**: End-to-end with real Typesense data

### Dependencies

- **Required Services**: Typesense 29.0 with indexed collections
- **Required Collections**: marker\_\* collections (Phase 1), all 12 collections (Phase 2)
- **Network**: Docker bridge network for frontend-typesense communication

---

## Key Implementation Decisions

### Why Vanilla InstantSearch.js?

- **Simplicity**: Direct implementation following Typesense documentation
- **Performance**: Fewer dependencies than React InstantSearch
- **Foundation**: Easy to migrate to React later if needed
- **Examples**: Official Typesense examples use vanilla InstantSearch.js

### Why Federated Search Pattern?

- **Leverages Infrastructure**: Uses existing 12 collections
- **Clear Comparison**: Each collection represents one strategy
- **Performance**: Typesense handles multi-index queries efficiently
- **Demonstration**: Visually shows "different strategies, different results"

### Why Phased Approach?

- **Quick Wins**: Phase 1 delivers immediate value
- **Risk Mitigation**: Incremental complexity addition
- **User Feedback**: Learn from Phase 1 before building Phase 2
- **Resource Management**: Manageable development cycles

---

## Troubleshooting

### Common Issues

1. **Collection Access**: Verify all marker\_\* collections exist and are indexed
2. **Network Connectivity**: Ensure frontend can reach typesense:8108
3. **Search Performance**: Monitor response times, optimize query parameters
4. **CORS Issues**: Verify Typesense CORS configuration

### Debug Tools

- **Typesense Dashboard**: http://localhost:8110
- **Browser DevTools**: Network tab for query inspection
- **Console Logs**: Search client debug information

---

## Success Metrics

### Phase 1 Success

- Functional federated search across 4 collections
- Professional UI with Algolia styling
- Response times under 500ms
- Clear visual differentiation between strategies

### Phase 2 Success

- Comprehensive metrics dashboard
- Intuitive strategy selection controls
- Meaningful performance comparisons
- Production-ready user experience

### Business Value

- Demonstrates chunking strategy impact on search results
- Provides data-driven strategy selection guidance
- Supports RAG system design decisions
- Enables compelling stakeholder presentations
