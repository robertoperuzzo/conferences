# ADR-012: Federated Search Implementation

## Status

Accepted

## Context

Following the successful implementation of:

- Multi-strategy chunking system with support for fixed_size, sliding_langchain, sliding_unstructured, and semantic strategies
- Typesense vector indexing system that creates 12 separate collections for each extraction method + chunking strategy combination (marker*\*, pypdf*\_, unstructured\_\_)
- Data pipeline that indexes chunks with comprehensive metadata

We need to implement **Federated Search** across multiple Typesense collections to demonstrate that "different chunking strategies produce different results" for the same query.

**Goals:**

1. Create a minimal working search interface using vanilla InstantSearch.js
2. Implement federated/multi-index search across collections
3. Display results side-by-side to show strategy differences
4. Use professional Algolia CSS styling
5. Establish foundation for ADR-013 (advanced comparison features)

## Decision

We will implement a **simple vanilla InstantSearch.js application** with federated search capabilities, following the official Typesense documentation patterns.

### 1. Simple Architecture

**Level 1 Structure** - Perfect for our simple vanilla JavaScript project:

```
frontend/
├── index.html                            # Main HTML structure with CDN links
├── js/
│   └── app.js                            # Main application logic (vanilla JS)
├── css/
│   └── main.css                          # Custom grid and layout styles
├── README.md                             # Project documentation
└── Dockerfile                            # nginx-based static file server
```

### 2. Federated Search Strategy

Using the **collectionSpecificSearchParameters** approach for multi-index search:

```javascript
const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({
  server: {
    apiKey: "xyz",
    nodes: [
      {
        host: "typesense",
        port: "8108",
        protocol: "http",
      },
    ],
    cacheSearchResultsForSeconds: 2 * 60,
  },
  // Common search parameters for all collections
  additionalSearchParameters: {
    highlight_fields: "content",
    snippet_threshold: 30,
    highlight_affix_num_tokens: 4,
  },
  // Collection-specific search parameters
  collectionSpecificSearchParameters: {
    marker_fixed_size: {
      query_by: "content,document_title",
    },
    marker_semantic: {
      query_by: "content,document_title",
    },
    marker_sliding_langchain: {
      query_by: "content,document_title",
    },
    marker_sliding_unstructured: {
      query_by: "content,document_title",
    },
  },
});
```

### Phase 1 UI Layout

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
│ │ │Result 2  │ │ │Result 2  │ │ │Result 2  │ │           │
│ │ └──────────┘ │ └──────────┘ │ └──────────┘ │           │
│ └──────────────┴──────────────┴──────────────┘           │
└──────────────────────────────────────────────────────────┘
```

### 4. Implementation Approach

#### Core Technologies:

- **InstantSearch.js** (vanilla JavaScript widgets via CDN)
- **typesense-instantsearch-adapter** (loaded via CDN)
- **nginx Alpine** for serving static files (lightweight Docker container)
- **Algolia CSS Base Themes** (reset + satellite) for professional styling foundation

#### Key Implementation Pattern:

**Vanilla JavaScript Approach with CDN dependencies:**

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
  <head>
    <title>Chunking Strategy Comparison</title>
    <!-- Algolia InstantSearch Base Styles -->
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/instantsearch.css@8.5.1/themes/reset-min.css"
    />
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/instantsearch.css@8.5.1/themes/satellite-min.css"
    />
    <!-- InstantSearch.js -->
    <script src="https://cdn.jsdelivr.net/npm/instantsearch.js@4.63.0/dist/instantsearch.production.min.js"></script>
    <!-- Typesense InstantSearch Adapter -->
    <script src="https://cdn.jsdelivr.net/npm/typesense-instantsearch-adapter@2.8.0/dist/typesense-instantsearch-adapter.min.js"></script>
    <!-- Custom Grid and Layout Styles -->
    <link rel="stylesheet" href="css/main.css" />
  </head>
  <body>
    <div id="searchbox-container">
      <div id="searchbox"></div>
    </div>

    <div id="search-results-container">
      <div class="facets-container">
        <div id="stats"></div>
      </div>

      <div class="search-results-list">
        <div class="results-grid">
          <div class="column">
            <h3>Fixed Size</h3>
            <div id="hits-fixed"></div>
          </div>
          <div class="column">
            <h3>Semantic</h3>
            <div id="hits-semantic"></div>
          </div>
          <div class="column">
            <h3>Sliding (LangChain)</h3>
            <div id="hits-sliding-lc"></div>
          </div>
          <div class="column">
            <h3>Sliding (Unstructured)</h3>
            <div id="hits-sliding-un"></div>
          </div>
        </div>

        <div id="pagination"></div>
      </div>
    </div>

    <script src="js/app.js"></script>
  </body>
</html>
```

