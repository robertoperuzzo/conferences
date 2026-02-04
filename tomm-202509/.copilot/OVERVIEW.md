# Smart Chunks, Better Search

## Why didn’t the chatbot find the answer when the document clearly contained it?

## Overview

### Captivating Introduction

Getting good answers from a chatbot or semantic search system isn’t just about the model—it’s about how well your data is prepared. Chunking plays a huge role in how effective Retrieval-Augmented Generation (RAG) really is. In this session, we’ll shift the spotlight from flashy use cases to the behind-the-scenes work that makes them possible.

We'll explore what chunking strategies exist today, how they impact retrieval quality, and which tools can help you get it right—from lightweight syntax-aware chunkers to AI-powered semantic parsers.

### Prerequisite

Familiarity with basic understanding of vector search and an interest in AI-enhanced workflows. No deep AI or data science knowledge required—just a desire to go beyond the basics.

### Outline

In this session, we’ll explore why **chunking is a critical piece of the RAG (Retrieval-Augmented Generation) pipeline** and how the way we break down content can make or break the quality of AI responses. Too often, when answers fall short, the issue isn’t the LLM itself—it’s how the documents were prepared.

As part of an **investigation where I really got my hands dirty**, we explored the tools and strategies that make chunking effective. To extract and prepare text from PDFs, we experimented with:

- **PyPDFParser**
- **MarkItDown**
- **Unstructured.io**
- **Marker**

From there, we’ll dive into different **chunking strategies** and see how each impacts retrieval quality:

- **Fixed-size**
- **Semantic** using LangChain’s `SemanticChunker`
- **Sliding window**, using the LangChain's `RecursiveCharacterTextSplitter` to create overlapping chunks with document structure awareness

Through this hands-on exploration, we also discuss the **trade-offs between quality and performance**, share some basic metrics, and highlight key lessons learned.

### Learning Objectives

- Learn how chunking affects the quality of responses in vector search and RAG systems
- Discover modern tools and libraries that improve document segmentation and preprocessing
- Evaluate trade-offs and choose the best approach based on your project needs
