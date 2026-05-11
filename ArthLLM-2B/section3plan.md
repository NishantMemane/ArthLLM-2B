Here is the complete breakdown of Section 3 — what it is, why it matters, and exactly where and how to get every piece of it.

---

# Section 3 — Stock Exchange Filings (~6B tokens)

## 📋 Progress Tracking Checklist
- [ ] BSE Annual Reports (Nifty 500)
- [ ] BSE Annual Reports (Remaining 4,500)
- [ ] BSE Quarterly Results
- [ ] BSE Shareholding Patterns
- [ ] BSE Board Meeting Outcomes (Dividends, Bonus, Demerger, etc.)
- [ ] BSE Insider Trading
- [ ] BSE/NSE Investor Presentations
- [ ] BSE/NSE Concall Transcripts
- [ ] NSE Circulars & F&O Specs
- [ ] NSE Index Methodology
- [ ] IPO Documents / DRHP
- [ ] Credit Rating Reports
- [ ] MCA21 ROC Filings
- [ ] Mutual Fund Monthly Portfolios (AMFI)
- [ ] Proxy Advisory Reports
- [ ] Takeover / Open Offer Documents
- [ ] QIP, Rights Issue, Buyback Documents
- [ ] Exchange Surveillance and Disciplinary Actions
- [ ] AMFI Agent / Distributor Training Material
- [ ] NSE Academy / BSE Institute Course Material
- [ ] Screener.in / Tijori Structured Data
- [ ] Demat and Broker Educational Content

---

## What This Section Actually Is

Think of Section 3 as **the financial report cards of every Indian company**. While Section 2 gives ArthLLM the rules (RBI/SEBI regulations), Section 3 gives it the **real-world application** — what companies actually do, earn, spend, and say to investors. This is the layer that makes ArthLLM understand Indian corporate finance from the inside, not just from a textbook.

There are three distinct sub-sources inside Section 3:

---

## Sub-Source A — BSE India Corporate Filings (~2B tokens)

### What It Is

BSE (Bombay Stock Exchange) is Asia's oldest stock exchange, with 5,000+ listed companies. Every listed company is legally required under SEBI LODR (Listing Obligations and Disclosure Requirements) to file documents with BSE. These filings are **publicly available** — they are not paywalled, not premium, just sitting there on the BSE website waiting to be downloaded.

What gets filed:

**Annual Reports** — The most important document a company produces. Every year, every listed company files a 100–400 page document containing: Audited financial statements (Balance Sheet, P&L, Cash Flow), Management Discussion and Analysis (MD&A), Director's Report, Corporate Governance Report, Notes to Accounts, Segment-wise performance breakdown. For 5,000 companies × 4 years = 20,000 annual reports. At ~80 pages each = ~1.6B tokens.

**Quarterly Results** — Every 3 months, companies report revenue, EBITDA, PAT, EPS. Comes with a brief management commentary. 5,000 companies × 4 quarters × 5 years = 100,000 filings.

**Corporate Announcements** — Dividend declarations, stock splits, bonus issues, buyback programs, board meeting outcomes, AGM notices, demerger schemes, rights issues, ESOP grants. Every material event a company announces goes here.

**Shareholding Patterns** — Filed every quarter. Shows exactly how much promoters own, how much FIIs own, how much DIIs own, how much public holds. Critically includes promoter pledge data — when promoters mortgage their shares to raise loans, this shows up here.

**Insider Trading Disclosures** — Every time a director, promoter, or KMP buys or sells shares, it must be disclosed within 2 trading days. This creates a real-time window into what insiders believe about their own company.

**Investor Presentations** — Companies upload slide decks after quarterly results explaining their performance. Dense with data, charts, forward guidance.

**Board Meeting Outcomes** — After every board meeting, companies file what was decided: new directors, auditor changes, capex approvals, subsidiary incorporations, related party transactions.

### Why ArthLLM Needs This

This data teaches the model:
- How Indian companies structure their financial disclosures
- Indian accounting terminology (Ind AS, depreciation as per Schedule II, deferred tax, ESOP accounting)
- Real numbers in crores and lakhs — "Revenue ₹4,250 crore, up 18% YoY"
- Promoter-specific language that no global LLM knows — "promoter holding," "creeping acquisition," "pledge creation/revocation"
- How Indian board governance actually works — related party transactions, audit committee recommendations, independent director declarations

