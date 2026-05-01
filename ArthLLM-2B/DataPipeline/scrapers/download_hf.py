"""
Step 1 — HuggingFace Dataset Downloader
Downloads all 15 datasets from the data collection guide.
Run from project root: python DataPipeline/scrapers/download_hf.py
"""

from datasets import load_dataset
from pathlib import Path
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW_INDIAN = Path("data/raw/indian")
RAW_GLOBAL = Path("data/raw/global")
RAW_INDIAN.mkdir(parents=True, exist_ok=True)
RAW_GLOBAL.mkdir(parents=True, exist_ok=True)

# (hf_dataset_id, config_or_None, output_path, notes)
DATASETS = [
    # ── Indian ──────────────────────────────────────────────────────────────
    ("ranvsingn/indian-financial-news",       None, RAW_INDIAN / "indian_financial_news.csv",    "~200M tokens"),
    ("sohan-ai/indian-stock-market-qa",       None, RAW_INDIAN / "indian_stock_qa.csv",          "~50M tokens"),
    ("ai4bharat/sangraha",                    "hi", RAW_INDIAN / "sangraha_hindi.csv",           "~2B tokens — large"),
    ("ai4bharat/IndicCorp",                   "hi", RAW_INDIAN / "indicorp_hindi.csv",           "~1B tokens — large"),
    ("iitk-researchers/indian-legal-dataset", None, RAW_INDIAN / "indian_legal.csv",             "~500M tokens"),
    ("Karthik-shanmugam/indian_news_nlp",     None, RAW_INDIAN / "indian_news_nlp.csv",          "~100M tokens"),
    ("ashishkgpian/hindi_text_corpus",        None, RAW_INDIAN / "hindi_text.csv",              "~300M tokens"),
    # ── Global ──────────────────────────────────────────────────────────────
    ("eloukas/edgar-corpus",                  None, RAW_GLOBAL / "edgar_corpus.csv",            "~3B tokens — very large"),
    ("sujet-ai/Sujet-Finance-Instruct-177k",  None, RAW_GLOBAL / "finance_instruct.csv",        "~100M tokens"),
    ("gbharti/finance-alpaca",                None, RAW_GLOBAL / "finance_alpaca.csv",          "~50M tokens"),
    ("FinGPT/fingpt-sentiment-train",         None, RAW_GLOBAL / "fingpt_sentiment.csv",        "~50M tokens"),
    ("zeroshot/twitter-financial-news",       None, RAW_GLOBAL / "twitter_finance.csv",         "~30M tokens"),
    ("nickmuchi/financial-classification",    None, RAW_GLOBAL / "financial_classification.csv","~20M tokens"),
    ("kiddothe2b/financial_reports",          None, RAW_GLOBAL / "financial_reports.csv",       "~500M tokens"),
    ("ChanceFocus/flare-finqa",               None, RAW_GLOBAL / "flare_finqa.csv",             "~30M tokens"),
]


def download_all(skip_existing: bool = True):
    total = len(DATASETS)
    for i, (name, config, out_path, notes) in enumerate(DATASETS, 1):
        log.info(f"[{i}/{total}] {name}  ({notes})")

        if skip_existing and out_path.exists():
            log.info(f"  → already exists, skipping. Delete to re-download.")
            continue

        try:
            ds = (
                load_dataset(name, config, split="train")
                if config
                else load_dataset(name, split="train")
            )
            log.info(f"  → {len(ds):,} rows loaded")
            ds.to_csv(str(out_path), index=False)
            log.info(f"  → saved to {out_path}")

        except Exception as e:
            log.error(f"  ✗ FAILED: {e}")
            log.error(f"    Try: ds = load_dataset('{name}', split=None); print(ds)")

    log.info("Done. Check data/raw/ for your files.")


if __name__ == "__main__":
    download_all()
