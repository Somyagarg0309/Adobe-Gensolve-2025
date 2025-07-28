# Persona-Driven Document Intelligence

This solution implements a modular, offline-first pipeline for intelligent document analysis. It's designed to extract and prioritize document sections based on a user's persona and their specific "job-to-be-done," ensuring that only the most relevant information is retrieved. The system achieves this by first building a rich, structurally-aware knowledge base from the provided documents and then leveraging modern vector search techniques.

## Overview

In today's information-rich environment, users often struggle to find precise information within vast document repositories. This project addresses that challenge by providing a smart document intelligence system that understands user intent (via "job-to-be-done") and user context (via "persona") to deliver highly relevant document excerpts. The offline-first design makes it suitable for environments with limited or no internet connectivity, prioritizing data privacy and on-premise processing.

## Architecture

The system's architecture is divided into three core, sequential stages:

### Stage 1: Structural Analysis & Content Ingestion

This initial stage is critical for transforming raw PDF documents into a structured and searchable format. It focuses on preserving the inherent hierarchy of the documents, which is often lost in simple text extraction.

  * **Dynamic Heading Extraction:** A robust, dynamic engine processes each PDF document to extract its structured outline (e.g., H1, H2, H3 headings) along with their corresponding page numbers. This engine employs a hybrid approach:

      * **Visual Analysis:** It analyzes font size, boldness, and other visual cues to identify potential headings.
      * **Pattern-Based Analysis:** It uses regular expressions and layout analysis to detect common heading patterns like numbering (e.g., "1. Introduction", "2.1 Sub-section") and consistent spacing.
        This dynamic approach is crucial because it avoids reliance on hardcoded rules, making it adaptable to a wide variety of document formats and ensuring that the structural context is preserved.

  * **Text Chunking with Metadata:** The complete text of each document is extracted page by page. This raw text is then intelligently divided into manageable, overlapping chunks using a `RecursiveCharacterTextSplitter`. Each chunk is enriched with vital metadata to maintain its contextual awareness:

      * `source`: The original filename of the document.
      * `page`: The page number from which the chunk was extracted.
      * `section_title`: The specific heading under which the chunk falls, as determined by the heading extraction engine.
        This metadata is paramount for later stages, allowing for precise retrieval and reconstruction of the document's original structure.

### Stage 2: Vectorized Knowledge Base Creation

Once the documents are processed and chunked, a comprehensive and searchable knowledge base is constructed using vector embeddings.

  * **Embedding Generation:** The `sentence-transformers` library, specifically the `all-MiniLM-L6-v2` model, is utilized to convert each text chunk into a high-dimensional vector embedding.

    **Why `all-MiniLM-L6-v2`?**

    This model was chosen for its optimal balance of performance, efficiency, and offline capabilities, aligning perfectly with the challenge constraints.

    **Comparison of Embedding Models**

    | Feature / Model          | Word2Vec                                  | BERT (Base/Large)                                 | **`all-MiniLM-L6-v2` (Chosen)** |
    | :----------------------- | :---------------------------------------- | :------------------------------------------------ | :------------------------------------------------- |
    | **Type** | Word-level embedding                      | Contextual word embedding (requires pooling for sentences) | Dedicated sentence embedding (SBERT derivative)    |
    | **Context Awareness** | Limited (static embeddings)               | High (words get different embeddings based on context) | High (sentences get semantically meaningful embeddings) |
    | **Output** | Word vectors                              | Word vectors (need aggregation for sentences)     | Direct sentence vectors                            |
    | **Size / Footprint** | Small (pre-computed word vectors)         | Large (hundreds of MBs to GBs)                    | **Very Compact (\<100MB)** |
    | **Computational Cost** | Low                                       | High (for full model inference)                   | Moderate (optimized for efficiency)                |
    | **Offline Capability** | Yes                                       | Yes (once downloaded)                             | **Yes (efficiently)** |
    | **Ease of Use for Sem. Search** | Requires manual sentence aggregation, less effective | Requires specific fine-tuning for sentence similarity | **Directly optimized for semantic search** |
    | **Relevance for this Project** | Less suitable for sentence-level semantic search | Overkill in size/compute for offline, may need fine-tuning for best sentence results | **Ideal for offline, efficient semantic sentence embeddings** |

  * **FAISS Indexing:** All generated vector embeddings are indexed into a FAISS (Facebook AI Similarity Search) vector store.

    **Why FAISS?**

    FAISS is a highly optimized library for efficient similarity search and clustering of dense vectors, making it an excellent choice for this offline, performance-critical solution.

    **Comparison of Vector Search/Ranking Approaches**

    | Feature / Approach       | Traditional Keyword Search (e.g., Lucene) | General Database (without vector extensions)        | Other ANN Libraries (e.g., Annoy, NMSLIB) | **FAISS (Chosen)** |
    | :----------------------- | :---------------------------------------- | :-------------------------------------------------- | :---------------------------------------- | :------------------------------------------------- |
    | **Search Type** | Keyword matching, inverted index          | Exact match, relational queries                     | Approximate Nearest Neighbor (ANN)        | **Approximate Nearest Neighbor (ANN)** |
    | **Semantic Understanding** | None (purely lexical)                     | None                                                | High (based on vector similarity)         | **High (based on vector similarity)** |
    | **Speed for Large Vectors** | N/A                                       | Very slow/inefficient for vector similarity         | Fast                                      | **Extremely Fast & Scalable** |
    | **Scalability** | Good for text search                      | Good for structured data                            | Good                                      | **Excellent (various indexing algorithms)** |
    | **Offline Capability** | Yes                                       | Yes                                                 | Yes                                       | **Yes (CPU-only, no external services needed)** |
    | **Memory Footprint** | Can be high for full-text indexes         | Varies                                              | Efficient                                 | **Efficient (depends on index type)** |
    | **Ease of Use** | High for keyword search                   | High for SQL                                        | Moderate                                  | **Moderate (well-documented, powerful)** |
    | **Relevance for this Project** | Lacks semantic search                 | Not designed for vector similarity                  | Strong contender, but FAISS offers broader algorithm choices | **Optimal for high-performance, offline vector similarity** |

