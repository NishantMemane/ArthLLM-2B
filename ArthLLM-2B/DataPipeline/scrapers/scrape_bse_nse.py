"""
BSE / NSE Scraper — Corporate Filings & Announcements
Target: ~4B tokens combined.
Uses Selenium because BSE/NSE have JavaScript-rendered content.

WARNING: Both sites have anti-scraping measures.
Strategy: Selenium + 2-5s random delays + User-Agent rotation + off-peak hours.
"""

import time
import random
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

log = logging.getLogger(__name__)
OUT_BSE = Path("data/raw/indian/bse_nse_filings.txt")
OUT_BSE.parent.mkdir(parents=True, exist_ok=True)

BSE_ANNOUNCEMENTS = "https://www.bseindia.com/corporates/ann.html"
NSE_FILINGS       = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0",
]


def get_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    return webdriver.Chrome(options=opts)


def scrape_bse_announcements(driver: webdriver.Chrome, pages: int = 10) -> str:
    """Scrape BSE corporate announcements — last N pages."""
    texts = []
    driver.get(BSE_ANNOUNCEMENTS)
    time.sleep(random.uniform(2, 5))
    # TODO: implement pagination + text extraction
    # Each page: find announcement table → extract rows → follow PDF links → extract
    texts.append(driver.page_source)
    return "\n".join(texts)


def run():
    log.info("Starting BSE/NSE scraper (Selenium)...")
    driver = get_driver()
    try:
        text = scrape_bse_announcements(driver)
        with OUT_BSE.open("w", encoding="utf-8") as f:
            f.write(text)
        log.info(f"Saved → {OUT_BSE}")
    finally:
        driver.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