```js
// js/app.js - Vanilla JavaScript with InstantSearch
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
    unstructured_fixed_size: { query_by: "content,document_title" },
    unstructured_semantic: { query_by: "content,document_title" },
    unstructured_sliding_langchain: { query_by: "content,document_title" },
    unstructured_sliding_unstructured: { query_by: "content,document_title" },
  },
});

const search = instantsearch({
  indexName: "unstructured_fixed_size",
  searchClient: typesenseInstantsearchAdapter.searchClient,
});

// Configure widgets
search.addWidgets([
  instantsearch.widgets.searchBox({ container: "#searchbox" }),
  instantsearch.widgets.stats({ container: "#stats" }),
  instantsearch.widgets
    .index({ indexName: "unstructured_fixed_size" })
    .addWidgets([
      instantsearch.widgets.hits({
        container: "#hits-fixed",
        templates: { item: (hit) => renderHit(hit, "Fixed Size") },
      }),
    ]),
  instantsearch.widgets
    .index({ indexName: "unstructured_semantic" })
    .addWidgets([
      instantsearch.widgets.hits({
        container: "#hits-semantic",
        templates: { item: (hit) => renderHit(hit, "Semantic") },
      }),
    ]),
  // ... other indices
]);

function renderHit(hit, strategyName) {
  return `
    <div class="hit">
      <div class="hit-strategy">${strategyName}</div>
      <div class="hit-meta">Chunk ${hit.chunk_index} • ${hit.token_count} tokens</div>
      <div class="hit-content">${hit._highlightResult.content.value}</div>
      <div class="hit-source">${hit.document_title}</div>
    </div>
  `;
}

search.start();
```

    marker_fixed_size: { query_by: "content,document_title" },
    marker_semantic: { query_by: "content,document_title" },
    marker_sliding_langchain: { query_by: "content,document_title" },
    marker_sliding_unstructured: { query_by: "content,document_title" },

},
});

// Hit template component
const HitTemplate = ({ hit, strategyName }) => (

  <div className="hit">
    <div className="hit-strategy">{strategyName}</div>
    <div className="hit-meta">
      Chunk {hit.chunk_index} • {hit.token_count} tokens
    </div>
    <div
      className="hit-content"
      dangerouslySetInnerHTML={{ __html: hit._highlightResult.content.value }}
    />
    <div className="hit-source">{hit.document_title}</div>
  </div>
);

function App() {
return (
<InstantSearch
      searchClient={typesenseInstantsearchAdapter.searchClient}
      indexName="marker_fixed_size"
    >

<div id="searchbox-container">
<SearchBox placeholder="Search across chunking strategies..." />
</div>

      <div id="search-results-container">
        <div id="facets-container">
          {/* Future: Add RefinementList, Stats, etc. */}
        </div>

        <div id="results-grid">
          <div className="column">
            <h3>Fixed Size</h3>
            <Index indexName="marker_fixed_size">
              <Hits
                hitComponent={({ hit }) => (
                  <HitTemplate hit={hit} strategyName="Fixed Size" />
                )}
              />
            </Index>
          </div>

          <div className="column">
            <h3>Semantic</h3>
            <Index indexName="marker_semantic">
              <Hits
                hitComponent={({ hit }) => (
                  <HitTemplate hit={hit} strategyName="Semantic" />
                )}
              />
            </Index>
          </div>

          <div className="column">
            <h3>Sliding (LangChain)</h3>
            <Index indexName="marker_sliding_langchain">
              <Hits
                hitComponent={({ hit }) => (
                  <HitTemplate hit={hit} strategyName="Sliding (LangChain)" />
                )}
              />
            </Index>
          </div>

          <div className="column">
            <h3>Sliding (Unstructured)</h3>
            <Index indexName="marker_sliding_unstructured">
              <Hits
                hitComponent={({ hit }) => (
                  <HitTemplate
                    hit={hit}
                    strategyName="Sliding (Unstructured)"
                  />
                )}
              />
            </Index>
          </div>
        </div>
      </div>
    </InstantSearch>

);
}

