# @title The Definitive Master Engine and its Components (v7.0 - Compliant)
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

# ==============================================================================
# FINALIZED HELPER FUNCTIONS
# ==============================================================================

def _get_document_baseline(doc):
    """Calculates the most common font size for the document's body text."""
    if not doc or doc.is_closed or doc.page_count == 0: return 10
    sizes = Counter()
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            if "lines" in block:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        sizes[round(span["size"])] += len(span["text"])
    return sizes.most_common(1)[0][0] if sizes else 10

def _identify_repeating_elements(doc):
    """Identifies headers/footers by finding text that repeats across pages."""
    if not doc or doc.is_closed or len(doc) < 3:
        return set(), set()
    repeating_texts = Counter()
    for page in doc:
        top_rect = fitz.Rect(0, 0, page.rect.width, page.rect.height * 0.1)
        bottom_rect = fitz.Rect(0, page.rect.height * 0.9, page.rect.width, page.rect.height)
        for rect, key in [(top_rect, "header"), (bottom_rect, "footer")]:
            text = page.get_text(clip=rect, sort=True).strip()
            if text and len(text.split()) < 15 and not text.isdigit():
                repeating_texts[(text, key)] += 1
    min_occurrence = max(2, len(doc) // 3)
    headers = {text for (text, key), count in repeating_texts.items() if key == 'header' and count >= min_occurrence}
    footers = {text for (text, key), count in repeating_texts.items() if key == 'footer' and count >= min_occurrence}
    return headers, footers

def _is_toc_page(page):
    """Heuristic to detect if a page is a Table of Contents."""
    blocks = page.get_text("blocks")
    if not blocks: return False
    toc_keywords = ["table of contents", "contents"]
    for b in blocks[:5]:
        if any(keyword in b[4].lower() for keyword in toc_keywords):
            return True
    dot_leader_count = sum(1 for b in blocks if "..." in b[4] and b[4].strip().endswith(tuple(map(str, range(10)))))
    if len(blocks) > 5 and dot_leader_count / len(blocks) > 0.3:
        return True
    return False

def _get_all_blocks(doc, headers, footers):
    """A standardized function to extract all text blocks with metadata."""
    all_blocks = []
    full_filter_list = headers.union(footers)
    for page_num, page in enumerate(doc):
        if _is_toc_page(page):
            continue
        for block in page.get_text("dict").get("blocks", []):
            block_text = " ".join(s["text"].strip() for l in block.get("lines", []) for s in l.get("spans", [])).strip()
            if not block_text or block_text.isdigit() or block_text in full_filter_list:
                continue
            if "lines" in block and block["lines"] and "spans" in block["lines"][0] and block["lines"][0]["spans"]:
                first_span = block["lines"][0]["spans"][0]
                all_blocks.append({
                    "text": block_text, "page": page_num + 1, "size": first_span["size"],
                    "bold": "bold" in first_span["font"].lower() or "black" in first_span["font"].lower(),
                    "y0": block['bbox'][1], "x0": block['bbox'][0]
                })
    return all_blocks

def _classify_document_type(doc, all_blocks):
    """Classifies the document to route it to the best engine."""
    if not all_blocks: return "flyer"
    text_content = " ".join(b['text'] for b in all_blocks)
    if len(doc) == 1 and np.mean([len(b['text'].split()) for b in all_blocks]) < 8:
        return "form"
    if len(doc) == 1:
        font_sizes = [b['size'] for b in all_blocks]
        if len(font_sizes) > 1 and np.std(font_sizes) > 4:
            return "flyer"
    hierarchical_headings = sum(1 for b in all_blocks if re.match(r"^\s*\d+(\.\d+)+", b['text']))
    if hierarchical_headings > len(doc) * 0.4:
        return "technical"
    if "request for proposal" in text_content.lower() or "rfp" in text_content.lower():
        return "business_rfp"
    return "business_rfp"

# ==============================================================================
# SPECIALIZED ENGINES
# ==============================================================================

def _run_visual_engine(doc, all_blocks, filter_list):
    """Specialist for technical documents with consistent styling."""
    df = pd.DataFrame(all_blocks)
    df = df[~df['text'].isin(filter_list)]
    if df.empty: return []
    features = StandardScaler().fit_transform(df[['size', 'bold', 'x0']])
    db = DBSCAN(eps=0.5, min_samples=3).fit(features)
    df['cluster'] = db.labels_
    if -1 not in df['cluster'].unique(): return []
    cluster_stats = df[df.cluster != -1].groupby('cluster').agg(count=('size', 'count')).reset_index()
    if cluster_stats.empty: return []
    body_cluster = cluster_stats.loc[cluster_stats['count'].idxmax()]['cluster']
    headings_df = df[(df['cluster'] != -1) & (df['cluster'] != body_cluster)].copy()
    noise_patterns = [r"^\s*\d+\s*$", r"©", r"table\s\d+", r"figure\s\d+", r"international software testing"]
    for pattern in noise_patterns:
        headings_df = headings_df[~headings_df['text'].str.contains(pattern, case=False, regex=True)]
    if headings_df.empty: return []
    avg_size = headings_df.groupby('cluster')['size'].mean().sort_values(ascending=False)
    level_map = {cid: f"H{min(i + 1, 4)}" for i, cid in enumerate(avg_size.index)}
    headings_df['level'] = headings_df['cluster'].map(level_map)
    final_outline = headings_df.sort_values(by=['page', 'y0'])[['level', 'text', 'page']].to_dict('records')
    return [h for h in final_outline if len(h['text'].split()) < 30]

def _run_hybrid_engine(doc, all_blocks):
    """A highly adaptive engine for business docs, forms, and flyers."""
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
            level = "H1" if "Appendix" in num_str else f"H{min(num_str.count('.') + 1, 4)}"
            
        elif is_bold and size > baseline_size * 1.15:
            if len(text.split()) < 5 and (i + 1 >= len(all_blocks) or len(all_blocks[i+1]['text'].split()) < 15):
                continue
            level = "H2" if size > baseline_size * 1.4 else "H3"
        
        if clean_text and level:
            outline.append({"level": level, "text": clean_text, "page": block["page"], "y0": block["y0"]})
    
    final_outline = []
    seen = set()
    for h in sorted(outline, key=lambda x: (x['page'], x['y0'])):
        if (h['text'], h['level']) not in seen:
            final_outline.append({'level': h['level'], 'text': h['text'], 'page': h['page']})
            seen.add((h['text'], h['level']))
    return final_outline

def _extract_from_bookmarks(doc):
    """Extracts headings from PDF bookmarks."""
    toc = doc.get_toc()
    return [{"level": f"H{level}", "text": ' '.join(title.split()), "page": page} for level, title, page in toc] if toc else None

# ==============================================================================
# THE MASTER ENGINE
# ==============================================================================

def run_master_engine(pdf_path: str):
    """The definitive, production-ready heading extraction solution."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"title": f"Error processing {os.path.basename(pdf_path)}", "outline": []}

    bookmark_outline = _extract_from_bookmarks(doc)
    if bookmark_outline:
        title = bookmark_outline[0]['text'] if bookmark_outline else "Untitled"
        return {"title": title, "outline": bookmark_outline[1:]}

    headers, footers = _identify_repeating_elements(doc)
    all_blocks = _get_all_blocks(doc, headers, footers)

    if not all_blocks:
        return {"title": "No text content found", "outline": []}

    first_page_top_blocks = [b for b in all_blocks if b['page'] == 1 and b['y0'] < doc[0].rect.height * 0.3]
    title = sorted(first_page_top_blocks, key=lambda x: -x['size'])[0]['text'] if first_page_top_blocks else "Untitled"

    doc_type = _classify_document_type(doc, all_blocks)
    
    outline = []
    if doc_type == 'technical':
        outline = _run_visual_engine(doc, all_blocks, headers.union(footers))
    else:
        outline = _run_hybrid_engine(doc, all_blocks)
    
    return {
        "title": title,
        "outline": outline,
    }

# ==============================================================================
# COMMAND-LINE INTERFACE FOR DOCKER EXECUTION
# ==============================================================================
def main():
    """
    Main function to automatically process all PDFs in the /app/input directory
    and save the JSON output to the /app/output directory.
    """
    input_dir = '/app/input'
    output_dir = '/app/output'

    if not os.path.exists(input_dir):
        print(f"Error: Input directory does not exist: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing {pdf_path}...")
            
            result = run_master_engine(pdf_path)
            
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    main()
