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

import hashlib
import os

class PDFValidationError(ValueError):
    """Raised when PDF fails format, size, page count, or text extractability validation."""
    pass

def validate_pdf_bytes(pdf_bytes: bytes) -> dict:
    if not pdf_bytes:
        raise PDFValidationError("No PDF data provided.")
        
    # Check magic bytes
    if not pdf_bytes.startswith(b"%PDF-"):
        raise PDFValidationError("Uploaded file is not a valid PDF (missing '%PDF-' header).")
        
    # Check size (<= 25 MB)
    max_size = 25 * 1024 * 1024
    if len(pdf_bytes) > max_size:
        raise PDFValidationError(f"PDF exceeds size limit of 25 MB (got {len(pdf_bytes) / (1024*1024):.1f} MB).")
        
    # Check page count and extractable text
    page_count = 0
    extracted_text = ""
    try:
        import pymupdf
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            page_count = len(doc)
            if page_count > 60:
                raise PDFValidationError(f"PDF exceeds maximum page limit of 60 pages (got {page_count} pages).")
            for page in doc:
                txt = page.get_text() or ""
                extracted_text += txt + "\n"
    except PDFValidationError:
        raise
    except Exception:
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(reader.pages)
            if page_count > 60:
                raise PDFValidationError(f"PDF exceeds maximum page limit of 60 pages (got {page_count} pages).")
            for page in reader.pages:
                txt = page.extract_text() or ""
                extracted_text += txt + "\n"
        except PDFValidationError:
            raise
        except Exception as e:
            raise PDFValidationError(f"Failed to parse PDF document: {e}")
            
    # Check for extractable text (non-whitespace characters >= 50)
    clean_text = "".join(extracted_text.split())
    if len(clean_text) < 50:
        raise PDFValidationError(
            "PDF contains no extractable text. Scanned or image-only documents are not supported; "
            "please upload a PDF with digital text."
        )
        
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    return {
        "sha256": sha256_hash,
        "page_count": page_count,
        "text_length": len(clean_text)
    }

def verify_quote(full_text: str, quote: str) -> bool:
    """Verifies that normalized quote is a substring of paper text."""
    if not quote or not full_text:
        return False
    norm_full = " ".join(full_text.split())
    norm_quote = " ".join(quote.split())
    return norm_quote in norm_full