export default App;

````

### 5. Collection Integration

**Phase 1 Scope: Focus on unstructured\_\* collections** (4 strategies):

- `unstructured_fixed_size` - Fixed chunk size strategy
- `unstructured_semantic` - Semantic chunking strategy
- `unstructured_sliding_langchain` - LangChain sliding window
- `unstructured_sliding_unstructured` - Unstructured sliding window

**Data Fields Utilized:**

- `content` - Chunk text content (searchable, highlightable)
- `document_title` - Source document title (searchable)
- `chunk_index` - Position in document (display)
- `token_count` - Chunk size metric (display)
- `document_filename` - Source file (metadata display)

### 6. Docker Integration

**Environment Configuration:**

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  depends_on:
    - typesense
  environment:
    - REACT_APP_TYPESENSE_HOST=typesense
    - REACT_APP_TYPESENSE_PORT=8108
    - REACT_APP_TYPESENSE_PROTOCOL=http
    - REACT_APP_TYPESENSE_API_KEY=xyz
  networks:
    - chunker-demo
````

**Container Workflow:**

1. `docker compose build frontend` - Build container
2. `docker compose up frontend` - Start on localhost:3000
3. Internal network communication to `typesense:8108`

## Rationale

### Why Vanilla JavaScript InstantSearch?

- **Simplicity**: No complex build tools or frameworks required
- **Direct Integration**: Official InstantSearch.js vanilla widgets work directly with Typesense
- **Performance**: Lightweight implementation with minimal overhead
- **Maintenance**: Easier to understand and modify without framework knowledge
- **CDN Loading**: All dependencies loaded via CDN for fast development
- **Browser Compatibility**: Works in all modern browsers without transpilation

### Why Level 1 Structure for Vanilla JavaScript?

- **Perfect Project Size Match**: Our simple federated search demo fits the "small project" criteria exactly
- **Single Feature Focus**: One main feature (federated search) doesn't need complex modular organization
- **Vanilla JavaScript Organization**: Simple file separation by type (HTML, CSS, JS)
- **Clear Separation of Concerns**:
  - `index.html` - Static HTML structure and dependency loading
  - `js/app.js` - All application logic and InstantSearch configuration
  - `css/main.css` - Presentation layer styling
  - `assets/` - Static assets like favicon
- **Easy to Navigate**: Minimal files, perfect for quick development and stakeholder demos
- **Standard Convention**: Follows traditional web development file organization
- **Future Migration Path**: Can easily add more JavaScript files when adding features in ADR-013

### Why Federated Search Pattern?

- **Leverages Existing Infrastructure**: Uses 12 collections already created by indexer
- **Clear Strategy Comparison**: Each collection represents one chunking strategy
- **Performance**: Typesense handles multi-index queries efficiently
- **Demonstration Value**: Visually shows "different strategies, different results"

### Why Algolia CSS Base Themes?

- **Professional Foundation**: Reset and Satellite themes provide clean, production-ready styling
- **Customization Ready**: Base themes designed to be extended with custom CSS
- **CDN Performance**: Cached, minified CSS served from reliable CDN
- **Official Recommendation**: Algolia's recommended approach for custom InstantSearch UIs
- **Consistent Look**: Ensures our interface matches InstantSearch design standards
- **Minimal File Overhead**: No need to include large CSS files in our project

