# Section 3 — Complete Scraping Plan (Phased)

> **Total Target: ~6B tokens** | 5 Phases | Priority-ordered by signal value

## 📋 Master Progress Checklist
**Phase 1: Earnings Call Transcripts**
- [1 ] 1A - BSE Announcements (Concalls)
- [ 1] 1B - Screener.in Concalls
- [1 ] 1C - Trendlyne Concalls
- [ 1] 1D - Tijori Finance Concalls
- [1 ] 1E - NSE Announcements (Concalls)
- [ 1] 1F - Company IR Websites
- [ 1] 1G - Moneycontrol (Archive 2015-2018)

**Phase 2: Annual Reports**
- [1 ] 2A - BSE Annual Reports (Nifty 500)
- [1 ] 2B - NSE Annual Reports (Nifty 500)
- [1 ] 2C - Pre-2020 Annual Reports (Moneycontrol/Screener)

**Phase 3: Quarterly Results + Shareholding**
- [1 ] 3A - Quarterly Results (All, 5 Years)
- [ 1] 3B - Shareholding Patterns (All, 5 Years)
- [ ] 3C - Investor Presentations

**Phase 4: IPO & Credit Ratings**
- [ ] 4A - DRHP / IPO Prospectuses
- [ ] 4B - Credit Rating Rationales (CRISIL, ICRA, CARE, India Ratings)
- [ ] 4C - Takeover / Open Offer Documents
- [ ] 4D - QIP / Rights Issue / Buyback Documents

**Phase 5: Board Announcements & Other**
- [1 ] 5A - Board Meeting Outcomes (Dividend, Bonus, Demerger, etc.)
- [1 ] 5B - Insider Trading Disclosures
- [ ] 5C - NSE Circulars + F&O Specs
- [1 ] 5D - Annual Reports (Remaining 4,500 companies)
- [ ] 5E - MCA21 ROC Filings (Unlisted)

**Bonus Phase**
- [ ] B1 - Proxy Advisory Reports
- [ ] B2 - Mutual Fund Portfolios (AMFI)
- [ ] B3 - Exchange Surveillance Notices
- [ ] B4 - NISM Certification Study Material
- [ ] B5 - NSE Academy / BSE Institute Material

---

## Phase 1 — HIGHEST SIGNAL FIRST: Earnings Call Transcripts (~2.5B tokens)

*Reason: Most unique, most differentiated. Nothing else in the corpus sounds like this.*

### 1A — BSE Announcements (Primary — Legally Mandated Uploads)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Filter | Category → **"Analysts/Institutional Investor Meet/Con. Call Updates"** |
| Date Range | 2019–2024 (5 years) |
| Format | PDF |
| Volume | 2,000+ companies, ~10,000–30,000 transcripts |
| Est. Tokens | ~1.5B (Nifty 500) + ~1.0B (extended universe) |

**Steps:**
1. Go to `bseindia.com/corporates/ann.html`
2. Set Category filter → "Analysts/Con. Call Updates"
3. Set date range: Jan 2019 – Dec 2024
4. Scrape all PDF links paginated
5. Download PDFs → extract text

---

### 1B — Screener.in Concalls

| Field | Detail |
|-------|--------|
| URL | `screener.in/concalls/` |
| Access | Free, paginated |
| Format | PDF |
| Coverage | Nifty 500, curated, 3–5 years back |

**Steps:**
1. Browse `screener.in/concalls/` (sorted by date)
2. For each company: `screener.in` → search company → Documents → Concall Transcripts
3. Use Screener's free API for bulk access
4. Download PDFs → extract text

---

### 1C — Trendlyne Concalls

| Field | Detail |
|-------|--------|
| URL | `trendlyne.com` → Concalls menu |
| Access | Free tier (recent transcripts) |
| Format | PDF |
| Coverage | Tagged by company, quarter, sector |

---

### 1D — Tijori Finance Concalls

| Field | Detail |
|-------|--------|
| URL | `tijorifinance.com` → search company → Concalls |
| Coverage | Nifty 500, large-caps, good historical depth |
| Format | PDF |

---

### 1E — NSE Announcements (Parallel to BSE)

