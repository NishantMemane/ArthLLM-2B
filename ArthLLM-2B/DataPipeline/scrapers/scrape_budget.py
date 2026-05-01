"""
Ministry of Finance — Union Budget & Economic Survey Scraper
Target: ~500M tokens  (budget speeches 1947–2026, economic surveys, finance bills)
URL: https://www.indiabudget.gov.in/
"""

import time
import requests
import logging
from pathlib import Path
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
OUT = Path("data/raw/indian/union_budget.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "ArthLLM Research (your@email.com)"}
DELAY   = 2

BUDGET_URLS = {
    "speeches":      "https://www.indiabudget.gov.in/budgetspeech.php",
    "economic_survey":"https://www.indiabudget.gov.in/economicsurvey/",
    "finance_bill":  "https://www.indiabudget.gov.in/finance_bill.php",
    "at_a_glance":   "https://www.indiabudget.gov.in/budget_at_glance.php",
}


def run():
    with OUT.open("w", encoding="utf-8") as f:
        for name, url in BUDGET_URLS.items():
            log.info(f"Fetching Budget {name}...")
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style"]): tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                f.write(f"\n\n=== BUDGET {name.upper()} ===\n\n{text}")
                log.info(f"  {len(text):,} chars")
            except Exception as e:
                log.error(f"  {e}")
            time.sleep(DELAY)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
