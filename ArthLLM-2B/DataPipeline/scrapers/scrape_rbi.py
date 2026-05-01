"""
RBI Scraper — Reserve Bank of India Publications
Target: ~3B tokens from 30+ years of RBI documents.
Scrapes: circulars, master directions, monetary policy, speeches, working papers.
"""

import time
import requests
import logging
from pathlib import Path
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
OUT = Path("data/raw/indian/rbi_publications.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "ArthLLM Research Bot — Indian Finance LLM (contact: your@email.com)"
}

RBI_URLS = {
    "circulars":    "https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx",
    "publications": "https://rbi.org.in/Scripts/Publications.aspx",
    "speeches":     "https://rbi.org.in/Scripts/BS_SpeechesView.aspx",
    "mpc":          "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
    "master_dir":   "https://rbi.org.in/Scripts/BS_ViewMasterDirections.aspx",
    "working_papers":"https://rbi.org.in/Scripts/PublicationsView.aspx?Id=21176",
}

DELAY_SECONDS = 3   # be polite — RBI servers are government infra


def scrape_page(url: str) -> str:
    """Fetch a single URL and return clean text."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove nav, scripts, styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        log.error(f"Failed {url}: {e}")
        return ""


def run():
    with OUT.open("w", encoding="utf-8") as f:
        for name, url in RBI_URLS.items():
            log.info(f"Scraping RBI {name}...")
            text = scrape_page(url)
            if text:
                f.write(f"\n\n=== RBI {name.upper()} ===\n\n")
                f.write(text)
                log.info(f"  {len(text):,} chars")
            time.sleep(DELAY_SECONDS)
    log.info(f"RBI scrape done → {OUT}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