### Where to Download

**Primary source — BSE website directly:**
Go to `bseindia.com` → click "Corporate" in the top menu → click "Announcements"

You will see a search interface. You can filter by:
- Company name or BSE scrip code
- Announcement category (Annual Report, Shareholding Pattern, Board Meeting, etc.)
- Date range

For annual reports specifically: `bseindia.com/corporates/ann.html`

For shareholding patterns: `bseindia.com/corporates/shp.html`

**Bulk approach — BSE Data Products:**
BSE has a dedicated data products section at `bseindia.com/markets/MarketInfo/BseDataArch.aspx`. This is BSE's own data archive. You can request bulk data packages here. There is a form to fill. Some packages are free, some are paid. The free ones include historical announcement data.

**Alternative — NSE also mirrors many BSE filings:**
`nseindia.com/companies-listing/corporate-filings/corporate-announcements`

Same LODR rules apply — most major companies file on both exchanges. If BSE is slow, NSE often has the same document.

**For old annual reports (pre-2010):**
`moneycontrol.com/financials/` has historical annual reports going back to 2000 for large companies. Screener.in also archives them.

---

## Sub-Source B — NSE India Filings (~2B tokens)

### What It Is

NSE (National Stock Exchange) lists around 2,000 companies (fewer than BSE but more liquid). The overlap with BSE is large — most companies list on both. But NSE has unique data that BSE doesn't:

**Nifty Index Methodology Documents** — How each index (Nifty 50, Nifty Bank, Nifty IT, Nifty Midcap 150) is constructed, rebalanced, and maintained. These documents explain which stocks get included, with what weightage, and why.

**NSE Circulars** — NSE issues its own operational circulars to its members (brokers) about trading rules, margin requirements, F&O lot size changes, new contract introductions. Different from SEBI circulars — more operational.

**F&O Contract Specifications** — Every futures and options contract on NSE has a specification sheet: lot size, expiry, settlement method, margin requirements. There are hundreds of these across equities, indices, currencies, and commodities.

**Governance Reports** — Board composition, related party transactions, corporate governance compliance reports.

**Integrated Annual Reports** — Similar to BSE but sometimes the same company uploads a higher-resolution version or additional material to NSE.

**Market Watch Data (Historical)** — NSE publishes historical OHLCV (Open, High, Low, Close, Volume) data for all listed securities going back to 1994. While this is numerical rather than text, the accompanying market bulletins and daily market reports are text-rich.

**NSE Knowledge Hub** — NSE publishes educational material, market reports, derivatives education modules. All English, all public.

### Why ArthLLM Needs This Separately

NSE-specific data teaches ArthLLM:
- F&O market language — "lot size," "open interest," "rollover," "put-call ratio," "implied volatility," "theta decay"
- Index construction logic — why certain stocks are in Nifty, how rebalancing works
- Broker-facing regulatory language which is different from retail investor language
- Market operations terminology — "trade-for-trade segment," "physical settlement," "exercise and assignment"

### Where to Download

**Primary — NSE website:**
`nseindia.com` → "Companies Listing" → "Corporate Filings" → "Corporate Announcements"

For annual reports: `nseindia.com/companies-listing/corporate-filings/annual-reports`

For F&O contract info: `nseindia.com/products-services/equity-derivatives-contract-specifications`

For NSE circulars: `nseindia.com/regulations/circulars`

**NSE Data Products (free historical data):**
`nseindia.com/market-data/live-market-statistics` — daily bhav copy (price data)
`nseindia.com/products-services/historical-data-equities` — historical OHLCV

**NSE Knowledge Hub:**
`nseindia.com/learn/learnings` — educational documents in PDF

**Important NSE trick — the session-cookie method:**
NSE's website blocks direct file downloads unless you have a session cookie from their site. The way to get around this (without code): Open NSE in your browser, navigate to the file you want, right-click → Save As. Your browser already has the session cookie so the download works. For bulk downloads, tools like `wget` with cookie export from your browser work well.

---

## Sub-Source C — Earnings Call Transcripts (~2B tokens)

### What It Is

This is the **single most differentiated and valuable sub-source** in Section 3. Nothing else in your entire 40B token corpus will sound quite like this.

