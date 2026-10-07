from pathlib import Path
from typing import Dict, Any, List

def extract_text(pdf_path: str) -> Dict[str, Any]:
    full_text = ""
    pages = []
    marked_lines = []
    
    try:
        import pymupdf
        with pymupdf.open(pdf_path) as doc:
            for page_idx, page in enumerate(doc):
                text = page.get_text()
                p_lines = text.splitlines()
                pages.append({"n": page_idx + 1, "lines": p_lines})
                for line_idx, line in enumerate(p_lines):
                    marked_lines.append(f"[p{page_idx + 1}:L{line_idx + 1}] {line}")
                full_text += text + "\n"
    except Exception:
        # Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                p_lines = text.splitlines()
                pages.append({"n": page_idx + 1, "lines": p_lines})
                for line_idx, line in enumerate(p_lines):
                    marked_lines.append(f"[p{page_idx + 1}:L{line_idx + 1}] {line}")
                full_text += text + "\n"
        except Exception as e:
            full_text = f"Error extracting PDF text: {e}"

    return {
        "pages": pages,
        "marked_text": "\n".join(marked_lines),
        "full_text": full_text
    }

def verify_quote(full_text: str, quote: str) -> bool:
    """Verifies that normalized quote is a substring of paper text."""
    if not quote or not full_text:
        return False
    norm_full = " ".join(full_text.split())
    norm_quote = " ".join(quote.split())
    return norm_quote in norm_full