| Field | Detail |
|-------|--------|
| URL | `nseindia.com/companies-listing/corporate-filings/corporate-announcements` |
| Filter | "Analyst/Institutional Investor Meet/Con. Call Updates" |
| Note | Same transcripts as BSE — use as backup / dedup |

> ⚠️ NSE blocks direct downloads without session cookie. Use browser cookie export + `wget`.

---

### 1F — Company IR Websites (Highest Quality, No OCR Errors)

Scrape these individually for older/better-quality transcripts:

| Company | IR URL |
|---------|--------|
| Reliance | `ril.com/InvestorRelations` |
| TCS | `tcs.com/investor-relations` |
| HDFC Bank | `hdfcbank.com/personal/resources/investor-relations` |
| *...all Nifty 50 companies* | `[company].com/investor-relations` |

---

### 1G — Moneycontrol (Older Archive, 2015–2018)

| Field | Detail |
|-------|--------|
| URL | `moneycontrol.com/stocks/company_info/` → click company → "Concall" |
| Coverage | Large-caps, transcripts back to 2015–16 |
| Use | Fill gaps for pre-2019 data |

---

## Phase 2 — Annual Reports: Nifty 500 First (~800M tokens)

*Reason: Top 500 companies = 90% of India's market cap. Start here, not all 5,000.*

### 2A — BSE Annual Reports (Nifty 500)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Filter | Category → **"Annual Report"** |
| Scope | Nifty 500 scrip codes only, FY2020–FY2024 (4 years) |
| Volume | ~2,000 files |
| Avg Pages | 160 pages each |
| Est. Tokens | ~800M |
| Format | PDF |

**Steps:**
1. Get list of Nifty 500 BSE scrip codes (from NSE website or screener.in)
2. For each scrip code: query `bseindia.com/corporates/ann.html` with category = Annual Report
3. Download all PDFs per company per year
4. Extract text

---

### 2B — NSE Annual Reports (Nifty 500)

| Field | Detail |
|-------|--------|
| URL | `nseindia.com/companies-listing/corporate-filings/annual-reports` |
| Note | Same companies, sometimes extra material uploaded here |
| Use | Pick up any files BSE missed |

---

### 2C — Moneycontrol / Screener (Pre-2020 Annual Reports)

| Field | Detail |
|-------|--------|
| URLs | `moneycontrol.com/financials/` and `screener.in` |
| Coverage | Historical annual reports back to 2000 for large caps |
| Use | Fill gaps for FY2015–FY2019 |

---

## Phase 3 — Quarterly Results + Shareholding Patterns (~700M tokens)

### 3A — Quarterly Results (All Companies, 5 Years)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Filter | Category → **"Financial Results"** |
| Scope | All companies, Q1 FY2020 – Q3 FY2025 |
| Volume | ~100,000 filings |
| Avg Pages | 5 pages each |
| Est. Tokens | ~500M |
| Format | PDF / HTML |

---

### 3B — Shareholding Patterns (All Companies, 5 Years)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/shp.html` |
| Scope | All companies, every quarter, 5 years |
| Volume | ~100,000 filings |
| Avg Pages | 3 pages each |
| Est. Tokens | ~200M |
| Format | XLSX / PDF |

**What to capture:** Promoter holding %, FII %, DII %, Public %, Promoter pledge data

---

### 3C — Investor Presentations

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Filter | Category → **"Investor Presentation"** |
| Backup | Company IR pages |
| Note | Dense with data, charts, forward guidance |

---

## Phase 4 — IPO Documents + Credit Rating Reports (~2.7B tokens)

### 4A — DRHP / IPO Prospectuses (~1.4B tokens)

| Field | Detail |
|-------|--------|
| Primary URL | `sebi.gov.in` → Filings → **"Draft Offer Documents"** |
| Mirror 1 | `bseindia.com/markets/PublicIssues/DraftProspectus.aspx` |
| Mirror 2 | `nseindia.com/companies-listing/primary-market` |
| Scope | All DRHPs filed 2014–2024 |
| Volume | ~3,500 DRHPs (1,500 mainboard + 2,000 SME) |
| Avg Pages | 400 pages each |
| Est. Tokens | ~1.4B |
| Format | PDF |

