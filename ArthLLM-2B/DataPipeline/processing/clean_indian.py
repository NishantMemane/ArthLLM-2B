"""
Indian-Aware Text Cleaner
Handles all special cases for Indian financial text:
  - ₹ symbol normalisation
  - Lakh/Crore number format preservation
  - Devanagari Unicode normalisation
  - HTML artifact removal
  - Hinglish language preservation
"""

import re
import unicodedata
import logging

log = logging.getLogger(__name__)


def normalize_rupee(text: str) -> str:
    """Normalize all rupee representations to ₹."""
    patterns = [r"Rs\.\s*", r"Rs\s+", r"INR\s*", r"₹\s*"]
    for pat in patterns:
        text = re.sub(pat, "₹", text)
    return text


def preserve_indian_numbers(text: str) -> str:
    """
    Indian number system: 1,00,000 = 1 lakh, 1,00,00,000 = 1 crore.
    Do NOT convert to western format — keep as-is for model to learn.
    """
    return text  # preserve intentionally


def normalize_devanagari(text: str) -> str:
    """NFC normalisation for Hindi/Devanagari characters."""
    return unicodedata.normalize("NFC", text)


def remove_html_artifacts(text: str) -> str:
    """Remove leftover HTML tags and entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    return text


def clean_whitespace(text: str) -> str:
    """Collapse multiple whitespace but preserve paragraph breaks."""
    text = re.sub(r"[^\S\n]+", " ", text)    # spaces within line
    text = re.sub(r"\n{3,}", "\n\n", text)  # max 2 newlines
    return text.strip()


def clean(text: str) -> str:
    """Full Indian-aware cleaning pipeline."""
    text = remove_html_artifacts(text)
    text = normalize_devanagari(text)
    text = normalize_rupee(text)
    text = preserve_indian_numbers(text)
    text = clean_whitespace(text)
    return text


def clean_file(in_path, out_path):
    log.info(f"Cleaning {in_path}...")
    with open(in_path, encoding="utf-8") as f:
        raw = f.read()
    cleaned = clean(raw)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    log.info(f"  {len(raw):,} → {len(cleaned):,} chars → {out_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    if len(sys.argv) == 3:
        clean_file(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python clean_indian.py <input.txt> <output.txt>")
