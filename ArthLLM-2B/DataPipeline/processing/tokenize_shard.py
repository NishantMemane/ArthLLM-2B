"""
Tokenizer Sharding — converts cleaned text into binary token shards.
Each shard = 100M tokens stored as uint16 numpy array.
~400 shards total for 40B tokens.
Shards are saved to data/tokenized_shards/ and synced to Google Drive.
"""

import numpy as np
import logging
from pathlib import Path
from tokenizers import Tokenizer

log       = logging.getLogger(__name__)
SHARD_DIR = Path("data/tokenized_shards")
SHARD_DIR.mkdir(parents=True, exist_ok=True)

SHARD_SIZE  = 100_000_000   # 100M tokens per shard
TOKENIZER_PATH = "tokenizer_32k_indian/tokenizer.json"


def load_tokenizer() -> Tokenizer:
    return Tokenizer.from_file(TOKENIZER_PATH)


def tokenize_file(text_file: Path, tokenizer: Tokenizer, shard_prefix: str):
    """Tokenize a cleaned text file into binary shards."""
    log.info(f"Tokenizing {text_file}...")
    tokens  = []
    shard_n = 0

    with text_file.open(encoding="utf-8") as f:
        for line in f:
            encoded = tokenizer.encode(line.strip())
            tokens.extend(encoded.ids)

            while len(tokens) >= SHARD_SIZE:
                shard   = np.array(tokens[:SHARD_SIZE], dtype=np.uint16)
                out     = SHARD_DIR / f"{shard_prefix}_{shard_n:04d}.bin"
                shard.tofile(out)
                log.info(f"  Saved shard {shard_n}: {out}")
                tokens  = tokens[SHARD_SIZE:]
                shard_n += 1

    # Save remainder
    if tokens:
        shard = np.array(tokens, dtype=np.uint16)
        out   = SHARD_DIR / f"{shard_prefix}_{shard_n:04d}.bin"
        shard.tofile(out)
        log.info(f"  Saved final shard {shard_n}: {out}  ({len(tokens):,} tokens)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("Run after training tokenizer. Example:")
    log.info("  tokenize_file(Path('data/cleaned/rbi.txt'), load_tokenizer(), 'rbi')")