**Also download:** Final prospectuses at `sebi.gov.in` → Filings → "Final Offer Documents"

**Why critical:** Only document combining industry analysis + risk disclosure + financial history + corporate narrative in one place. 400–700 pages of the richest company-level content that exists.

---

### 4B — Credit Rating Rationales (~900M tokens)

#### CRISIL
| Field | Detail |
|-------|--------|
| URL | `crisil.com/en/home/our-businesses/ratings/credit-rating-news-and-views.html` |
| Also | `crisilratings.com` |
| Coverage | 25,000+ rated entities, avg 3 rationale docs each |
| Format | PDF (4–8 pages each) |

#### ICRA
| Field | Detail |
|-------|--------|
| URL | `icra.in/Rationale/Index` |
| Coverage | All rated entities, publicly searchable by company and sector |

#### CARE Ratings
| Field | Detail |
|-------|--------|
| URL | `careratings.com/Ratings/RatingAction.aspx` |
| Coverage | Full database of press releases and rationales |

#### India Ratings (Fitch)
| Field | Detail |
|-------|--------|
| URL | `indiaratings.co.in/RatingActions` |
| Coverage | Full database |

> **Also scrape:** Each agency's free sector research reports — CRISIL Research sector reports are especially high-quality training material.

---

### 4C — Takeover / Open Offer Documents (~150M tokens)

| Field | Detail |
|-------|--------|
| URL | `sebi.gov.in` → Regulatory → Takeovers → Open Offer Documents |
| Direct | `sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=7&ssid=14` |
| Volume | ~1,000–1,500 offer documents (15 years × 50–100/year) |
| Avg Pages | 100 pages each |
| Est. Tokens | ~150M |

---

### 4D — QIP / Rights Issue / Buyback Documents (~200M tokens)

| Field | Detail |
|-------|--------|
| URL | SEBI filings portal (same as DRHPs) |
| Also | BSE / NSE announcements, filter by "Rights Issue" / "Buyback" / "QIP" |
| Volume | 500+ QIPs in last 10 years + rights + buybacks |
| Avg Pages | 100–200 pages each |

---

## Phase 5 — Board Announcements + NSE Docs + Remaining Annual Reports (~1.5B tokens)

### 5A — Board Meeting Outcomes + Corporate Announcements (~500M tokens)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Categories to pull | "Board Meeting," "Insider Trading/SAST," "Dividend," "Bonus," "Buyback," "Demerger" |
| Volume | ~500,000 filings |
| Avg Pages | 2 pages each |
| Est. Tokens | ~500M |

---

### 5B — Insider Trading Disclosures

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Filter | Category → **"Insider Trading/SAST"** |
| Note | Director/promoter/KMP buy-sell disclosures, filed within 2 trading days |

---

### 5C — NSE Circulars + F&O Contract Specs (~200M tokens)

| Field | Detail |
|-------|--------|
| NSE Circulars | `nseindia.com/regulations/circulars` — 2000–2026, all available |
| F&O Specs | `nseindia.com/products-services/equity-derivatives-contract-specifications` |
| NSE Knowledge Hub | `nseindia.com/learn/learnings` — educational PDFs |
| NSE Index Methodology | `nseindia.com/products-services` — one per index, updated quarterly |
| Volume | ~5,000 documents |
| Avg Pages | 10 pages each |
| Est. Tokens | ~200M |

---

### 5D — Annual Reports: Remaining 4,500 Companies (~800M tokens)

| Field | Detail |
|-------|--------|
| URL | `bseindia.com/corporates/ann.html` |
| Scope | All BSE listed companies EXCLUDING Nifty 500 (already done in Phase 2) |
| Volume | ~18,000 files |
| Avg Pages | 80 pages each |
| Est. Tokens | ~800M |
| ⚠️ Warning | Many small-caps have low-quality disclosures — apply quality filter aggressively |

---

### 5E — MCA21 ROC Filings — Unlisted Companies (~2B tokens)

