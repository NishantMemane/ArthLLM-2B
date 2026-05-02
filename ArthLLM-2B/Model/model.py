"""
ArthLLM — Full 2B Parameter Model.

Assembles all components: embedding → N transformer blocks → RMSNorm → LM head.
Weights between embedding and LM head are tied (saves ~80M params).
"""

import torch
import torch.nn as nn
from Model.config import ArthLLMConfig
from Model.block import TransformerBlock, RMSNorm


class ArthLLM(nn.Module):

    def __init__(self, cfg: ArthLLMConfig):
        super().__init__()
        self.cfg = cfg

        self.embed   = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks  = nn.ModuleList([TransformerBlock(cfg) for _ in range(cfg.n_layers)])
        self.norm    = RMSNorm(cfg.d_model)
        self.lm_head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)

        # Tie weights: embedding ↔ lm_head (standard practice, saves memory)
        self.lm_head.weight = self.embed.weight

        self._init_weights()

    def _init_weights(self):
        """Standard normal init — consistent with LLaMA 3."""
        nn.init.normal_(self.embed.weight, mean=0.0, std=0.02)
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, input_ids: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """
        Args:
            input_ids : [batch, seq_len]
            mask      : causal mask [batch, 1, seq, seq] or None
        Returns:
            logits    : [batch, seq_len, vocab_size]
        """
        x = self.embed(input_ids)          # [B, S, d_model]

        for block in self.blocks:
            x = block(x, mask)

        x = self.norm(x)
        return self.lm_head(x)             # [B, S, vocab_size]

    def count_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    cfg   = ArthLLMConfig()
    model = ArthLLM(cfg)
    total = model.count_params()
    print(f"ArthLLM total trainable parameters: {total / 1e9:.3f}B")

    # Smoke test
    ids = torch.randint(0, cfg.vocab_size, (2, 16))
    out = model(ids)
    print(f"Output shape: {out.shape}")   # expect [2, 16, 32000]
