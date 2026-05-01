"""
MinHash Deduplication — removes exact and near-duplicate documents.
Uses datasketch for scalable MinHash LSH.
Target: reduce ~40B raw → ~40B deduplicated (finance text has less duplication than web).
"""

import logging
from datasketch import MinHash, MinHashLSH
from pathlib import Path

log = logging.getLogger(__name__)


def shingle(text: str, k: int = 5) -> set[str]:
    """k-character shingles for MinHash."""
    return {text[i:i+k] for i in range(len(text) - k + 1)}


def build_minhash(text: str, num_perm: int = 128) -> MinHash:
    m = MinHash(num_perm=num_perm)
    for s in shingle(text):
        m.update(s.encode("utf-8"))
    return m


def deduplicate_texts(texts: list[str], threshold: float = 0.85) -> list[str]:
    """
    Remove near-duplicates using Jaccard similarity.
    threshold=0.85 means 85% similar documents are considered duplicates.
    """
    lsh    = MinHashLSH(threshold=threshold, num_perm=128)
    unique = []

    for i, text in enumerate(texts):
        m = build_minhash(text)
        if not lsh.query(m):
            lsh.insert(f"doc_{i}", m)
            unique.append(text)

    removed = len(texts) - len(unique)
    log.info(f"Dedup: {len(texts)} → {len(unique)} docs (removed {removed} duplicates)")
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = ["RBI raises repo rate by 25bps.", "RBI raises repo rate by 25 bps.", "Completely different text."]
    result = deduplicate_texts(sample, threshold=0.7)
    print(f"Unique: {result}")
