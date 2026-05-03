"""
Text Generation — ArthLLM inference.
Used for sanity checks during training and after fine-tuning.
"""

import torch
from tokenizers import Tokenizer
from Model.config import ArthLLMConfig
from Model.model import ArthLLM
from pathlib import Path


def load_model(ckpt_path: str, cfg: ArthLLMConfig = None) -> ArthLLM:
    cfg   = cfg or ArthLLMConfig()
    model = ArthLLM(cfg)
    ckpt  = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model


@torch.no_grad()
def generate(
    model: ArthLLM,
    tokenizer: Tokenizer,
    prompt: str,
    max_new_tokens: int = 200,
    temperature: float = 0.7,
    top_p: float = 0.9,
    device: str = "cpu",
) -> str:
    model = model.to(device)
    ids   = tokenizer.encode(prompt).ids
    x     = torch.tensor([ids], dtype=torch.long, device=device)

    for _ in range(max_new_tokens):
        with torch.autocast(device_type=device, dtype=torch.bfloat16):
            logits = model(x)[:, -1, :]        # last token logits

        logits = logits / temperature

        # Top-p (nucleus) sampling
        probs  = torch.softmax(logits, dim=-1)
        sorted_probs, sorted_idx = torch.sort(probs, descending=True)
        cumsum = torch.cumsum(sorted_probs, dim=-1)
        mask   = (cumsum - sorted_probs) > top_p
        sorted_probs[mask] = 0
        sorted_probs /= sorted_probs.sum()
        next_tok = sorted_idx[0, torch.multinomial(sorted_probs[0], 1)]

        x = torch.cat([x, next_tok.view(1, 1)], dim=1)

        if next_tok.item() == tokenizer.token_to_id("<eos>"):
            break

    return tokenizer.decode(x[0].tolist())


if __name__ == "__main__":
    CKPT = "checkpoints/arthlm_step_001000.pt"
    TOK  = "tokenizer_32k_indian/tokenizer.json"

    if Path(CKPT).exists() and Path(TOK).exists():
        model     = load_model(CKPT)
        tokenizer = Tokenizer.from_file(TOK)
        out = generate(model, tokenizer, "RBI raised the repo rate by")
        print(out)
    else:
        print("No checkpoint found yet. Train first.")
