"""
Shard Data Loader — streams tokenized binary shards for training.
Memory-efficient: loads one shard at a time (100M tokens = ~200MB).
"""

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import logging

log = logging.getLogger(__name__)


class ShardDataset(Dataset):
    """Dataset that reads pre-tokenized binary shards."""

    def __init__(self, shard_dir: str, seq_len: int = 2048):
        self.shards  = sorted(Path(shard_dir).glob("*.bin"))
        self.seq_len = seq_len
        self.tokens  = None
        self._load_shard(0)
        log.info(f"Found {len(self.shards)} shards in {shard_dir}")

    def _load_shard(self, idx: int):
        self.tokens = np.fromfile(self.shards[idx], dtype=np.uint16).astype(np.int64)
        log.info(f"Loaded shard {idx}: {len(self.tokens):,} tokens")

    def __len__(self) -> int:
        return len(self.tokens) // (self.seq_len + 1)

    def __getitem__(self, idx: int):
        start = idx * (self.seq_len + 1)
        chunk = self.tokens[start : start + self.seq_len + 1]
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:],  dtype=torch.long)
        return x, y


def get_dataloader(shard_dir: str, seq_len: int, batch_size: int,
                   num_workers: int = 2) -> DataLoader:
    ds = ShardDataset(shard_dir, seq_len)
    return DataLoader(ds, batch_size=batch_size, shuffle=True,
                      num_workers=num_workers, pin_memory=True)