An earnings call (called "concall" in Indian finance) is a quarterly conference call where the company's CEO, CFO, and sometimes the MD speak to analysts and investors for 45–90 minutes. The format is:
1. Management gives a prepared 10–15 minute presentation on quarterly results
2. Analysts from Goldman, Morgan Stanley, IIFL, Motilal Oswal, Kotak Securities, etc. ask questions
3. Management answers in detail

These transcripts teach ArthLLM:
- How Indian corporate management thinks and communicates
- Cause-effect relationships in Indian business — "raw material cost inflation impacted EBITDA margins by 180bps"
- Forward guidance language — "we expect volume growth in the range of 12-15% for FY25"
- Sector-specific Indian terminology — cement companies talk differently from IT companies, banks talk differently from pharma
- Analyst questioning style — the kind of questions users will actually ask ArthLLM

The Nifty 500 alone, over 5 years, gives 10,000 transcripts. Scale to all BSE companies that conduct calls and you get 30,000–50,000 transcripts.

### Where to Download

**Source 1 — Screener.in (Best starting point, free):**
Go to `screener.in` → search for any company → scroll to "Documents" section → click "Concall Transcripts." Screener has manually curated transcripts for hundreds of Nifty 500 companies going back 3–5 years. These are PDFs. Download them individually.

For bulk access: Screener has a free API. You can also browse their concall section at `screener.in/concalls/` which lists recent transcripts sorted by date.

**Source 2 — BSE Announcements (Largest free source):**
Go to `bseindia.com/corporates/ann.html` → in the "Category" filter, select "Analysts/Institutional Investor Meet/Con. Call Updates" → set date range. Companies are required to upload concall transcripts as a regulatory filing within a few days of the call. This is the most comprehensive source because it's legally mandated. You will find transcripts for 2,000+ companies here.

**Source 3 — Trendlyne (Best organized, free tier):**
Go to `trendlyne.com` → click "Concalls" in the top menu. Trendlyne has one of the best organized concall databases in India. They tag transcripts by company, quarter, sector. The free tier gives access to recent transcripts. They also have AI-generated summaries alongside the originals.

**Source 4 — Tijori Finance:**
Go to `tijorifinance.com` → search a company → click on "Concalls." Tijori focuses on Nifty 500 companies and has good historical depth for large-caps.

**Source 5 — Company Investor Relations websites:**
Every large company maintains an Investor Relations (IR) section on their own website where they upload transcripts, presentations, and annual reports. For example:
- Reliance: `ril.com/InvestorRelations`
- TCS: `tcs.com/investor-relations`
- HDFC Bank: `hdfcbank.com/personal/resources/investor-relations`

These are often higher quality (no OCR errors) and go further back in time than third-party aggregators.

**Source 6 — NSE Announcements (parallel to BSE):**
`nseindia.com/companies-listing/corporate-filings/corporate-announcements` → filter by "Analyst/Institutional Investor Meet/Con. Call Updates." Same transcripts as BSE but sometimes different upload timing.

**Source 7 — Moneycontrol (For older transcripts):**
`moneycontrol.com/stocks/company_info/` → click any company → "Concall." Moneycontrol has an older archive and sometimes has transcripts going back to 2015-16 for large caps.

---

## The Full Section 3 Download Map (No Code)

Here is the complete picture of where everything lives and how to get it:

| Data Type | Primary Source | Backup Source | Format | Notes |
|---|---|---|---|---|
| Annual Reports (BSE) | bseindia.com/corporates/ann.html | moneycontrol.com/financials | PDF | Filter category: "Annual Report" |
| Annual Reports (NSE) | nseindia.com/corporate-filings/annual-reports | Same as above | PDF | Some companies upload extra material |
| Quarterly Results | bseindia.com/corporates/ann.html | nseindia.com | PDF/HTML | Category: "Financial Results" |
| Shareholding Pattern | bseindia.com/corporates/shp.html | nseindia.com | XLSX/PDF | Every quarter, every company |
| Board Meeting Outcomes | bseindia.com/corporates/ann.html | — | PDF | Category: "Board Meeting" |
| Insider Trading | bseindia.com/corporates/ann.html | — | PDF | Category: "Insider Trading/SAST" |
| Investor Presentations | bseindia.com/corporates/ann.html | Company IR pages | PDF | Category: "Investor Presentation" |
| NSE Circulars | nseindia.com/regulations/circulars | — | PDF | 2000–2026, all available |
| F&O Contract Specs | nseindia.com/products-services | — | PDF | All equity, index, currency contracts |
| Concall Transcripts | bseindia.com (regulatory uploads) | screener.in/concalls | PDF | This is the richest source |
| Concall Transcripts | trendlyne.com/concalls | tijorifinance.com | PDF | Better organized |
| Concall Transcripts | Company IR websites | moneycontrol.com | PDF | Highest quality, older archive |
| NSE Index Methodology | nseindia.com/products-services | — | PDF | One per index, updated quarterly |

