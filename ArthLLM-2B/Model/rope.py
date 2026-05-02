"""
Rotary Position Embedding (RoPE) + YaRN extension.

RoPE  : Standard implementation (LLaMA 3 / Mistral style)
YaRN  : Extends context from 2048 → 16K for long Indian regulatory docs
        (RBI annual reports, Union Budget, SEBI consultation papers)
"""

import math
import torch
import torch.nn as nn
from Model.config import ArthLLMConfig


class RotaryEmbedding(nn.Module):
    """Standard RoPE — position-dependent rotation of Q and K vectors."""

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__()
        self.head_dim  = cfg.head_dim
        self.max_seq   = cfg.max_seq_len
        self.theta     = cfg.rope_theta

        # Precompute inverse frequencies  [head_dim/2]
        inv_freq = 1.0 / (
            self.theta ** (torch.arange(0, self.head_dim, 2).float() / self.head_dim)
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def _compute_cos_sin(self, seq_len: int, device: torch.device):
        t        = torch.arange(seq_len, device=device).float()
        freqs    = torch.outer(t, self.inv_freq)        # [seq, head_dim/2]
        emb      = torch.cat([freqs, freqs], dim=-1)    # [seq, head_dim]
        return emb.cos(), emb.sin()

    def forward(self, q: torch.Tensor, k: torch.Tensor):
        """q, k: [batch, heads, seq, head_dim]"""
        seq_len = q.shape[2]
        cos, sin = self._compute_cos_sin(seq_len, q.device)
        cos = cos[None, None, :, :]   # broadcast over batch, heads
        sin = sin[None, None, :, :]
        return apply_rotary(q, cos, sin), apply_rotary(k, cos, sin)


class YaRNRotaryEmbedding(RotaryEmbedding):
    """
    YaRN (Yet another RoPE extensioN) — extends context without retraining.
    Scales rope_theta by yarn_scale so that position indices up to
    original_max * yarn_scale become reachable.

    Critical for ArthLLM: RBI annual reports can be 50K+ tokens.
    """

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__(cfg)
        self.yarn_scale  = cfg.yarn_scale
        self.yarn_alpha  = cfg.yarn_alpha
        self.original_max = cfg.original_max_seq_len

        # Rescale inv_freq for extended context
        scale    = self.yarn_scale ** (self.head_dim / (self.head_dim - 2))
        inv_freq = 1.0 / (
            (cfg.rope_theta * scale) **
            (torch.arange(0, self.head_dim, 2).float() / self.head_dim)
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)


def apply_rotary(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Apply rotary embeddings to input tensor x."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    rotated = torch.cat([-x2, x1], dim=-1)
    return (x * cos) + (rotated * sin)


def get_rope(cfg: ArthLLMConfig) -> RotaryEmbedding:
    """Factory: returns YaRN-extended RoPE if configured, else standard RoPE."""
    if cfg.use_yarn:
        return YaRNRotaryEmbedding(cfg)
    return RotaryEmbedding(cfg)
