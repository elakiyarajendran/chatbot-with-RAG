import re
import io
from pypdf import PdfReader
from docx import Document as DocxDocument


def count_tokens(text: str) -> int:
    """Approximate token count (1 token ~= 4 chars or 0.75 words)."""
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    return max(int(words * 1.3), int(chars / 4))


def clean_text(text: str) -> str:
    """Clean text, normalize whitespace and fix hyphenations."""
    # Fix hyphenation across lines (e.g., infor-\nmation -> information)
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    # Replace multiple newlines with at most double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace weird spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF with [Page X] tags."""
    stream = io.BytesIO(file_bytes)
    reader = PdfReader(stream)
    pages_text = []
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        cleaned = clean_text(extracted)
        pages_text.append(f"[Page {i}]\n{cleaned}")

    full_text = "\n\n".join(pages_text)
    return full_text, total_pages


def extract_from_docx(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from DOCX with approximate page markers."""
    stream = io.BytesIO(file_bytes)
    doc = DocxDocument(stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Group paragraphs into ~500 word blocks to simulate pages
    pages_text = []
    current_page = []
    current_words = 0
    page_num = 1
    
    for p in paragraphs:
        current_page.append(p)
        current_words += len(p.split())
        if current_words >= 450:
            pages_text.append(f"[Page {page_num}]\n" + "\n".join(current_page))
            current_page = []
            current_words = 0
            page_num += 1

    if current_page:
        pages_text.append(f"[Page {page_num}]\n" + "\n".join(current_page))

    full_text = "\n\n".join(pages_text)
    return full_text, max(1, page_num)


def extract_from_plain_text(text: str, filename: str = "text") -> tuple[str, int]:
    """Extract from plain text or markdown, inserting page markers if not present."""
    cleaned = clean_text(text)
    if "[Page " in cleaned:
        # Already has page markers
        matches = re.findall(r'\[Page (\d+)\]', cleaned)
        total_pages = max([int(m) for m in matches]) if matches else 1
        return cleaned, total_pages

    # Break into simulated pages of ~500 words
    words = cleaned.split()
    total_words = len(words)
    chunk_word_size = 450
    pages_text = []
    page_num = 1

    for i in range(0, max(1, total_words), chunk_word_size):
        page_words = words[i:i + chunk_word_size]
        pages_text.append(f"[Page {page_num}]\n" + " ".join(page_words))
        page_num += 1

    full_text = "\n\n".join(pages_text)
    return full_text, max(1, page_num - 1)


def chunk_document(full_text: str, chunk_size: int = 800, overlap: int = 120) -> list[dict]:
    """
    Split document into chunks storing metadata:
    chunk_index, page_start, page_end, section_heading, text
    """
    # Split text by page markers first
    page_blocks = re.split(r'\[Page (\d+)\]', full_text)
    
    pages = []
    # If starting with page marker
    if len(page_blocks) > 1:
        # page_blocks[0] is preamble, page_blocks[1] is page num, page_blocks[2] is text, etc.
        for i in range(1, len(page_blocks), 2):
            p_num = int(page_blocks[i])
            p_text = page_blocks[i + 1] if i + 1 < len(page_blocks) else ""
            pages.append({"page": p_num, "text": p_text.strip()})
    else:
        pages.append({"page": 1, "text": full_text})

    chunks = []
    chunk_idx = 0

    for p in pages:
        p_num = p["page"]
        text = p["text"]
        
        # Look for section headings like "4. Attendance Policy" or "4.1 Minimum Attendance"
        lines = text.split("\n")
        current_heading = f"Page {p_num}"
        buffer = []
        
        for line in lines:
            trimmed = line.strip()
            heading_match = re.match(r'^(\d+(\.\d+)*\s+[A-Z][\w\s,-]+)', trimmed)
            if heading_match:
                current_heading = heading_match.group(1)[:80]

            buffer.append(line)
            buf_text = "\n".join(buffer)
            toks = count_tokens(buf_text)

            if toks >= chunk_size:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_start": p_num,
                    "page_end": p_num,
                    "section_heading": current_heading,
                    "text": buf_text.strip()
                })
                chunk_idx += 1
                # keep overlap
                words = buf_text.split()
                overlap_words = words[-int(overlap * 0.75):] if len(words) > overlap else []
                buffer = [" ".join(overlap_words)] if overlap_words else []

        if buffer:
            remaining_text = "\n".join(buffer).strip()
            if remaining_text:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_start": p_num,
                    "page_end": p_num,
                    "section_heading": current_heading,
                    "text": remaining_text
                })
                chunk_idx += 1

    return chunks