---

## Priority Order for Downloading Section 3

Given you have limited time and the data is large, here is the order that maximizes impact:

**Do first (highest signal per token):**
Earnings call transcripts from BSE announcements. This is unique, differentiated, and nothing else in your corpus sounds like it. Set the BSE filter to "Analysts/Con. Call Updates" and pull 5 years of data.

**Do second:**
Annual reports from BSE for the Nifty 500 companies only. The top 500 companies cover 90% of India's market cap. Start here rather than all 5,000 companies.

**Do third:**
Quarterly results for Nifty 500. These are short (2–5 pages each) but there are 10,000 of them and they teach the model numerical financial reasoning.

**Do fourth:**
Shareholding patterns for Nifty 500, all quarters for 5 years. This teaches the model promoter-FII-DII ownership language.

**Do last:**
Expand annual reports and quarterly results to the full BSE universe of 5,000 companies. Many will be small-cap with low-quality disclosures, so quality filter aggressively here.

---

## Token Reality Check

| Sub-Source | Files | Avg Pages | Tokens |
|---|---|---|---|
| BSE Annual Reports (Nifty 500, 4 years) | 2,000 | 160 | ~800M |
| BSE Annual Reports (remaining 4,500 companies) | 18,000 | 80 | ~800M |
| Quarterly Results (all, 5 years) | 100,000 | 5 | ~500M |
| Shareholding Patterns (all, quarterly) | 100,000 | 3 | ~200M |
| Board Outcomes + Announcements | 500,000 | 2 | ~500M |
| Concall Transcripts (Nifty 500, 5 years) | 10,000 | 25 | ~1.5B |
| Concall Transcripts (extended universe) | 20,000 | 20 | ~1.0B |
| NSE Circulars + Specs + Docs | 5,000 | 10 | ~200M |
| **Section 3 Total** | | | **~5.5B** |

This lands right at your 6B target after accounting for deduplication between BSE and NSE copies of the same document.

The most important thing to remember about Section 3: the earnings call transcripts alone are worth more per token than almost anything else in your corpus because they teach the model the conversational, reasoning layer of Indian corporate finance — the layer users will actually expect when they ask ArthLLM questions.


Section 3 — Missing Sources That Belong Here🔴 CRITICAL MISSING — These Should Have Been in the Original PlanAddition 1 — IPO Documents / DRHP (~1.5B tokens)What it is:Every company that lists on BSE or NSE must file a Draft Red Herring Prospectus (DRHP) with SEBI before the IPO. This is the most detailed document a company ever produces about itself — more detailed than any annual report.A typical DRHP runs 400–700 pages and contains:

Complete business description — every product, every geography, every customer segment
5 years of restated financials — the most audited numbers in existence
Risk factors — companies must disclose every conceivable risk in plain English. This section alone is 50–80 pages of structured risk language
Industry analysis — sector size, growth rates, competitive landscape
Management background — every director's full career history
Legal proceedings — every pending case against the company
Use of proceeds — exactly where the IPO money is going and why
Objects of the issue — capex plans, debt repayment, working capital
Related party transactions — full history of promoter dealings
Why ArthLLM desperately needs this:No other document combines industry analysis, risk disclosure, financial history, and corporate narrative in one place. A model trained on DRHPs understands:

How Indian companies describe their businesses to investors
How risk is communicated in Indian securities law language
Sector-specific language for every industry (cement, pharma, fintech, NBFC, hospital, logistics)
IPO-specific terminology — anchor investors, price band, grey market premium, allotment ratio, oversubscription
Scale: India has had approximately 1,500+ mainboard IPOs in the last 10 years and 2,000+ SME IPOs. That is 3,500+ DRHPs at 400 pages average = approximately 1.4B tokens of the richest company-level content that exists.Where to download:SEBI's website is the primary repository. Go to sebi.gov.in → "Filings" → "Draft Offer Documents." Every DRHP filed since 2000 is available as a free PDF. They are organized by year and company name.The BSE website also mirrors these at bseindia.com/markets/PublicIssues/DraftProspectus.aspxNSE mirrors them at nseindia.com/companies-listing/primary-marketFor the final prospectus (after SEBI approval, with price band added): sebi.gov.in → "Filings" → "Final Offer Documents"Addition 2 — Credit Rating Reports (~1.2B tokens)What it is:India has four major credit rating agencies — CRISIL (S&P subsidiary), ICRA (Moody's subsidiary), CARE Ratings, and India Ratings (Fitch subsidiary). Every rated entity — every bank, every NBFC, every large company that borrows — has a rating rationale document published by these agencies.A rating rationale is typically 4–8 pages and contains:

