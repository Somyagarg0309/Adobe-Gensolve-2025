# Approach Explanation: Persona-Driven Document Intelligence

## Overview

This solution is designed as a modular, offline-first pipeline that intelligently extracts and prioritizes document sections based on a user persona and their specific "job-to-be-done." It achieves this by first creating a rich, structurally-aware knowledge base from the provided documents and then using modern vector search techniques to find the most relevant information.

The architecture is broken down into three core stages:

### Stage 1: Structural Analysis & Content Ingestion

This stage leverages the robust heading extraction engine developed in Challenge 1a. For each document in the input collection:

1.  **Dynamic Heading Extraction:** The document is processed to extract a structured outline (H1, H2, etc.) and page numbers. This engine is fully dynamic, using a hybrid of visual (font size, boldness) and pattern-based (numbering, layout) analysis to identify headings without any hardcoded rules. This provides crucial structural context that is often lost in simple text extraction.

2.  **Text Chunking with Metadata:** The full text of the document is extracted and split into manageable, overlapping chunks using a `RecursiveCharacterTextSplitter`. Crucially, each chunk is enriched with metadata, including its source filename, page number, and the specific heading it falls under (as determined by the 1a engine). This ensures that every piece of text retains its structural context.

### Stage 2: Vectorized Knowledge Base Creation

Once all documents are processed and chunked, a comprehensive and searchable knowledge base is created:

1.  **Embedding Generation:** The `sentence-transformers` library (specifically the `all-MiniLM-L6-v2` model) is used to convert each text chunk into a high-dimensional vector embedding. This model is chosen for its excellent performance, small footprint (<100MB), and offline capabilities, ensuring it meets all challenge constraints.

2.  **FAISS Indexing:** All vector embeddings are indexed into a `FAISS` (Facebook AI Similarity Search) vector store. FAISS is an extremely efficient library for similarity search that runs entirely on the CPU, making it perfect for this offline task. This index allows for near-instantaneous retrieval of the most semantically similar text chunks for any given query.

### Stage 3: Persona-Driven Retrieval and Ranking

The final stage uses the persona's "job-to-be-done" to query the knowledge base and generate the final output:

1.  **Querying:** The text from `job.txt` is embedded into a vector using the same sentence-transformer model.

2.  **Similarity Search:** This query vector is used to perform a similarity search against the FAISS index, retrieving the top N most relevant text chunks from across the entire document collection.

3.  **Ranking and Formatting:** The retrieved chunks are ranked based on their relevance score from the FAISS search. This ranked list is then formatted into the final `output.json`, populating the `extracted_sections` and `sub_section_analysis` fields as required by the challenge specification.

This end-to-end, offline approach ensures that the system can accurately and efficiently pinpoint the most important information for a specific user, powered by a deep, structural understanding of the source documents.