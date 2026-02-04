# ### **1. Hook & Introduction (3 slides, 3 min total)**

**Slide 1.1: The Problem**

- Example question: "Why did the chatbot miss the answer when the document clearly had it?"
- Single screenshot: Failed RAG output (hallucination or incomplete answer)

**Slide 1.2: Same Question, Different Results**

- Side-by-side screenshots from ArXiv paper example:
  - **Left**: Bad result from poor chunking (fixed-size that cuts mid-sentence)
  - **Right**: Good result from better chunking (semantic chunking)
- Same question: "What is the main contribution of transformer architecture?"

**Slide 1.3: The Real Issue**

- Show the actual chunks that were retrieved for each result
- Message: _The issue isn't the LLM — it's how we broke down the document._

---

### **2. Why Chunking Is Mission-Critical (4 slides, 8 min total)**

**Slide 2.1: RAG Pipeline Overview**

- RAG Pipeline Diagram: **Document → Chunking → Embedding → Vector DB → Retrieval → LLM**
- Highlight chunking as the critical first step

> Note:
> We have to consider the impact of text extraction methods on chunking strategy.
> Different methods may produce varying text structures, affecting how we chunk the content.
> This is why I tested three different methods: `pypdf`, `unstructured`, and `marker`, and I would like to share the results with you.

**Slide 2.2: The Token Budget Problem**