Overall rating and outlook (AAA, AA+, A, BBB, below investment grade)
Detailed financial analysis — leverage ratios, coverage ratios, liquidity position
Business risk assessment — market position, customer concentration, regulatory risk
Management quality assessment
Industry-specific risk factors
Outlook — what would cause an upgrade or downgrade
Rating agencies also publish:

Sector reports — annual/quarterly views on banking, real estate, NBFC, infrastructure
Research reports — thematic analysis on specific financial topics
Default studies — historical default rates by rating category
Rating transition matrices — how ratings migrate over time
Why ArthLLM needs this:Credit rating language is a distinct and extremely important dialect of Indian finance. Every banker, every treasury professional, every analyst reads rating rationales. ArthLLM without this cannot:

Explain what makes a company AAA vs BBB
Discuss credit risk in Indian bond markets
Analyze NBFC or bank creditworthiness
Understand why rating downgrades trigger financial crises (IL&FS was rated AAA two months before default)
This is also the only source that gives ArthLLM structured, expert-written analysis of private companies and unlisted entities — NBFCs, housing finance companies, infrastructure SPVs that never appear in BSE filings.Scale: CRISIL alone has rated 25,000+ entities over its history. If each has an average of 3 rating rationale documents = 75,000 documents × 6 pages = 450,000 pages = approximately 450M tokens. Across all four agencies the number doubles to ~900M tokens.Where to download:CRISIL: crisil.com/en/home/our-businesses/ratings/credit-rating-news-and-views.html — Rating rationales are publicly available for all rated entities. Search by company name or sector. Also crisilratings.comICRA: icra.in/Rationale/Index — All rating rationales publicly available, searchable by company and sectorCARE Ratings: careratings.com/Ratings/RatingAction.aspx — Full database of press releases and rationalesIndia Ratings: indiaratings.co.in/RatingActions — Full databaseBonus: All four agencies also publish free sector research at their main websites. CRISIL Research in particular publishes deep sector reports that are exceptional training material.Addition 3 — MCA21 ROC Filings for Unlisted Companies (~2B tokens)What it is:This is the single biggest gap in the entire ArthLLM corpus that nobody has thought about.Every company registered in India — not just listed companies, but ALL 2+ million registered companies — must file annual financial statements with the Registrar of Companies through the MCA21 system. This includes:

Balance Sheet
Profit & Loss Statement
Director's Report
Auditor's Report
Cash Flow Statement
Notes to Accounts
This means ArthLLM can learn the financials of Reliance Jio (unlisted), Nykaa's subsidiaries, every private equity-backed startup, every large NBFC that isn't listed, every subsidiary of every listed company, every family-owned conglomerate.The Director's Report alone is a goldmine — it's a 15–30 page narrative describing the business, risks, financial performance, and future plans, written in formal Indian corporate English.Why this matters enormously:India's unlisted sector is actually larger than the listed sector by number of companies. Many of India's most important economic entities are unlisted — Jio, Tata Sons, Reliance Retail, D-Mart's subsidiaries, Zerodha, all private banks' subsidiaries. If ArthLLM only knows listed company language, it has a massive blind spot.Where to download:MCA21 Public Data: mca.gov.in/content/mca/global/en/data-and-reports/company-data.htmlMCA offers a free data extract of all company master data. Financial filings are publicly accessible through the MCA21 portal at efiling.mca.gov.in — search any company by CIN (Corporate Identification Number) and download their filings.For bulk data: MCA publishes the complete company master data as a free download. The individual financial filings require per-document access but are all publicly available at no cost.Addition 4 — Mutual Fund Monthly Portfolios + AMFI Data (~400M tokens)What it is:Every mutual fund scheme in India must publish its complete portfolio every month. This means every stock, every bond, every money market instrument held — with quantities and market values. AMFI (Association of Mutual Funds in India) aggregates all of this.Additionally, AMFI publishes:

