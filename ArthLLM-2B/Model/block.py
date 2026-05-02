"""
ArthLLM Transformer Block.

Pre-norm architecture (norm before attention/FFN, not after).
RMSNorm is faster than LayerNorm — used in LLaMA 3.
"""

import torch
import torch.nn as nn
from Model.config import ArthLLMConfig
from Model.attention import ArthAttention
from Model.ffn import SwiGLUFFN


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps   = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        norm = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return norm * self.weight


class TransformerBlock(nn.Module):

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__()
        self.attn_norm = RMSNorm(cfg.d_model)
        self.ffn_norm  = RMSNorm(cfg.d_model)
        self.attn      = ArthAttention(cfg)
        self.ffn       = SwiGLUFFN(cfg)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        # Pre-norm + residual for attention
        x = x + self.attn(self.attn_norm(x), mask)
        # Pre-norm + residual for FFN
        x = x + self.ffn(self.ffn_norm(x))
        return x
