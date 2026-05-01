"""
PDF Text Extractor
Processes all PDFs downloaded from RBI, SEBI, Budget, MCA.
Uses pdfplumber (better for tables) with PyPDF2 as fallback.
"""

import logging
from pathlib import Path
import pdfplumber
import PyPDF2

log = logging.getLogger(__name__)


def extract_text_pdfplumber(pdf_path: Path) -> str:
    """Primary extractor — handles tables well."""
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def extract_text_pypdf2(pdf_path: Path) -> str:
    """Fallback extractor."""
    text = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def extract(pdf_path: Path) -> str:
    """Try pdfplumber first, fall back to PyPDF2."""
    try:
        text = extract_text_pdfplumber(pdf_path)
        if text.strip():
            return text
    except Exception:
        pass
    return extract_text_pypdf2(pdf_path)


def process_directory(pdf_dir: Path, out_file: Path):
    pdfs = list(pdf_dir.glob("**/*.pdf"))
    log.info(f"Found {len(pdfs)} PDFs in {pdf_dir}")
    with out_file.open("w", encoding="utf-8") as f:
        for pdf in pdfs:
            log.info(f"  Extracting {pdf.name}...")
            text = extract(pdf)
            if text.strip():
                f.write(f"\n\n=== {pdf.name} ===\n\n{text}")
    log.info(f"Done → {out_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example: process_directory(Path("data/raw/indian/pdfs"), Path("data/raw/indian/rbi_publications.txt"))
