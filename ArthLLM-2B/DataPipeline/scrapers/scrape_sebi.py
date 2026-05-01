"""
SEBI Scraper — Securities and Exchange Board of India
Target: ~1.5B tokens.
Scrapes: circulars, regulations, annual reports, enforcement orders.
"""

import time
import requests
import logging
from pathlib import Path
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
OUT = Path("data/raw/indian/sebi_circulars.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "ArthLLM Research Bot (your@email.com)"}
DELAY   = 3

SEBI_URLS = {
    "circulars":    "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1",
    "regulations":  "https://www.sebi.gov.in/legal/regulations.html",
    "consultation": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2",
    "annual_rpts":  "https://www.sebi.gov.in/reports-and-statistics/annual-reports.html",
    "enforcement":  "https://www.sebi.gov.in/enforcement/orders.html",
}


def scrape_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        log.error(f"Failed {url}: {e}")
        return ""


def run():
    with OUT.open("w", encoding="utf-8") as f:
        for name, url in SEBI_URLS.items():
            log.info(f"Scraping SEBI {name}...")
            text = scrape_page(url)
            if text:
                f.write(f"\n\n=== SEBI {name.upper()} ===\n\n")
                f.write(text)
            time.sleep(DELAY)
    log.info(f"SEBI scrape done → {OUT}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
