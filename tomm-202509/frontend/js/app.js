// Vanilla JavaScript Federated Search Application
// Using InstantSearch.js with Typesense adapter

// Typesense configuration for federated search
const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({
    server: {
        apiKey: "xyz",
        nodes: [
            {
                host: "localhost",
                port: "8108", 
                protocol: "http",
            },
        ],
        cacheSearchResultsForSeconds: 2 * 60,
    },
    // Common search parameters for all collections
    additionalSearchParameters: {
        highlight_fields: "content,document_title",
        snippet_threshold: 30,
        highlight_affix_num_tokens: 4,
        per_page: 20, // Increased since we're showing documents now, not chunks
    },
    // Collection-specific search parameters
    collectionSpecificSearchParameters: {
        unstructured_fixed_size: {
            query_by: "content,document_title",
        },
        unstructured_semantic: {
            query_by: "content,document_title",
        },
        unstructured_sliding_langchain: {
            query_by: "content,document_title",
        },
        unstructured_sliding_unstructured: {
            query_by: "content,document_title",
        },
    },
});

// Initialize InstantSearch
const search = instantsearch({
    indexName: "unstructured_fixed_size", // Primary index
    searchClient: typesenseInstantsearchAdapter.searchClient,
});

// Group hits by document_id for document-level display
function groupHitsByDocument(hits) {
    const documentGroups = {};
    
    // Debug: log the first hit to see available fields
    if (hits.length > 0) {
        console.log('First hit structure:', hits[0]);
        console.log('Available keys:', Object.keys(hits[0]));
        // Check if there's a text_match score
        if (hits[0].text_match) {
            console.log('Text match score:', hits[0].text_match);
        }
        if (hits[0].text_match_info) {
            console.log('Text match info:', hits[0].text_match_info);
        }
    }
    
    hits.forEach(hit => {
        const docId = hit.document_id || 'unknown';
        if (!documentGroups[docId]) {
            documentGroups[docId] = {
                document_id: docId,
                document_title: hit.document_title || 'Untitled Document',
                chunks: [],
                totalScore: 0,
                relevanceScore: 0,
                allChunkCount: 0,
                tokenRange: { min: Infinity, max: 0 }
            };
        }
        documentGroups[docId].chunks.push(hit);
        
        // Accumulate scores for averaging - try different score fields
        let score = 0;
        if (hit.text_match) {
            score = parseFloat(hit.text_match);
        } else if (hit.text_match_info && hit.text_match_info.score) {
            score = parseFloat(hit.text_match_info.score);
        } else if (hit._rankingInfo && hit._rankingInfo.score) {
            score = parseFloat(hit._rankingInfo.score);
        } else if (hit.score) {
            score = parseFloat(hit.score);
        } else if (hit._score) {
            score = parseFloat(hit._score);
        }
        documentGroups[docId].totalScore += score;
        
        // Track token count range
        const tokenCount = hit.token_count || 0;
        if (tokenCount > 0) {
            documentGroups[docId].tokenRange.min = Math.min(documentGroups[docId].tokenRange.min, tokenCount);
            documentGroups[docId].tokenRange.max = Math.max(documentGroups[docId].tokenRange.max, tokenCount);
        }
        
        // Estimate total chunks in document (this is approximate based on chunk indices)
        const chunkIndex = hit.chunk_index || 0;
        documentGroups[docId].allChunkCount = Math.max(documentGroups[docId].allChunkCount, chunkIndex + 1);
    });
    
    // Calculate average relevance score and sort documents
    return Object.values(documentGroups)
        .map(doc => {
            doc.relevanceScore = doc.chunks.length > 0 ? doc.totalScore / doc.chunks.length : 0;
            
            // Sort chunks by relevance and keep top 3 most relevant for preview
            doc.chunks = doc.chunks
                .sort((a, b) => {
                    const getScore = (hit) => {
                        if (hit.text_match) return parseFloat(hit.text_match);
                        if (hit.text_match_info && hit.text_match_info.score) {
                            return parseFloat(hit.text_match_info.score);
                        }
                        if (hit._rankingInfo && hit._rankingInfo.score) {
                            return parseFloat(hit._rankingInfo.score);
                        }
                        if (hit.score) return parseFloat(hit.score);
                        if (hit._score) return parseFloat(hit._score);
                        return 0;
                    };
                    return getScore(b) - getScore(a);
                })
                .slice(0, 3);
                
            // Clean up token range if no valid tokens found
            if (doc.tokenRange.min === Infinity) {
                doc.tokenRange.min = 0;
            }
            
            return doc;
        })
        .sort((a, b) => b.relevanceScore - a.relevanceScore);
}