Monthly industry data — AUM by category, SIP flows, redemption data
Historical NAV data for every scheme going back to inception
Fund manager commentary — many AMCs publish monthly factsheets with fund manager views
What makes this exceptional training data:Fund manager commentary is a unique dialect. It sounds like this:"The fund maintained its overweight position in private sector banks 
given their superior asset quality metrics and NIM trajectory. 
We remain cautious on IT given demand uncertainty in key verticals. 
The portfolio's duration was kept short given our view of a higher 
for longer rate environment."This is expert-level Indian investment reasoning in clean, structured English — and there are 1,500+ schemes producing this commentary every month for 10+ years.Where to download:AMFI website: amfiindia.com/research-information/mf-data — Complete monthly portfolio disclosures for every scheme, every AMC, going back to 2000. All free, all downloadable as text/CSV/PDF.Individual AMC websites publish factsheets: HDFC AMC, SBI MF, ICICI Pru AMC, Nippon India MF, Axis MF — each publishes monthly factsheets with full portfolio + fund manager commentary.🟡 HIGH IMPACT MISSING — Should Definitely Be IncludedAddition 5 — Proxy Advisory Reports (~200M tokens)What it is:Before every company's Annual General Meeting (AGM), proxy advisory firms publish detailed reports analyzing whether shareholders should vote for or against each resolution. Three major players in India:InGovern Research (ingovern.com) — The most comprehensive. Analyzes board composition, related party transactions, executive compensation, auditor independence for all Nifty 500 companies.IiAS — Institutional Investor Advisory Services (iias.in) — Publishes detailed governance scorecards. Very structured analytical language.SES — Stakeholders Empowerment Services (sesindia.org) — Focuses on minority shareholder protection.A typical proxy advisory report is 15–40 pages and contains forensic-level analysis of governance issues that doesn't appear anywhere else:"The proposed remuneration of ₹18 crore for the MD represents 
142x the median employee compensation. In FY23, the company's 
PAT declined 23% while the MD's remuneration increased 18%. 
We recommend shareholders vote AGAINST this resolution."Why ArthLLM needs this: This teaches the model governance analysis, executive compensation benchmarking, related party transaction red flags — topics that are central to institutional investment in India but absent from every other source.Where to download: InGovern publishes free reports on their website. IiAS has a subscription model but releases some reports free. SES publishes research at their website. Many reports also get cited in financial media and are archived on BSE/NSE.Addition 6 — Takeover / Open Offer Documents (~300M tokens)What it is:When any entity acquires 25% or more of a listed company, SEBI's SAST (Substantial Acquisition of Shares and Takeovers) regulations require them to make a public open offer to buy an additional 26% from minority shareholders. The offer document filed for this is extraordinarily detailed:
Complete acquirer background and financial position
Detailed history of how the acquisition happened
Valuation methodology — why this price was chosen
Future plans for the company
Financing arrangement for the acquisition
Regulatory approvals obtained
These documents are fascinating because they tell the story of India's biggest M&A transactions from the inside — Mittal Steel acquiring Arcelor, Walmart acquiring Flipkart (the India listed entity angle), Tata acquiring Jaguar Land Rover (Indian parent's open offer obligations).Scale: SEBI processes 50–100 open offers per year. Going back 15 years = approximately 1,000–1,500 offer documents at 100 pages each = 150M tokens of pure M&A reasoning.Where to download: SEBI website → sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=7&ssid=14 — All open offer documents are publicly available.Addition 7 — QIP, Rights Issue, Buyback Documents (~200M tokens)What it is:When already-listed companies raise additional capital or return capital, they file detailed documents:QIP (Qualified Institutional Placement): When a listed company raises money by selling fresh shares to institutional investors. The placement memorandum is 100–200 pages with full company analysis, risk factors, use of proceeds. India has seen 500+ QIPs in the last 10 years.Rights Issue Documents: When a company offers existing shareholders the right to buy additional shares. The letter of offer is similarly detailed.Buyback Documents: When a company buys back its own shares. The offer document explains the rationale — cash generation, capital allocation philosophy, valuation assessment.All of these contain the company's own detailed self-assessment written at a specific point in time, which makes them different from annual reports in valuable ways.Where to download: All filed with SEBI and mirrored on BSE/NSE. Same SEBI filings portal as DRHPs.Addition 8 — Exchange Surveillance and Disciplinary Actions (~150M tokens)What it is:BSE and NSE both issue surveillance notices, trading member disciplinary actions, and market integrity communications that are separate from SEBI's enforcement actions:BSE Notices: bseindia.com/markets/MarketInfo/NoticesCirculars.aspx — BSE issues notices to listed companies for non-compliance, notices about stocks being moved to trade-for-trade segment, notices about enhanced surveillance measures.NSE Disciplinary Actions: nseindia.com/regulations/member-regulations/disciplinary-actions — NSE's disciplinary proceedings against brokers, trading members, and sub-brokers.Exchange-Imposed Surveillance: When a stock is placed in ASM (Additional Surveillance Measure) or GSM (Graded Surveillance Measure) framework — these notices explain exactly why (unusual price movement, poor financials, investor complaints).Why this matters: This teaches ArthLLM the language of market surveillance and the specific red flags that trigger regulatory attention — penny stocks, price manipulation patterns, corporate governance failures. This is signal that no other dataset provides.Addition 9 — AMFI Agent / Distributor Training Material (~100M tokens)What it is:AMFI certifies mutual fund distributors and agents through the NISM (National Institute of Securities Markets) examination. The study material for these exams is publicly available and covers:
Complete Indian mutual fund regulation
All fund categories and their investment mandates
Risk-o-meter framework
Distributor code of conduct
Tax treatment of mutual fund investments
Investor suitability assessment
This is textbook-quality structured content specifically written to explain Indian investment products to a lay audience — exactly the register ArthLLM needs when answering retail investor questions.Where to download: nism.ac.in/certification-examinations/ — All NISM study materials are free PDFs. Relevant certifications: NISM Series V-A (Mutual Fund Distributors), NISM Series VIII (Equity Derivatives), NISM Series X-A/B (Investment Adviser).Addition 10 — NSE Academy / BSE Institute Course Material (~150M tokens)What it is:Both exchanges run educational institutes with full certification programs:NSE Academy (nseindia.com/learn) — Courses on: Certified Market Professional, Derivatives Market, Currency Markets, Commodity Markets, Technical Analysis, Fundamental Analysis. All course material in English.BSE Institute (bsebti.com) — Post-graduate programs in Finance, Banking, Insurance. Study material covers Indian capital markets comprehensively.NISM (nism.ac.in) — 22+ different certification examinations for securities market professionals. Each has free workbooks covering: Equity, Derivatives, Mutual Funds, Investment Advisory, Research Analysis, Currency, Commodity, Depository.The NISM workbooks are particularly valuable — they are written by SEBI-affiliated educators and cover Indian markets regulation with perfect accuracy. Every regulatory concept ArthLLM needs to know about Indian capital markets is in these workbooks in clean, structured English.🟢 GOOD TO HAVE — Strong Additions If You Have CapacityAddition 11 — Screener.in + Tijori Finance Structured Data PagesBoth platforms aggregate 10 years of financial data for all listed companies into clean structured pages. The text descriptions, financial summaries, and ratio analyses on these pages are already clean and finance-relevant. Screener's company pages in particular include:
Concise business description in plain English
10-year financial summary with growth rates
Quarterly results timeline
Peer comparison tables
Shareholding trend analysis
screener.in/explore/ → every company page is publicly accessible.Addition 12 — Demat and Broker Educational ContentZerodha Varsity is already in your plan but deserves expansion. Other brokers also publish substantial free educational content:Zerodha Varsity (zerodha.com/varsity) — Already included, but ensure ALL modules are captured including Options Theory, Risk Management, Trading Systems, Personal Finance.Groww Learn (groww.in/learn) — Groww has built an exceptional free learning library covering stocks, mutual funds, IPOs, fixed deposits, insurance. Written for first-time Indian investors. Very clean English.Upstox Learn (upstox.com/learn) — Similar structured content.Angel One Knowledge Center (angelone.in/knowledge-center) — Technical analysis, fundamental analysis, derivatives education specific to Indian markets.HDFC Securities Learning Center — Banking and NBFC specific investment education.These platforms have collectively published millions of words of Indian-specific investment education that uses the exact vocabulary retail investors use when they ask questions — which is the vocabulary ArthLLM's users will use.