| Field | Detail |
|-------|--------|
| Master Data URL | `mca.gov.in/content/mca/global/en/data-and-reports/company-data.html` |
| Filing Access | `efiling.mca.gov.in` → search by CIN |
| Coverage | 2+ million registered companies (unlisted) |
| Documents | Balance Sheet, P&L, Director's Report, Auditor's Report, Cash Flow, Notes |
| Bulk Data | MCA publishes complete company master data as free download |
| Format | Individual filings: public, no cost, per-document access |
| Priority | Jio, Tata Sons, Reliance Retail, Zerodha, large NBFCs, PE-backed companies |

**Why:** India's unlisted sector is larger than the listed sector by number of companies. Jio, Reliance Retail, Tata Sons — all unlisted.

---

## Bonus Scrapes — High Impact Additions

### B1 — Proxy Advisory Reports (~200M tokens)

| Source | URL | Notes |
|--------|-----|-------|
| InGovern | `ingovern.com` | Nifty 500, free reports — most comprehensive |
| IiAS | `iias.in` | Free subset, governance scorecards |
| SES | `sesindia.org` | Minority shareholder protection focus |

---

### B2 — Mutual Fund Monthly Portfolios + AMFI Data (~400M tokens)

| Field | Detail |
|-------|--------|
| Primary | `amfiindia.com/research-information/mf-data` |
| Coverage | Monthly portfolios for every scheme, every AMC, back to 2000 |
| Format | CSV / PDF |
| Also | Individual AMC factsheets: HDFC AMC, SBI MF, ICICI Pru AMC, Nippon India MF, Axis MF |

---

### B3 — Exchange Surveillance Notices (~150M tokens)

| Source | URL |
|--------|-----|
| BSE Notices | `bseindia.com/markets/MarketInfo/NoticesCirculars.aspx` |
| NSE Disciplinary | `nseindia.com/regulations/member-regulations/disciplinary-actions` |
| What to get | ASM/GSM notices, trading member actions, non-compliance notices |

---

### B4 — NISM Certification Study Material (~100M tokens)

| Field | Detail |
|-------|--------|
| URL | `nism.ac.in/certification-examinations/` |
| Priority Modules | NISM V-A (Mutual Fund Distributors), NISM VIII (Equity Derivatives), NISM X-A/B (Investment Adviser), NISM Research Analyst |
| Format | Free PDFs |
| Total | 22+ certifications |

---

### B5 — NSE Academy + BSE Institute Course Material (~150M tokens)

| Source | URL |
|--------|-----|
| NSE Academy | `nseindia.com/learn/learnings` |
| BSE Institute | `bsebti.com` |
| Groww Learn | `groww.in/learn` |
| Upstox Learn | `upstox.com/learn` |
| Angel One | `angelone.in/knowledge-center` |

---

## Master Download Map

