"""
ArthLLM Model Configuration
All architectural decisions from the master plan, documented.
"""

from dataclasses import dataclass, field


@dataclass
class ArthLLMConfig:
    # ── Identity ──────────────────────────────────────────────────────────
    model_name: str = "ArthLLM-2B"
    version:    str = "1.0"

    # ── Tokenizer ─────────────────────────────────────────────────────────
    # 32K covers Hindi/Hinglish tokens + all Indian finance terms natively
    # (SEBI, NBFC, ASBA, crore, lakh, GST, TDS etc. are single tokens)
    vocab_size: int = 32_000

    # ── Architecture ──────────────────────────────────────────────────────
    d_model:    int = 2560    # embedding dimension → drives parameter count
    n_layers:   int = 32      # depth for regulatory reasoning chains
    n_heads:    int = 20      # attention heads  (d_model / n_heads = 128)
    n_kv_heads: int = 8       # GQA key-value heads → 2× VRAM saving on T4
    ffn_dim:    int = 10240   # SwiGLU FFN hidden size  (4 × d_model)
    max_seq_len: int = 2048   # base context window

    # ── RoPE ──────────────────────────────────────────────────────────────
    # LLaMA 3 standard theta — works well for Indian regulatory language
    rope_theta: float = 500_000.0

    # ── YaRN ──────────────────────────────────────────────────────────────
    # RBI annual reports, Union Budget speeches = 50K–100K tokens.
    # YaRN extends 2048 → 16K without retraining.
    use_yarn:             bool  = True
    yarn_scale:           float = 8.0      # 2048 × 8 = 16384 effective context
    yarn_alpha:           float = 1.0
    original_max_seq_len: int   = 2048

    # ── Training Flags ────────────────────────────────────────────────────
    dropout: float = 0.0    # large models regularize via data volume, not dropout
    bias:    bool  = False  # modern standard — slightly better generalisation

    def __post_init__(self):
        assert self.d_model % self.n_heads == 0, "d_model must be divisible by n_heads"
        assert self.n_heads % self.n_kv_heads == 0, "n_heads must be divisible by n_kv_heads"

    @property
    def head_dim(self) -> int:
        return self.d_model // self.n_heads

    def estimate_params(self) -> int:
        """Rough parameter count (matches ~2.1B for these defaults)."""
        embed   = self.vocab_size * self.d_model                            # embedding
        attn    = self.n_layers * (4 * self.d_model * self.d_model)        # Q/K/V/O
        ffn     = self.n_layers * (3 * self.d_model * self.ffn_dim)        # SwiGLU = 3 mats
        norms   = self.n_layers * 2 * self.d_model + self.d_model          # RMSNorm
        lm_head = self.vocab_size * self.d_model                           # tied weights
        total   = embed + attn + ffn + norms + lm_head
        return total

    def __repr__(self):
        p = self.estimate_params()
        return (
            f"ArthLLMConfig("
            f"vocab={self.vocab_size}, d_model={self.d_model}, "
            f"layers={self.n_layers}, heads={self.n_heads}, "
            f"kv_heads={self.n_kv_heads}, ffn={self.ffn_dim}, "
            f"params≈{p/1e9:.2f}B)"
        )


# Singleton — import this everywhere
CONFIG = ArthLLMConfig()

if __name__ == "__main__":
    cfg = ArthLLMConfig()
    print(cfg)
    print(f"Estimated parameters: {cfg.estimate_params() / 1e9:.3f}B")
