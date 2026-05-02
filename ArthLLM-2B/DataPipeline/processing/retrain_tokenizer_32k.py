"""
Retrain Tokenizer — Indian-Aware 32K BPE Tokenizer
Trained on a corpus sample that includes Hindi/Hinglish + finance terms.
This ensures Indian terms (SEBI, NBFC, crore, lakh, ASBA, etc.) are single tokens.
"""

import logging
from pathlib import Path
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

log     = logging.getLogger(__name__)
OUT_DIR = Path("tokenizer_32k_indian")
OUT_DIR.mkdir(exist_ok=True)

VOCAB_SIZE = 32_000
SPECIAL_TOKENS = ["<pad>", "<unk>", "<bos>", "<eos>"]

# Indian finance special tokens — these are guaranteed single tokens
INDIAN_FINANCE_TOKENS = [
    "SEBI", "RBI", "NSE", "BSE", "NIFTY", "SENSEX",
    "NBFC", "HFC", "MFI", "NCLT", "NCLAT", "IBBI",
    "ASBA", "IPO", "FPO", "SIP", "ELSS", "ULIP", "NPS", "PPF",
    "GST", "TDS", "LTCG", "STCG", "STT",
    "crore", "lakh", "arab",
    "Nifty50", "BSE500", "Sensex30",
    "FII", "DII", "QIB", "HNI",
]


def train(corpus_files: list[Path]):
    tokenizer = Tokenizer(models.BPE(unk_token="<unk>"))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()

    trainer = trainers.BpeTrainer(
        vocab_size=VOCAB_SIZE,
        special_tokens=SPECIAL_TOKENS + INDIAN_FINANCE_TOKENS,
        min_frequency=2,
        show_progress=True,
    )

    tokenizer.train([str(f) for f in corpus_files], trainer)
    tokenizer.save(str(OUT_DIR / "tokenizer.json"))
    log.info(f"Tokenizer saved → {OUT_DIR}/tokenizer.json")

    # Verify Indian tokens are preserved
    test = "SEBI circular about NBFC regulations in crore rupees"
    enc  = tokenizer.encode(test)
    log.info(f"Test: '{test}' → {enc.tokens}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    corpus = list(Path("data/cleaned").glob("*.txt"))
    if corpus:
        train(corpus)
    else:
        log.warning("No cleaned text files found in data/cleaned/. Run cleaning step first.")
