"""
ArthLLM Attention — Grouped Query Attention (GQA)

GQA uses n_kv_heads=8 shared K/V heads for n_heads=20 query heads.
This gives 2× VRAM reduction on Kaggle T4 vs standard MHA.
Flash Attention 2 is used when available.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from Model.config import ArthLLMConfig
from Model.rope import get_rope

try:
    from flash_attn import flash_attn_func
    FLASH_AVAILABLE = True
except ImportError:
    FLASH_AVAILABLE = False


class ArthAttention(nn.Module):

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__()
        self.n_heads    = cfg.n_heads
        self.n_kv_heads = cfg.n_kv_heads
        self.head_dim   = cfg.head_dim
        self.d_model    = cfg.d_model
        self.n_rep      = self.n_heads // self.n_kv_heads  # how many Q heads share each KV

        # Projections
        self.q_proj  = nn.Linear(cfg.d_model, cfg.n_heads    * cfg.head_dim, bias=cfg.bias)
        self.k_proj  = nn.Linear(cfg.d_model, cfg.n_kv_heads * cfg.head_dim, bias=cfg.bias)
        self.v_proj  = nn.Linear(cfg.d_model, cfg.n_kv_heads * cfg.head_dim, bias=cfg.bias)
        self.o_proj  = nn.Linear(cfg.n_heads * cfg.head_dim, cfg.d_model,    bias=cfg.bias)

        self.rope = get_rope(cfg)

    def _expand_kv(self, x: torch.Tensor) -> torch.Tensor:
        """Repeat K/V heads to match Q head count (GQA expansion)."""
        # x: [B, n_kv_heads, S, head_dim] → [B, n_heads, S, head_dim]
        B, n_kv, S, D = x.shape
        x = x[:, :, None, :, :].expand(B, n_kv, self.n_rep, S, D)
        return x.reshape(B, n_kv * self.n_rep, S, D)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        B, S, _ = x.shape

        q = self.q_proj(x).view(B, S, self.n_heads,    self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, S, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, S, self.n_kv_heads, self.head_dim).transpose(1, 2)

        # Apply RoPE to Q and K
        q, k = self.rope(q, k)

        # Expand K/V for GQA
        k = self._expand_kv(k)
        v = self._expand_kv(v)

        if FLASH_AVAILABLE and mask is None:
            # Flash Attention 2 path (fastest, requires no mask)
            q_ = q.transpose(1, 2)   # [B, S, H, D]
            k_ = k.transpose(1, 2)
            v_ = v.transpose(1, 2)
            out = flash_attn_func(q_, k_, v_, causal=True)
            out = out.reshape(B, S, -1)
        else:
            # Standard scaled dot-product attention
            scale = self.head_dim ** -0.5
            scores = torch.matmul(q, k.transpose(-2, -1)) * scale   # [B, H, S, S]
            if mask is not None:
                scores = scores + mask
            attn = F.softmax(scores, dim=-1)
            out  = torch.matmul(attn, v)                             # [B, H, S, D]
            out  = out.transpose(1, 2).contiguous().view(B, S, -1)

        return self.o_proj(out)
