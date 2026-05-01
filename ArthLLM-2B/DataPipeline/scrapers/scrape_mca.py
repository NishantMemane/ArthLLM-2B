"""
MCA Scraper — Ministry of Corporate Affairs
NCLT Orders, NCLAT Orders, IBBI Insolvency, Companies Act.
Target: ~1B tokens
"""

import time, requests, logging
from pathlib import Path
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
OUT = Path("data/raw/indian/mca_filings.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

URLS = {
    "companies_act": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks.html",
    "nclt_orders":   "https://nclt.gov.in/order-judgement",
    "nclat_orders":  "https://nclat.gov.in/?page_id=258",
    "ibbi_orders":   "https://ibbi.gov.in/orders",
}


def run():
    with OUT.open("w", encoding="utf-8") as f:
        for name, url in URLS.items():
            try:
                r = requests.get(url, timeout=30,
                    headers={"User-Agent": "ArthLLM Research"})
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script","style"]): tag.decompose()
                text = soup.get_text("\n", strip=True)
                f.write(f"\n\n=== MCA {name.upper()} ===\n\n{text}")
                log.info(f"  {name}: {len(text):,} chars")
            except Exception as e:
                log.error(f"  {name} failed: {e}")
            time.sleep(2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
