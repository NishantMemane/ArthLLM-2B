"""
SwiGLU Feed-Forward Network.

SwiGLU is used in LLaMA 3, Mistral, Gemma — best activation for language tasks.
Architecture: gate(x) * swish(up(x)), projected back via down.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from Model.config import ArthLLMConfig


class SwiGLUFFN(nn.Module):

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__()
        self.gate = nn.Linear(cfg.d_model, cfg.ffn_dim, bias=cfg.bias)
        self.up   = nn.Linear(cfg.d_model, cfg.ffn_dim, bias=cfg.bias)
        self.down = nn.Linear(cfg.ffn_dim, cfg.d_model, bias=cfg.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))
