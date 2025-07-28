# Dynamic PDF Heading Extraction Engine

**Adobe India Hackathon 2025 (Connecting The dots) : Challenge 1A Solution**

-----

##  Overview

This project presents a robust, high-performance, and offline-first Python solution for **dynamic PDF heading extraction**. Developed as part of the **Adobe Connecting the dots Hackathon (Challenge 1A)**, our "Master Engine" intelligently analyzes diverse PDF documents to generate a structured outline (Title, H1, H2, H3, and corresponding page numbers).

Unlike traditional methods that rely on brittle, hardcoded rules, our solution leverages a sophisticated, adaptive architecture that classifies document types on-the-fly and applies specialized extraction engines, ensuring accuracy across a wide range of document layouts.

-----

## Problem Statement

The core challenge, as outlined in the [official Adobe Hackathon document](https://d8it4huxumps7.cloudfront.net/uploads/submissions_case/6874faecd848a_Adobe_India_Hackathon_-_Challenge_Doc.pdf), was to:

  * **Accurately extract structured outlines**: Identify document titles and hierarchical headings (H1, H2, H3) along with their page numbers.
  * **Handle diverse PDF structures**: The solution must be truly dynamic, adaptable to various layouts (e.g., technical reports, business proposals, forms, flyers) without pre-training on specific templates.
  * **Ensure high performance**: The engine needs to be fast, operate exclusively on CPU, and maintain a small computational footprint suitable for production environments.
  * **Offline-first capability**: The solution must function entirely offline.

-----

## Key Features

  * **Intelligent Document Classification**: Dynamically categorizes PDFs into "technical," "business\_rfp," "form," or "flyer" types to optimize extraction strategy.
  * **Adaptive Visual Engine**: Utilizes unsupervised clustering (DBSCAN) to identify heading styles based on font size, boldness, and position, ideal for technical documents with consistent typography.
  * **Robust Hybrid Engine**: A versatile rule-based engine combining pattern recognition (for numbered headings), stylistic analysis (font size/boldness relative to baseline), and structural "look-ahead" for general business documents.
  * **Bookmark Prioritization**: Extracts outlines directly from PDF bookmarks when available, providing the fastest and most reliable method.
  * **Automated Header/Footer & ToC Removal**: Cleans document text by intelligently identifying and filtering out repetitive page elements and Table of Contents pages.
  * **Production-Ready**: Designed for efficiency, reliability, and minimal resource consumption in a CPU-only environment.
  * **Schema-Compliant JSON Output**: Provides a clean, structured JSON output for easy integration into downstream applications.

-----

## Behind the Logic: Research & Methodology

Our Master Engine's design is a culmination of established research principles in Document Layout Analysis and our innovative adaptations to meet the challenge's stringent requirements.

### Core Architecture: The "Master Engine" as an Intelligent Router

The decision to implement a multi-engine architecture, rather than a single monolithic approach, stems from the understanding that **document structure analysis is context-dependent**. Different document types exhibit unique visual and logical characteristics. Routing to specialized engines ensures optimal performance and accuracy.

### Specialized Engine Methodologies:

1.  **The Adaptive Visual Engine (Inspired by Unsupervised Learning & Typographic Analysis)**

      * **Concept**: This engine embodies the principle of "learning" the document's inherent style guide without explicit rules. It's particularly effective for documents where visual consistency dictates hierarchy, common in technical publications.
      * **Research Backing**:
          * **Unsupervised Learning**: Our approach aligns with the idea of using clustering to discover latent structures in data, a core concept in unsupervised learning. This avoids the need for large, labeled datasets for training.
          * **Homogeneous Blocks (Lin, 2009)**: The work by Lin (2009) on grouping text into "homogeneous blocks" based on consistent font properties directly influenced our feature engineering, emphasizing that visual cues like font size and boldness are strong indicators of structural roles.
          * **Document Profiling (El-Shayeb et al.)**: The concept of first profiling a document's general features to create a baseline for comparison, as mentioned by El-Shayeb et al. in their work on document analysis, supports our initial baseline font size calculation and subsequent relative analysis.
      * **Implementation**: We extract a numerical feature vector `[font_size, is_bold_flag, x_position]` for each text block. `StandardScaler` normalizes these features, and `DBSCAN` clusters them. DBSCAN is chosen for its ability to discover clusters of varying shapes and handle noise, without requiring the number of clusters (i.e., heading levels) to be predefined. The largest cluster is identified as body text, and remaining clusters are ranked by mean font size to assign "H" levels.

2.  **The Hybrid Two-Stage Engine (Pragmatic & Pattern-Driven)**

      * **Concept**: This engine prioritizes a blend of speed and precision, recognizing that many business and structured documents adhere to predictable numbering schemes while also using visual cues.
      * **Research Backing**:
          * **Two-Stage Approach (UMBC Paper)**: This approach is directly inspired by research advocating for a "two-stage" process in document analysis: a low-level block analysis followed by a high-level structural analysis. Our "High-Recall Visual Detection" acts as Stage 1, while "Logical Hierarchy Refinement" is Stage 2.
          * **Explicit Numbering Schemes (Lin, 2009)**: The importance of explicit numbering (e.g., "1.", "2.1", "A.") as a robust indicator for section headings is well-documented in literature, including Lin (2009). Our use of Regular Expressions (`re.compile`) is a direct application of this principle.
      * **Implementation**: Stage 1 broadly identifies potential heading candidates based on `font_size > baseline_size OR is_bold`. Stage 2 then applies sophisticated `regex` patterns to precisely detect numbered/lettered headings (e.g., `^\s*(?:(Appendix\s[A-Z])|(\d+(?:\.\d+)*)|([A-Z]))\s*[.:-]?\s*`). For non-numbered but visually prominent blocks, their level is inferred contextually. This dual approach ensures both high recall and high precision.

### General Architectural Principles:

  * **Pre-processing (Headers/Footers, ToC)**: Filtering out boilerplate elements and non-content pages is a common best practice in document information extraction to reduce noise and improve the accuracy of subsequent analysis, as emphasized in many PDF extraction tool overviews.
  * **Bookmark Extraction**: Utilizing embedded PDF metadata (like a document's Table of Contents or "Outline") is the most direct and reliable way to extract structure if available, as it represents the author's explicit intent.

By thoughtfully combining these principles and specialized engines, our Master Engine delivers a dynamic, robust, and performant solution for PDF heading extraction.

-----

## 🛠️ Installation & Usage (Docker)

The project is designed to run seamlessly within a Docker container, ensuring a consistent environment and ease of deployment.

### Prerequisites

  * Docker installed on your system.

### Steps

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/Somyagarg0309/Adobe-Gensolve-2025.git
    cd Adobe-Gensolve-2025/Challenge_1a
    ```

2.  **Place Your PDFs:**

    Create an `input` directory inside `Challenge_1a` (if it doesn't exist) and place all the PDF documents you want to process into this `input` folder.

    ```bash
    # Example:
    mkdir input
    mv /path/to/your/document.pdf input/
    ```

3.  **Build the Docker Image:**

    Navigate to the `Challenge_1a` directory and build the Docker image. This process installs all necessary Python dependencies.

    ```bash
    docker build -t pdf-heading-extractor .
    ```

4.  **Run the Extraction:**

    Execute the Docker container. This command will:

      * Mount your local `input` directory to `/app/input` inside the container.
      * Mount your local `output` directory to `/app/output` inside the container.
      * Run the `main` function of our script, which processes all PDFs in `/app/input`.
      * Save the resulting JSON files to `/app/output` on your host machine.

    <!-- end list -->

    ```bash
    docker run -v "$(pwd)/input":/app/input -v "$(pwd)/output":/app/output pdf-heading-extractor
    ```

    You will see processing messages in your console:

    ```
    Processing /app/input/your_document_name.pdf...
    Successfully generated /app/output/your_document_name.json
    ```

### Output Format

For each processed PDF, a corresponding JSON file will be generated in the `output` directory. The structure of the JSON output is as follows:

```json
{
  "title": "Your Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "1. Introduction to the Project",
      "page": 2
    },
    {
      "level": "H2",
      "text": "1.1 Background and Motivation",
      "page": 2
    },
    {
      "level": "H3",
      "text": "1.1.1 Problem Statement",
      "page": 3
    },
    {
      "level": "H1",
      "text": "2. System Architecture",
      "page": 5
    }
    // ... more headings
  ]
}
```

-----

## Project Structure

```
.
├── Challenge_1a/
│   ├── main.py                     # The core Master Engine Python script
│   ├── Dockerfile                  # Dockerfile for containerization
│   ├── requirements.txt            # Python dependencies
│   ├── input/                      # Directory for input PDFs (created by user)
│   └── output/                     # Directory for generated JSON outputs (created by script)
└── README.md
```

-----

## Dependencies

The solution relies on the following Python libraries:

  * `fitz` (PyMuPDF): A high-performance library for PDF parsing, text extraction, and layout analysis.
  * `scikit-learn`: Provides machine learning tools, specifically `DBSCAN` for clustering and `StandardScaler` for feature scaling.
  * `numpy`: Fundamental package for numerical computing in Python.
  * `pandas`: Powerful data structures for data analysis and manipulation, used in the visual engine.
  * Standard Python libraries: `os`, `re`, `json`, `collections.Counter` for common utilities.

These dependencies are listed in `requirements.txt` and automatically installed when building the Docker image.

-----