### Why Focus on unstructured\_\* Collections?

- **Reduced Complexity**: 4 strategies instead of 12 collections
- **Clear Comparison**: Same extraction method, different chunking strategies
- **Proof of Concept**: Establishes pattern for adding other extraction methods
- **Performance**: Fewer simultaneous queries for better response time

## Success Criteria

### Functional Requirements:

1. ✅ Single search box queries all 4 marker\_\* collections simultaneously
2. ✅ Results displayed in 4-column grid (Fixed, Semantic, Sliding LC, Sliding Unstructured)
3. ✅ Search term highlighting in chunk content
4. ✅ Chunk metadata display (index, token count, document title)
5. ✅ Professional UI using Algolia CSS theme

### Performance Requirements:

1. ✅ Search results appear within 500ms for typical queries
2. ✅ Responsive grid layout works on desktop and mobile
3. ✅ No blocking or UI freezing during searches

### Demonstration Requirements:

1. ✅ Clearly shows different results for same query across strategies
2. ✅ Highlights strategy differences through side-by-side comparison
3. ✅ Professional appearance suitable for stakeholder demos

## Implementation Plan

### Stage 1: Basic Setup

- [ ] Create minimal package.json with InstantSearch.js dependencies
- [ ] Create basic HTML structure with Algolia CSS
- [ ] Test Docker container builds and runs

### Stage 2: Typesense Integration

- [ ] Configure typesense-instantsearch-adapter with federated search
- [ ] Test connection to existing marker\_\* collections
- [ ] Verify search functionality across all 4 strategies
- [ ] Debug any collection access or query issues

### Stage 3: UI Implementation

- [ ] Implement responsive 4-column grid layout
- [ ] Style hit templates for chunk display
- [ ] Add search highlighting and metadata display
- [ ] Test with real search queries

### Stage 4: Refinement

- [ ] Polish styling and responsive behavior
- [ ] Add loading states and error handling
- [ ] Performance testing with multiple simultaneous queries
- [ ] Documentation and demo preparation

## Dependencies

**Required Services:**

- Typesense 29.0 running with marker\_\* collections indexed
- Docker network connectivity between frontend and typesense services

**Required Data:**

- `marker_fixed_size` collection with indexed chunks
- `marker_semantic` collection with indexed chunks
- `marker_sliding_langchain` collection with indexed chunks
- `marker_sliding_unstructured` collection with indexed chunks

**Collection Schema Requirements:**
Each collection must have these searchable/displayable fields:

- `content` (text, searchable)
- `document_title` (text, searchable)
- `chunk_index` (integer, facetable)
- `token_count` (integer, facetable)
- `document_filename` (text, facetable)

## Next Steps

ADR-013 will add:

- Performance metrics dashboard
- Extraction method comparison (marker vs pypdf vs unstructured)
- Strategy selection controls and filtering
- Advanced comparison features and analytics
- Use case presets (conceptual, technical, methodological)

## Risks & Mitigation

**Risk: Collection Unavailability**

- _Mitigation_: Verify all marker\_\* collections exist before frontend development
- _Fallback_: Graceful degradation with empty state messages

**Risk: Poor Search Performance**

- _Mitigation_: Limit results per collection (5-10 hits max)
- _Monitoring_: Test with representative queries and data volumes

**Risk: UI Complexity**

- _Mitigation_: Start with minimal viable interface, iterate based on feedback
- _Fallback_: Single-collection view if federated search proves problematic

## Notes

- **Proof of Concept Scope**: This establishes the foundation for chunking strategy comparison
- **Local Development**: All testing in Docker environment, no production deployment
- **Collection Dependencies**: Requires ADR-010 (Typesense Vector Indexing) completion
- **Future Extensibility**: Architecture designed to support ADR-013 enhancements
- **Browser Support**: Modern browsers only (Chrome 90+, Firefox 88+, Safari 14+)
