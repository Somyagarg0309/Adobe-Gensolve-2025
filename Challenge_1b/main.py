# @title Challenge 1b: Persona-Driven Document Intelligence Engine (Final)
import fitz  # PyMuPDF
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import time
import re
import json
import os
from collections import Counter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from datetime import datetime

# ==============================================================================
# CHALLENGE 1A HEADING EXTRACTION LOGIC (Encapsulated)
# ==============================================================================

def _get_document_baseline(doc):
    if not doc or doc.is_closed or doc.page_count == 0: return 10
    sizes = Counter()
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            if "lines" in block:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        sizes[round(span["size"])] += len(span["text"])
    return sizes.most_common(1)[0][0] if sizes else 10

def _get_all_blocks(doc):
    all_blocks = []
    for page_num, page in enumerate(doc):
        for block in page.get_text("dict").get("blocks", []):
            block_text = " ".join(s["text"].strip() for l in block.get("lines", []) for s in l.get("spans", [])).strip()
            if not block_text or block_text.isdigit():
                continue
            if "lines" in block and block["lines"] and "spans" in block["lines"][0] and block["lines"][0]["spans"]:
                first_span = block["lines"][0]["spans"][0]
                all_blocks.append({
                    "text": block_text, "page": page_num + 1, "size": first_span["size"],
                    "bold": "bold" in first_span["font"].lower() or "black" in first_span["font"].lower(),
                    "y0": block['bbox'][1]
                })
    return all_blocks

def run_heading_extraction(doc):
    all_blocks = _get_all_blocks(doc)
    if not all_blocks:
        return []

    baseline_size = _get_document_baseline(doc)
    outline = []
    numbered_pattern = re.compile(r"^\s*(?:(Appendix\s[A-Z])|(\d+(?:\.\d+)*)|([A-Z]))\s*[.:-]?\s*")

    for i, block in enumerate(all_blocks):
        text, is_bold, size = block['text'], block['bold'], block['size']
        level, clean_text = None, text
        match = numbered_pattern.match(text)
        
        if match:
            if not is_bold and (len(text.split()) < 5 and size < baseline_size * 1.1):
                continue
            groups, clean_text = match.groups(), text[match.end():].strip()
            num_str = next(g for g in groups if g is not None)
            level = 1 if "Appendix" in num_str else min(num_str.count('.') + 1, 4)
        elif is_bold and size > baseline_size * 1.15:
            if len(text.split()) < 5 and (i + 1 >= len(all_blocks) or len(all_blocks[i+1]['text'].split()) < 15):
                continue
            level = 2 if size > baseline_size * 1.4 else 3
        
        if clean_text and level:
            outline.append({"level": level, "text": clean_text, "page": block["page"], "y0": block["y0"]})
    
    final_outline = []
    seen = set()
    for h in sorted(outline, key=lambda x: (x['page'], x['y0'])):
        if (h['text'], h['level']) not in seen:
            final_outline.append({'level': f"H{h['level']}", 'text': h['text'], 'page': h['page']})
            seen.add((h['text'], h['level']))
    return final_outline

# ==============================================================================
# CHALLENGE 1B CORE LOGIC
# ==============================================================================

def process_documents(input_dir):
    all_docs_data = []
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    for filename in pdf_files:
        pdf_path = os.path.join(input_dir, filename)
        try:
            doc = fitz.open(pdf_path)
            headings = run_heading_extraction(doc)
            pages_text = [page.get_text() for page in doc]
            
            all_docs_data.append({
                "filename": filename,
                "headings": headings,
                "pages_text": pages_text
            })
            doc.close()
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    return all_docs_data

def create_knowledge_base(docs_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_chunks = []

    for data in docs_data:
        current_heading = "Introduction"
        for page_num, page_text in enumerate(data['pages_text'], 1):
            page_headings = [h for h in data['headings'] if h['page'] == page_num]
            if page_headings:
                current_heading = page_headings[0]['text']

            chunks = text_splitter.split_text(page_text)
            for chunk in chunks:
                all_chunks.append({
                    "page_content": chunk,
                    "metadata": {
                        "source": data['filename'],
                        "page": page_num,
                        "section_title": current_heading
                    }
                })

    if not all_chunks:
        return None

    # **FIX:** Point to the pre-downloaded model cache inside the container
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        cache_folder="/app/model_cache" # This tells the script where to find the model
    )
    
    documents = [doc['page_content'] for doc in all_chunks]
    metadatas = [doc['metadata'] for doc in all_chunks]
    
    vector_store = FAISS.from_texts(documents, embeddings, metadatas=metadatas)
    return vector_store

def find_relevant_sections(vector_store, query, top_k=10):
    if not vector_store:
        return []
    results_with_scores = vector_store.similarity_search_with_score(query, k=top_k)
    
    final_results = []
    for doc, score in results_with_scores:
        final_results.append({
            "document": doc.metadata.get("source", "Unknown"),
            "page_number": doc.metadata.get("page", 0),
            "section_title": doc.metadata.get("section_title", "Unknown"),
            "refined_text": doc.page_content,
            "relevance_score": float(score)
        })
    
    ranked_results = sorted(final_results, key=lambda x: x['relevance_score'])
    for i, item in enumerate(ranked_results):
        item['importance_rank'] = i + 1

    return ranked_results

def main():
    input_dir = '/app/input'
    output_dir = '/app/output'
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(os.path.join(input_dir, 'persona.txt'), 'r') as f:
            persona = f.read().strip()
        with open(os.path.join(input_dir, 'job.txt'), 'r') as f:
            job_to_be_done = f.read().strip()
        pdf_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')])
    except FileNotFoundError as e:
        print(f"Error: Missing input file - {e.filename}")
        return

    print("Processing documents to extract text and structure...")
    docs_data = process_documents(input_dir)
    
    print("Creating knowledge base and vector store...")
    vector_store = create_knowledge_base(docs_data)
    
    print(f"Searching for sections relevant to the job: '{job_to_be_done[:50]}...'")
    relevant_sections = find_relevant_sections(vector_store, job_to_be_done)

    output_data = {
        "metadata": {
            "input_documents": pdf_files,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": [
            {
                "document": sec["document"],
                "section_title": sec["section_title"],
                "importance_rank": sec["importance_rank"],
                "page_number": sec["page_number"]
            } for sec in relevant_sections
        ],
        "subsection_analysis": [
             {
                "document": sec["document"],
                "refined_text": sec["refined_text"],
                "page_number": sec["page_number"]
            } for sec in relevant_sections
        ]
    }

    output_path = os.path.join(output_dir, 'output.json')
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"\nProcessing complete. Output written to {output_path}")

if __name__ == "__main__":
    main()
