"""
Quality Filter — removes low-quality text before tokenization.
Applies the data quality checklist from the master plan.
"""

import re
import logging
from langdetect import detect, LangDetectException

log = logging.getLogger(__name__)

ALLOWED_LANGS = {"en", "hi"}   # English and Hindi (Hinglish detected as one or both)
MIN_CHARS     = 100
MAX_REPEAT_RATIO = 0.3         # reject if >30% chars are the same character


def is_finance_relevant(text: str) -> bool:
    """Simple keyword check — at least one finance keyword must be present."""
    keywords = [
        "sebi", "rbi", "nse", "bse", "sensex", "nifty", "crore", "lakh",
        "rupee", "equity", "debt", "fund", "interest", "rate", "bank",
        "loan", "insurance", "tax", "gst", "tds", "ipo", "mutual fund",
        "quarterly", "revenue", "profit", "earnings", "dividend",
        "फंड", "बैंक", "ब्याज", "शेयर", "रुपये",
    ]
    lower = text.lower()
    return any(k in lower for k in keywords)


def is_valid_language(text: str) -> bool:
    try:
        lang = detect(text)
        return lang in ALLOWED_LANGS
    except LangDetectException:
        return False


def has_repetition(text: str) -> bool:
    if not text:
        return False
    most_common_char = max(set(text), key=text.count)
    return (text.count(most_common_char) / len(text)) > MAX_REPEAT_RATIO


def passes_quality(text: str, check_finance: bool = True) -> bool:
    if len(text.strip()) < MIN_CHARS:
        return False
    if has_repetition(text):
        return False
    if check_finance and not is_finance_relevant(text):
        return False
    return True


def filter_texts(texts: list[str], check_finance: bool = True) -> list[str]:
    kept = [t for t in texts if passes_quality(t, check_finance)]
    log.info(f"Quality filter: {len(texts)} → {len(kept)} texts")
    return kept


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    samples = [
        "RBI raised repo rate by 25 bps citing inflation concerns above 6%.",  # keep
        "aaaaaaaaaaaaaaaaaaaaaaaaaaa",                                          # reject — repetition
        "Hello how are you doing today",                                        # reject — no finance
    ]
    for s in filter_texts(samples):
        print(f"KEPT: {s[:60]}")