- **Simple analogy**: "LLMs are like people with limited attention span"
- **Context window = Limited memory**: GPT-5 free tier can only "remember" 8K tokens at once (Plus: 32K, Pro: 128K)
- **The math problem**: 1 ArXiv paper = ~12K tokens, but GPT-5 free can only process 8K tokens
- **Chunking as the solution**: Break 12K tokens → 2-3 chunks of 4-6K tokens each
- **Token calculation reminder**: Typical ArXiv paper ~8-16 pages × 500-800 words/page × 0.75 tokens/word = 3K-9.6K tokens (rounded to ~12K for safety margin)
- **Visual**:
  - Left: Massive document trying to squeeze into tiny LLM box (doesn't fit!)
  - Right: Same document broken into perfect-sized chunks that fit perfectly
- **Key insight**: "You can't put a whale through a keyhole, but you can cut it into fish-sized pieces"

> **📝 Tokenization Explainer (for Q&A reference)**:
>
> Tokens are pre-defined units (not decisions made by the LLM) that can be:
>
> - **Characters**: Single letters, numbers, punctuation
> - **Sub-words**: Common sequences like "un##happi##ness"
> - **Whole words**: Complete common words
>
> **Process**: Text → Tokenization algorithm (BPE, WordPiece) → Sequence of numerical IDs → LLM processes numbers, not text
>
> **Key point**: LLMs see text as sequences of numbers, predict next most probable token based on learned relationships from training data.

**Slide 2.3: Precision vs. Recall Trade-off**

- Illustrate the **precision vs. recall trade-off**
- Small chunks = high precision, low recall
- Large chunks = low precision, high recall
- Visual diagram showing the balance

**Slide 2.4: Chunking Defines What's Retrievable**

- Key point: _Chunking defines what the retriever can even see_
- Example: Important information split across chunks = invisible to retrieval
- Visual: Same content, different chunking, different retrievability

---

### **3. Chunking Strategies (15 min)**

Visual side-by-side examples of chunking a single 2,000-word doc.

- **Fixed-size blocks**: Simple and fast baseline using `TokenTextSplitter` (e.g., 512 or 1024 tokens).
- **Sliding windows (LangChain)**: Overlapping chunks using `RecursiveCharacterTextSplitter` for document-structure-aware splitting.
- **Sliding windows (Unstructured)**: Element-based chunking using `partition_pdf()` with custom overlap logic.
- **Semantic chunking**: Meaning-preserving chunks using `SemanticChunker` to split at natural breakpoints.
- **Hybrid approaches**: Mentioned as a future enhancement but not implemented in the PoC.

> Include a live retrieval example:
>
> Ask the same question across different chunking methods → compare answers.

---

### **4. Tools & Libraries for Chunking (15 min)**

- **General-purpose chunkers**
  - LangChain: `TokenTextSplitter`, `RecursiveCharacterTextSplitter`, `SemanticChunker`
  - Unstructured.io: Multi-format ingestion and element-based chunking
- **Evaluation**
  - Metrics: Relevance scores, search speed, chunk coherence, and content completeness
  - Tools: Custom Python scripts for evaluation and Typesense for indexing/retrieval

👉 Replace “Drupal + Typesense integration” with **“Typesense-based vector search pipeline”**:

- Vector store: Typesense
- Show workflow: Content → Chunking → Embedding → Typesense → Retrieval

---

### **5. Live Demo: Chunking in Action (15–20 min)**

- Dataset: ArXiv papers (scientific PDFs with diverse structures).
- Implement 4 strategies: Fixed-size, Sliding Window (LangChain), Sliding Window (Unstructured), Semantic.
- Index all chunks in separate Typesense collections.
- Run the same 2 queries.
- Show:
  - Which chunks were retrieved.
  - The LLM answer.
- **Audience poll**: Which answer is closest to ground truth?

Optional metrics (visual chart):

- Retrieval accuracy (precision@k)
- Token usage per query
- Latency

---

### **6. Trade-offs & Best Practices (10 min)**

- **Cost vs. Quality vs. Latency triangle**
- When to use:
  - Fixed-length → fast prototyping, small docs
  - Sliding windows → structured content with overlaps
  - Semantic → long, complex documents
- Emphasize: _Always test retrieval quality before scaling._

---

### **7. Future Trends (5 min)**

- Adaptive, query-aware chunking
- Chunking + reranking
- Metadata-aware embeddings (tables, graphs, images)
- Standardization in evaluation (RAGAS, new benchmarks)

---

### **8. Key Takeaways (5 min)**

- **Chunking is the foundation of effective RAG.**
- Tools today let us go beyond fixed-size splitting.
- Sliding windows and semantic chunking are practical and effective.
- Measure retrieval, not just answers.
- The future is dynamic, context-aware chunking.

---

## 📌 Demo Implementation Options

- **Python-based demo** using LangChain + Unstructured + Typesense.
- Input: ArXiv PDFs (public dataset).
- Output: Side-by-side retrieval results from different chunking strategies.
- No CMS integration required — just raw text → chunks → embeddings → retrieval → answers.

---

## 📌 Slide Deck Flow

1. **Title**: _Smart Chunks, Better Search: Enhancing Vector Indexing with Typesense and AI Tools_
2. **Hook**: Failed RAG Answer Example (why did chatbot miss it?)
3. **Same Question, Different Results**: Bad vs Good chunking side-by-side
4. **The Real Issue**: Show actual chunks retrieved (it's the chunking, not the LLM)
5. **RAG Pipeline Overview**: Document → Chunking → Embedding → Vector DB → Retrieval → LLM
6. **Token Budget Problem**: GPT-5 limits (8K/32K/128K), ArXiv paper ~12K tokens, chunking solution
7. **Precision vs Recall Trade-off**: Small chunks (precise) vs Large chunks (comprehensive)
8. **Chunking Defines Retrievability**: Same content, different chunking, different results
9. **Chunking Strategies Overview**: 4 methods (Fixed-size, Sliding Window x2, Semantic)
10. **Tools & Libraries**: LangChain, Unstructured, Typesense pipeline
11. **Live Demo**: ArXiv papers, 4 strategies, side-by-side results, audience poll
12. **Evaluation Metrics**: Precision@k, token usage, latency comparison
13. **Trade-offs & Best Practices**: When to use each strategy
14. **Future Trends**: Adaptive chunking, reranking, metadata-aware embeddings
15. **Key Takeaways**: Chunking is foundation, measure retrieval quality
16. **Q&A** (with tokenization explainer ready for technical questions)