// Hit template function for rendering document-level results
function renderDocumentHit(document, strategyName) {
    const getHighlightedTitle = (chunk) => {
        if (chunk._highlightResult && chunk._highlightResult.document_title && chunk._highlightResult.document_title.value) {
            return chunk._highlightResult.document_title.value;
        }
        return document.document_title;
    };

    const getHighlightedContent = (chunk) => {
        if (chunk._highlightResult && chunk._highlightResult.content && chunk._highlightResult.content.value) {
            return chunk._highlightResult.content.value;
        }
        return chunk.content || 'No content available';
    };

    // Calculate chunk statistics
    const tokenCounts = document.chunks.map(chunk => chunk.token_count || 0).filter(count => count > 0);
    const chunkIndices = document.chunks.map(chunk => chunk.chunk_index || 0);
    
    // Use the precomputed token range from grouping function
    const minTokens = document.tokenRange ? document.tokenRange.min : 
        (tokenCounts.length > 0 ? Math.min(...tokenCounts) : 0);
    const maxTokens = document.tokenRange ? document.tokenRange.max : 
        (tokenCounts.length > 0 ? Math.max(...tokenCounts) : 0);
    const totalChunks = document.allChunkCount || document.chunks.length;
    
    // Show the most relevant chunk content as a preview
    const topChunk = document.chunks[0];
    const previewContent = getHighlightedContent(topChunk);
    
    // Try different ways to get the score
    let topChunkScore = 0;
    if (topChunk.text_match) {
        topChunkScore = topChunk.text_match;
    } else if (topChunk.text_match_info && topChunk.text_match_info.score) {
        topChunkScore = topChunk.text_match_info.score;
    } else if (topChunk._rankingInfo && topChunk._rankingInfo.score) {
        topChunkScore = topChunk._rankingInfo.score;
    } else if (topChunk.score) {
        topChunkScore = topChunk.score;
    } else if (topChunk._score) {
        topChunkScore = topChunk._score;
    } else if (document.relevanceScore) {
        topChunkScore = document.relevanceScore;
    }
    
    const scoreDisplay = parseFloat(topChunkScore).toFixed(3);

    return `
        <div class="document-hit">
            <div class="document-header">
                <div class="hit-strategy">${strategyName}</div>
                <div class="document-title">${getHighlightedTitle(topChunk)}</div>
                <div class="document-meta">
                    Document ID: ${document.document_id} • 
                    ${document.chunks.length} relevant chunk${document.chunks.length !== 1 ? 's' : ''} found
                </div>
                <div class="chunk-stats">
                    Chunks: ${totalChunks} total • 
                    Tokens: ${minTokens > 0 ? (minTokens !== maxTokens ? `${minTokens}-${maxTokens}` : minTokens) : 'N/A'} per chunk •
                    Strategy: ${document.chunks[0].strategy_name || 'N/A'}
                </div>
            </div>
            <div class="document-preview">
                <div class="preview-label">
                    <span>Most relevant content:</span>
                    <span class="score-badge">Score: ${scoreDisplay}</span>
                </div>
                <div class="preview-content">${previewContent}</div>
            </div>
        </div>
    `;
}

