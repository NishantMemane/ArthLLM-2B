"""
SEC EDGAR Downloader — Global Finance Data
The edgar-corpus HuggingFace dataset covers this (~3B tokens).
This script is the fallback: direct EDGAR API access for specific filings.
No API key needed — just set User-Agent header.
"""

import requests, logging
from pathlib import Path

log = logging.getLogger(__name__)
OUT = Path("data/raw/global/sec_edgar.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

# EDGAR requires a valid User-Agent identifying your app
HEADERS = {"User-Agent": "ArthLLM Research your@email.com"}
BASE    = "https://data.sec.gov"


def get_company_filings(cik: str, form_type: str = "10-K") -> list[dict]:
    url = f"{BASE}/submissions/CIK{cik.zfill(10)}.json"
    r   = requests.get(url, headers=HEADERS)
    data = r.json()
    filings = data.get("filings", {}).get("recent", {})
    forms   = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    return [
        {"accession": acc, "form": form}
        for form, acc in zip(forms, accessions)
        if form == form_type
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("EDGAR bulk download — prefer HuggingFace eloukas/edgar-corpus instead.")
    log.info("Use this script only for specific company filings not in the HF dataset.")