| # | Data Type | Primary URL | Backup URL | Format | Phase |
|---|-----------|-------------|------------|--------|-------|
| 1 | Concall Transcripts | `bseindia.com/corporates/ann.html` (cat: Concall) | `screener.in/concalls/` | PDF | 1 |
| 2 | Concall Transcripts | `trendlyne.com` → Concalls | `tijorifinance.com` | PDF | 1 |
| 3 | Concall Transcripts (old) | Company IR pages | `moneycontrol.com` | PDF | 1 |
| 4 | Annual Reports (Nifty 500) | `bseindia.com/corporates/ann.html` (cat: Annual Report) | `nseindia.com/corporate-filings/annual-reports` | PDF | 2 |
| 5 | Annual Reports (pre-2020) | `moneycontrol.com/financials/` | `screener.in` | PDF | 2 |
| 6 | Quarterly Results | `bseindia.com/corporates/ann.html` (cat: Financial Results) | `nseindia.com` | PDF/HTML | 3 |
| 7 | Shareholding Patterns | `bseindia.com/corporates/shp.html` | `nseindia.com` | XLSX/PDF | 3 |
| 8 | Investor Presentations | `bseindia.com/corporates/ann.html` (cat: Investor Presentation) | Company IR pages | PDF | 3 |
| 9 | DRHPs | `sebi.gov.in` → Filings → Draft Offer Documents | `bseindia.com/markets/PublicIssues/DraftProspectus.aspx` | PDF | 4 |
| 10 | Final Prospectuses | `sebi.gov.in` → Filings → Final Offer Documents | NSE primary market | PDF | 4 |
| 11 | CRISIL Rating Rationales | `crisilratings.com` | `crisil.com/ratings` | PDF | 4 |
| 12 | ICRA Rating Rationales | `icra.in/Rationale/Index` | — | PDF | 4 |
| 13 | CARE Rating Rationales | `careratings.com/Ratings/RatingAction.aspx` | — | PDF | 4 |
| 14 | India Ratings Rationales | `indiaratings.co.in/RatingActions` | — | PDF | 4 |
| 15 | Open Offer Documents | `sebi.gov.in` (SAST section) | — | PDF | 4 |
| 16 | QIP / Rights / Buyback Docs | SEBI filings portal | BSE/NSE announcements | PDF | 4 |
| 17 | Board Meeting Outcomes | `bseindia.com/corporates/ann.html` (cat: Board Meeting) | — | PDF | 5 |
| 18 | Insider Trading Disclosures | `bseindia.com/corporates/ann.html` (cat: Insider Trading/SAST) | — | PDF | 5 |
| 19 | NSE Circulars | `nseindia.com/regulations/circulars` | — | PDF | 5 |
| 20 | F&O Contract Specs | `nseindia.com/products-services/equity-derivatives-contract-specifications` | — | PDF | 5 |
| 21 | NSE Index Methodology | `nseindia.com/products-services` | — | PDF | 5 |
| 22 | Annual Reports (remaining 4,500) | `bseindia.com/corporates/ann.html` | — | PDF | 5 |
| 23 | MCA21 Unlisted Filings | `efiling.mca.gov.in` | `mca.gov.in/data-and-reports` | PDF | 5 |
| 24 | Proxy Advisory Reports | `ingovern.com`, `iias.in`, `sesindia.org` | — | PDF | Bonus |
| 25 | AMFI Monthly Portfolios | `amfiindia.com/research-information/mf-data` | AMC websites | CSV/PDF | Bonus |
| 26 | Exchange Surveillance | `bseindia.com/markets/MarketInfo/NoticesCirculars.aspx` | `nseindia.com/regulations/member-regulations` | PDF | Bonus |
| 27 | NISM Study Material | `nism.ac.in/certification-examinations/` | — | PDF | Bonus |
| 28 | Broker Education Content | `groww.in/learn`, `upstox.com/learn`, `angelone.in/knowledge-center` | `nseindia.com/learn` | HTML | Bonus |

---

## Token Summary by Phase

| Phase | What | Est. Tokens | Priority |
|-------|------|-------------|----------|
| Phase 1 | Concall Transcripts | ~2.5B | 🔴 Do first |
| Phase 2 | Annual Reports — Nifty 500 | ~800M | 🔴 Do second |
| Phase 3 | Quarterly Results + Shareholding | ~700M | 🟠 Do third |
| Phase 4 | IPOs + Credit Ratings + M&A Docs | ~2.7B | 🟠 Do fourth |
| Phase 5 | Board Announcements + NSE + Remaining ARs + MCA | ~3.5B | 🟡 Do last |
| Bonus | Proxy, AMFI, NISM, Broker Content | ~1.0B | 🟢 If capacity |
| **TOTAL** | | **~11.2B** | |

> Target is 6B tokens. Phases 1–3 alone get you to ~4B. Adding selective Phase 4 (IPOs + Credit Ratings) gets you past 6B with the highest-quality data.

---

## Technical Notes

- **NSE Session Cookie:** NSE blocks direct downloads without a browser session. Export cookie from browser and use with `wget` or `requests`.
- **BSE Pagination:** BSE announcement search paginates — scrape all pages per filter combination.
- **PDF Extraction:** Use `pdfplumber` or `pymupdf` — many BSE filings are scanned PDFs requiring OCR (`pytesseract` / `pdfminer`).
- **Deduplication:** BSE and NSE mirror many filings. Hash PDFs after download and deduplicate before text extraction.
- **Quality Filter for Small-Caps:** Phase 5's 4,500 small-cap annual reports will have low-quality disclosures. Filter out companies with market cap < ₹100 crore or filings < 20 pages.
- **MCA21 Rate Limiting:** MCA portal throttles requests — use delays between requests and retry logic.