// Configure search widgets
search.addWidgets([
    // Search Box
    instantsearch.widgets.searchBox({
        container: "#searchbox",
        placeholder: "Search for relevant documents across chunking strategies...",
        showLoadingIndicator: true,
    }),

    // Stats Display
    instantsearch.widgets.stats({
        container: "#stats",
        templates: {
            text: ({ nbHits, processingTimeMS, query }) => {
                if (query) {
                    return `${nbHits.toLocaleString()} documents found in ${processingTimeMS}ms`;
                }
                return 'Enter a search term to find relevant documents';
            }
        }
    }),

    // Fixed Size Strategy Results
    instantsearch.widgets.index({ indexName: "unstructured_fixed_size" })
        .addWidgets([
            instantsearch.widgets.hits({
                container: "#hits-fixed",
                templates: {
                    item: (hit) => {
                        if (hit._isDocumentGroup) {
                            return renderDocumentHit(hit._documentGroup, "Fixed Size");
                        }
                        return '';
                    },
                    empty: '<div class="empty-state">No documents found with fixed size chunking</div>',
                },
                transformItems(items) {
                    const documents = groupHitsByDocument(items);
                    // Return only one item per document to fix pagination
                    return documents.map(doc => ({
                        ...doc.chunks[0], // Use the top chunk as the base
                        _isDocumentGroup: true,
                        _documentGroup: doc,
                        objectID: `doc_${doc.document_id}` // Unique ID for the document
                    }));
                }
            }),
        ]),

    // Semantic Strategy Results  
    instantsearch.widgets.index({ indexName: "unstructured_semantic" })
        .addWidgets([
            instantsearch.widgets.hits({
                container: "#hits-semantic",
                templates: {
                    item: (hit) => {
                        if (hit._isDocumentGroup) {
                            return renderDocumentHit(hit._documentGroup, "Semantic");
                        }
                        return '';
                    },
                    empty: '<div class="empty-state">No documents found with semantic chunking</div>',
                },
                transformItems(items) {
                    const documents = groupHitsByDocument(items);
                    return documents.map(doc => ({
                        ...doc.chunks[0],
                        _isDocumentGroup: true,
                        _documentGroup: doc,
                        objectID: `doc_${doc.document_id}`
                    }));
                }
            }),
        ]),

    // Sliding LangChain Strategy Results
    instantsearch.widgets.index({ indexName: "unstructured_sliding_langchain" })
        .addWidgets([
            instantsearch.widgets.hits({
                container: "#hits-sliding-lc",
                templates: {
                    item: (hit) => {
                        if (hit._isDocumentGroup) {
                            return renderDocumentHit(hit._documentGroup, "Sliding (LangChain)");
                        }
                        return '';
                    },
                    empty: '<div class="empty-state">No documents found with sliding LangChain chunking</div>',
                },
                transformItems(items) {
                    const documents = groupHitsByDocument(items);
                    return documents.map(doc => ({
                        ...doc.chunks[0],
                        _isDocumentGroup: true,
                        _documentGroup: doc,
                        objectID: `doc_${doc.document_id}`
                    }));
                }
            }),
        ]),

        // Sliding Unstructured Strategy Results
    instantsearch.widgets.index({ indexName: "unstructured_sliding_unstructured" })
        .addWidgets([
            instantsearch.widgets.hits({
                container: "#hits-sliding-un",
                templates: {
                    item: (hit) => {
                        if (hit._isDocumentGroup) {
                            return renderDocumentHit(hit._documentGroup, "Sliding (Unstructured)");
                        }
                        return '';
                    },
                    empty: '<div class="empty-state">No documents found with sliding unstructured chunking</div>',
                },
                transformItems(items) {
                    const documents = groupHitsByDocument(items);
                    return documents.map(doc => ({
                        ...doc.chunks[0],
                        _isDocumentGroup: true,
                        _documentGroup: doc,
                        objectID: `doc_${doc.document_id}`
                    }));
                }
            }),
        ]),

    // Pagination (disabled since we're showing documents, not chunks)
    // instantsearch.widgets.pagination({
    //     container: "#pagination",
    //     padding: 2,
    //     showFirst: false,
    //     showLast: false,
    // }),
]);

// Start the search
search.start();

// Add some loading feedback
document.addEventListener('DOMContentLoaded', function() {
    const searchBox = document.querySelector('#searchbox input');
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            // Add a subtle loading indicator when typing
            const containers = ['#hits-fixed', '#hits-semantic', '#hits-sliding-lc', '#hits-sliding-un'];
            containers.forEach(container => {
                const element = document.querySelector(container);
                if (element) {
                    element.classList.add('loading');
                    setTimeout(() => element.classList.remove('loading'), 300);
                }
            });
        });
    }
});

console.log('Document-focused Federated Search Application Loaded - Ready to find relevant documents across chunking strategies!');
