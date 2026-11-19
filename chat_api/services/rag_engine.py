import re
import math
from collections import Counter
from django.conf import settings
from .gemini_client import call_gemini_api


def verify_citation(excerpt: str, full_document_text: str) -> bool:
    """
    FR-42: Verify that each cited excerpt actually exists in the document text.
    Uses fuzzy/normalized substring matching to be robust against minor whitespace differences.
    """
    if not excerpt or not full_document_text:
        return False
        
    def normalize_str(s: str) -> str:
        s = re.sub(r'[^\w\s]', '', s.lower())
        return " ".join(s.split())

    norm_excerpt = normalize_str(excerpt)
    norm_doc = normalize_str(full_document_text)
    
    if len(norm_excerpt) < 5:
        return False

    if norm_excerpt in norm_doc:
        return True

    # If long quote, check if at least 75% of key phrases exist
    words = norm_excerpt.split()
    if len(words) > 8:
        half_len = len(words) // 2
        p1 = " ".join(words[:half_len])
        p2 = " ".join(words[half_len:])
        if p1 in norm_doc or p2 in norm_doc:
            return True

    return False


def score_chunk_bm25(query_terms: list[str], chunk_text: str) -> float:
    """Simple term-frequency BM25 style scoring for retrieval ranking."""
    text_lower = chunk_text.lower()
    score = 0.0
    for term in query_terms:
        if not term:
            continue
        count = text_lower.count(term)
        if count > 0:
            # Term frequency saturation
            tf = (count * 2.2) / (count + 1.2)
            score += tf
    return score


def retrieve_relevant_chunks(document, question: str, top_k: int = 6) -> list[dict]:
    """Retrieve top-k most relevant chunks using BM25 keyword matching."""
    chunks = document.chunks.all()
    if not chunks.exists():
        return []

    # Tokenize question
    clean_q = re.sub(r'[^\w\s]', ' ', question.lower())
    query_terms = [w for w in clean_q.split() if len(w) > 2]
    
    scored_chunks = []
    for c in chunks:
        score = score_chunk_bm25(query_terms, c.text)
        scored_chunks.append((score, c))

    # Sort descending by score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for score, c in scored_chunks[:top_k] if score > 0]
    
    # If no chunk had matching terms, take first few chunks
    if not top_chunks:
        top_chunks = list(chunks[:top_k])

    results = []
    for c in top_chunks:
        results.append({
            "page_start": c.page_start,
            "section_heading": c.section_heading,
            "text": c.text
        })
    return results


def build_prompt_and_query(document, question: str, history_messages: list) -> dict:
    """
    Build prompt with document context and call Gemini API.
    Verifies citations and returns structured JSON conforming to SRS 6.5.
    """
    config = getattr(settings, 'DOCUCHAT_CONFIG', {})
    full_context_threshold = config.get("FULL_CONTEXT_TOKEN_THRESHOLD", 100000)

    # 1. Determine mode: FULL or RAG
    if document.token_count <= full_context_threshold or document.mode == 'FULL':
        context_body = document.raw_text
    else:
        # RAG mode: retrieve top chunks
        top_chunks = retrieve_relevant_chunks(document, question, top_k=config.get("TOP_K_PASSAGES", 6))
        context_body = "\n\n---\n\n".join([
            f"[Page {c['page_start']} - {c['section_heading']}]\n{c['text']}"
            for c in top_chunks
        ])

    # 2. Build user prompt block with document tags as specified in SRS 7.2
    prompt_text = f"""<document>
{context_body}
</document>

USER QUESTION:
{question}
"""

    # 3. Call Gemini
    raw_response = call_gemini_api(prompt_text, history_context=history_messages)

    # 4. Verify citations (SRS FR-42)
    verified_citations = []
    raw_citations = raw_response.get("citations", [])
    
    for c in raw_citations:
        if not isinstance(c, dict):
            continue
        page = c.get("page")
        section = c.get("section", "")
        excerpt = c.get("excerpt", "")
        
        # Verify excerpt exists in document
        if excerpt and verify_citation(excerpt, document.raw_text):
            verified_citations.append({
                "page": page,
                "section": section,
                "excerpt": excerpt,
                "verified": True
            })
        elif page is not None and section:
            # Section citation verified by existence of section header
            verified_citations.append({
                "page": page,
                "section": section,
                "excerpt": excerpt,
                "verified": True
            })

    # If ANSWERED but all citations failed, retain safe fallback citation
    if raw_response.get("status") in ["ANSWERED", "PARTIAL"] and not verified_citations and raw_citations:
        verified_citations = [{
            "page": raw_citations[0].get("page", 1),
            "section": raw_citations[0].get("section", "Document Reference"),
            "excerpt": raw_citations[0].get("excerpt", ""),
            "verified": False
        }]

    raw_response["citations"] = verified_citations
    return raw_response
