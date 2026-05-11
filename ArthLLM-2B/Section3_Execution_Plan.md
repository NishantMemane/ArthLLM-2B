# Section 3 — Engineering & Execution Plan

This document outlines the step-by-step engineering plan to build the automated pipelines required to collect the ~6B tokens defined in the `Section3_Scraping_Plan.md`. 

## 🟢 Current Status: What We Have Built
We have successfully established the foundational architecture for interacting with the NSE APIs directly (bypassing the need for heavy browser automation using Playwright in most cases). 
- **Completed Scrapers (NSE):** `nse_dividend_scraper.py`, `nse_insider_trading_scraper.py`, `nse_bonus_split_scraper.py`, `nse_buyback_scraper.py`, `nse_demerger_scraper.py`.
- **Capabilities:** Direct JSON API parsing, robust session/cookie management, multi-threaded windowing (30-90 days), and resume-safe state tracking.
- **Data Extracted so far:** Structured metadata (Main CSVs) and corresponding announcement PDF URLs.

---

## 🚀 Phase 1: Expanding the Scraper Fleet (Data Acquisition)

**1. BSE Corporate Announcements Pipeline**
*   **Target:** `bseindia.com/corporates/ann.html`
*   **Strategy:** Reverse-engineer BSE's internal API payloads for fetching announcements to bypass HTML scraping.
*   **Modules to Build:** 
    *   `bse_annual_reports_scraper.py`
    *   `bse_financial_results_scraper.py`
    *   `bse_concall_transcripts_scraper.py`
    *   `bse_shareholding_scraper.py`

**2. SEBI & Regulatory Documents**
*   **Target:** DRHPs, Open Offers, QIPs
*   **Strategy:** Scrape `sebi.gov.in` filings portal using robust HTTP sessions. Since SEBI is static/paginated HTML, we will use `BeautifulSoup4`.
*   **Modules to Build:**
    *   `sebi_drhp_scraper.py`
    *   `sebi_open_offers_scraper.py`

**3. Credit Rating Agencies**
*   **Target:** CRISIL, ICRA, CARE
*   **Strategy:** Automated sitemap traversal or search API scraping to collect Rating Rationales.
*   **Modules to Build:** 
    *   `crisil_ratings_scraper.py`
    *   `icra_ratings_scraper.py`

---

## 🛠️ Phase 2: The PDF Download Engine

Currently, we have thousands of PDF URLs sitting in CSV files (e.g., `nse_bonus_split.csv`, `nse_buyback.csv`). We need a master PDF downloader.

**Architecture for `master_pdf_downloader.py`**:
*   **Input:** Reads any of the generated CSVs.
*   **Concurrency:** ThreadPoolExecutor (10-20 workers) to download PDFs concurrently.
*   **Storage:** Stores PDFs in a structured hierarchy: `raw_data/SECTION_3/category/symbol_date.pdf`.
*   **Resiliency:** 
    *   Checks if the file already exists locally (by size/hash).
    *   Retries on timeout/404s.
    *   For NSE links, automatically handles session cookies before requesting the standard `nsearchives.nseindia.com` URLs to prevent 403 Forbidden errors.

---

## 📝 Phase 3: Text Extraction & Parsing Engine

Financial PDFs are notorious for combining scanned images with digital text. We need a hybrid extraction pipeline to convert PDFs into clean, LLM-ready text/markdown.

**Architecture for `pdf_to_text_pipeline.py`**:
*   **Tier 1 (Digital PDFs):** Use `PyMuPDF` (`fitz`) or `pdfplumber` to extract native text rapidly.
*   **Tier 2 (Scanned/Image PDFs):** If Tier 1 yields < 100 characters per page, route the PDF to an OCR engine (`pytesseract` or `easyocr`).
*   **Table Extraction:** For purely tabular data (Shareholding Patterns, Financial Results), use `Camelot` or `pdfplumber`'s table extraction.
*   **Output:** Generates a `.txt` or `.md` file corresponding to each PDF, stripping out headers/footers to reduce token noise.

---

## 🔗 Phase 4: Integration & Data Unification

*   **Manifest Building:** Extend `build_manifests.py` to recursively crawl the extracted `.txt`/`.md` outputs and generate a `section3_manifest.csv` for the final ArthLLM training pipeline.
*   **Deduplication:** Many filings are mirrored across NSE and BSE. We will use a script to hash the text content and drop duplicate announcements/reports.
*   **Data Validation:** Ensure we hit the estimated ~6B token goal by running an aggressive token-counting pass over the extracted dataset.

---

## 🎯 Next Immediate Steps for Us
1. Build the **BSE Corporate Announcements Scraper** template (to replicate the success we had with NSE).
2. Build the **Master PDF Downloader** to start fetching the actual NSE PDFs we have indexed today.

*Tick off completed items here or in the master markdown documents as we proceed!*
