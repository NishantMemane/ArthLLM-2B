"""
Perplexity Evaluation — measures model quality on held-out Indian finance text.
Lower perplexity = better. Target: <20 on Indian finance test set.
"""

import math
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer
from Model.config import ArthLLMConfig
from Model.model import ArthLLM


@torch.no_grad()
def compute_perplexity(model: ArthLLM, tokenizer: Tokenizer,
                       text: str, seq_len: int = 512,
                       device: str = "cpu") -> float:
    model.eval().to(device)
    ids    = tokenizer.encode(text).ids
    ids    = torch.tensor(ids, dtype=torch.long).to(device)
    losses = []

    for i in range(0, len(ids) - seq_len, seq_len):
        chunk = ids[i : i + seq_len + 1]
        x, y  = chunk[:-1].unsqueeze(0), chunk[1:].unsqueeze(0)
        logits = model(x)
        loss   = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1))
        losses.append(loss.item())

    return math.exp(sum(losses) / len(losses))


if __name__ == "__main__":
    test_text = (
        "The Reserve Bank of India raised the repo rate by 25 basis points "
        "to 6.75%, citing persistent core inflation above the 4% target. "
        "The Monetary Policy Committee voted 5-1 in favour of the hike."
    )
    print("Perplexity eval ready. Load model and run compute_perplexity().")