### Stage 3: Persona-Driven Retrieval and Ranking

The final stage integrates the user's persona and "job-to-be-done" to query the vectorized knowledge base and generate the desired output.

  * **Querying:** The text from `job.txt` (representing the user's "job-to-be-done" or query) is embedded into a vector using the *same* `sentence-transformer` model (`all-MiniLM-L6-v2`) used in Stage 2. This ensures consistency in the embedding space, allowing for accurate similarity comparisons.
  * **Similarity Search:** This query vector is then used to perform a similarity search against the FAISS index. The system retrieves the top `N` (configurable, default `10`) most semantically relevant text chunks from across the entire document collection. FAISS efficiently identifies the closest vectors to the query vector in the high-dimensional space.
  * **Ranking and Formatting:** The retrieved chunks are ranked based on their relevance score obtained directly from the FAISS search (lower score indicates higher relevance in FAISS for distance metrics). This ranked list is then formatted into the `output.json` file, populating the `extracted_sections` and `sub_section_analysis` fields as required by the challenge specification. The `importance_rank` is assigned based on this relevance ordering.

This end-to-end, offline approach ensures that the system can accurately and efficiently pinpoint the most important information for a specific user, powered by a deep, structural understanding of the source documents.

## Directory Structure

```
├── input/
│   ├── persona.txt
│   ├── job.txt
│   └── document1.pdf
│   └── document2.pdf
│   └── ...
├── output/
│   └── output.json
└── app/
    ├── main.py
    └── Dockerfile
    └── requirements.txt
```

  * `input/`: This directory contains all input files for the application.
      * `persona.txt`: Defines the user's persona.
      * `job.txt`: Describes the "job-to-be-done" or the user's specific query/need.
      * `*.pdf`: All PDF documents to be analyzed by the system.
  * `output/`: This directory will store the `output.json` generated by the application.
  * `app/`: Contains the core application code and Docker-related files.
      * `main.py`: The main Python script implementing the document intelligence pipeline.
      * `Dockerfile`: Defines the Docker image for the application.
      * `requirements.txt`: Lists Python dependencies.

## Docker Information

The solution is designed to run within a Docker container, ensuring a consistent and isolated environment.

**Dockerfile:**

```dockerfile
# Use a slim Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY app/ .

# Create input and output directories
RUN mkdir -p /app/input
RUN mkdir -p /app/output

# Command to run the application
CMD ["python", "main.py"]
```

**`requirements.txt`:**

```
PyMuPDF==1.23.8 # fitz
scikit-learn==1.3.2
numpy==1.26.4
pandas==2.2.2
sentence-transformers==2.7.0
langchain==0.1.20
faiss-cpu==1.8.0
```

**To Build and Run the Docker Container:**

1.  **Navigate to the root directory** of the project where `Dockerfile` and `app` directory are located.
2.  **Place your input files** (`persona.txt`, `job.txt`, and your PDF documents) into the `input/` directory.
3.  **Build the Docker image:**
    ```bash
    docker build -t persona-document-intelligence .
    ```
4.  **Run the Docker container:**
    ```bash
    docker run --rm \
        -v "$(pwd)/input:/app/input" \
        -v "$(pwd)/output:/app/output" \
        persona-document-intelligence
    ```
      * `--rm`: Automatically removes the container when it exits.
      * `-v "$(pwd)/input:/app/input"`: Mounts your local `input` directory to the container's `/app/input` directory, allowing the container to access your input files.
      * `-v "$(pwd)/output:/app/output"`: Mounts your local `output` directory to the container's `/app/output` directory, so the generated `output.json` file will be accessible on your host machine.

After the container finishes execution, you will find the `output.json` file in your local `output/` directory.
