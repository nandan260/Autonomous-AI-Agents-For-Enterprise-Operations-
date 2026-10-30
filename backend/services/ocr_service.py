import os
from pathlib import Path
import pymupdf as fitz


def extract_text(file_path: str) -> str:
    """Extract text from PDF or text file using PyMuPDF."""
    if not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in [".txt", ".md", ".csv", ".json"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def _extract_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"[OCR Error] Failed to read {pdf_path}: {e}")
    return text


def find_document(folder: str, doc_name: str) -> str | None:
    """Find document file in uploads folder with matching base name."""
    if not os.path.isdir(folder):
        return None
    for ext in [".pdf", ".png", ".jpg", ".jpeg", ".txt"]:
        path = os.path.join(folder, doc_name + ext)
        if os.path.exists(path):
            return path
    # Also check case-insensitive match
    for fname in os.listdir(folder):
        base, _ = os.path.splitext(fname)
        if base.lower() == doc_name.lower():
            return os.path.join(folder, fname)
    return None
