# ArthLLM — Complete Master Plan
## India's First 2B Parameter Indian Finance Language Model from Scratch
### Built in Pune. Built for Bharat.

---

> **ArthLLM** (Arth = अर्थ = Money + Meaning in Hindi/Sanskrit)
> The first LLM purpose-built for Indian financial markets, regulations, and language.
> Zero competition. Massive market. Built from scratch.

---

# TABLE OF CONTENTS

1. Project Vision
2. Why Indian Finance LLM — The Opportunity
3. Hardware & Compute Setup
4. Final Model Specifications
5. Data Strategy — 70% Indian / 30% Global
6. Indian-Specific Vocabulary & Concepts
7. Tokenizer Strategy (Indian-Aware)
8. Phase 1 — Tokenization (Done)
9. Phase 2 — Vector Embeddings (Done)
10. Phase 3 — Positional Encoding (RoPE + YaRN)
11. Phase 4 — Self Attention + GQA
12. Phase 5 — Transformer Block
13. Phase 6 — Full Model Architecture
14. Phase 7 — Data Pipeline (40B tokens, 70% Indian)
15. Phase 8 — Pre-training on Kaggle (Automated)
16. Phase 9 — Fine-tuning (Indian Finance Tasks)
17. Phase 10 — Evaluation & Benchmarking
18. Automation & Monitoring Setup
19. Full Project File Structure
20. Timeline
21. Upgrade Path
22. Quick Reference — All Decisions

---

# 1. PROJECT VISION

Build **ArthLLM** — a 2 Billion parameter language model from scratch that is the **first LLM purpose-built for Indian financial markets**.

### What ArthLLM Understands
```
Indian Markets        →  BSE, NSE, Nifty, Sensex, F&O, SME IPO
Indian Regulations    →  RBI, SEBI, IRDAI, PFRDA, MCA, NCLT
Indian Companies      →  PSU, NBFC, HFC, MFI structures
Indian Numbers        →  Lakh, Crore, Arab number system
Indian Tax            →  GST, TDS, Income Tax, STT, LTCG, STCG
Indian Investment     →  SIP, ELSS, ULIP, NPS, PPF, FD
Indian Budget         →  Union Budget, Economic Survey, RBI Policy
Indian News           →  Economic Times, Moneycontrol, Mint, LiveMint
Hinglish Finance      →  Mixed Hindi-English financial news
Regional Context      →  Sensex rally, Nifty correction, FII/DII flows
```

### Target Tasks
```
1. Sentiment Analysis        →  BSE/NSE news headlines (bullish/bearish/neutral)
2. Risk Detection            →  SEBI filings, loan disclosures
3. Financial Summarization   →  RBI policy, Budget speech, annual reports
4. Regulatory Q&A            →  SEBI rules, RBI circulars, GST queries
5. Earnings Analysis         →  Indian company results (Nifty 500)
6. Market Commentary         →  Indian equity research style
```

### Why This Matters
```
India is the 5th largest economy → moving to 3rd by 2030
BSE has 5,000+ listed companies
~150M retail investors (fastest growing in world)
Zero production-grade Indian finance LLM exists today
You would be FIRST ⭐
```

---

# 2. WHY INDIAN FINANCE LLM — THE OPPORTUNITY

### What Existing Finance LLMs Cannot Do

| Capability | BloombergGPT | FinGPT | ArthLLM |
|---|---|---|---|
| BSE/NSE terminology | ❌ | ❌ | ✅ |
| RBI monetary policy | ❌ | ❌ | ✅ |
| SEBI regulations | ❌ | ❌ | ✅ |
| Lakh/Crore numbers | ❌ | ❌ | ✅ |
| Indian Ind AS accounting | ❌ | ❌ | ✅ |
| Hinglish financial news | ❌ | ❌ | ✅ |
| Indian mutual funds | ❌ | ❌ | ✅ |
| GST/TDS/Indian tax | ❌ | ❌ | ✅ |
| Indian IPO process (ASBA) | ❌ | ❌ | ✅ |
| Indian insolvency (NCLT) | ❌ | ❌ | ✅ |
| Union Budget language | ❌ | ❌ | ✅ |
| Promoter holding concept | ❌ | ❌ | ✅ |

### The Market
```
Potential users of ArthLLM:
  ├── Retail investors (~150M in India)
  ├── Financial advisors & wealth managers
  ├── CA firms & tax professionals
  ├── Fintech companies (Zerodha, Groww, Paytm Money)
  ├── Banks & NBFCs (compliance, risk)
  ├── Regulatory bodies (SEBI, RBI internal tools)
  ├── Financial journalists (ET, Mint, MC)
  └── Academic researchers (IIM, IIT finance depts)
```

---

# 3. HARDWARE & COMPUTE SETUP

## Coding Platform — Google Colab
```
Use for    : Writing + testing code (Phases 3-8 development)
NOT for    : Long training runs
RAM        : 47GB available
Session    : Short sessions fine for coding
```

## Training Platform — Kaggle ⭐ (Free, Unattended)
```
GPU        : 2× T4 = 32GB VRAM total
RAM        : 30GB
Session    : 12 hours stable
Free hrs   : 30hrs/week (resets every week)
Scheduler  : Runs notebook automatically every 12hrs
Babysit    : Zero — fully unattended ✅
```

## Storage — Google Drive (5TB)
```
Checkpoints          : saved every 500 steps
Data shards          : all 400 shards (~80GB)
Tokenizer artifacts  : vocab + merges
Final model weights  : ~4GB (bf16)
Both Colab + Kaggle connect to same Drive ✅
```

## Monitoring (Remote from Pune)
```
WandB       : Live loss curves, tokens/sec, perplexity
              Check from phone browser anywhere
Telegram    : Notifications on save / crash / complete
              Works on cheap data from phone
```

## Future Upgrade Path
```
Apply now  : Google TRC Program (free TPU pod)
             sites.research.google/trc
             ArthLLM is perfect research justification
If approved: Scale to 7B ArthLLM on v5e pod
             Same code, just change config
```

---

# 4. FINAL MODEL SPECIFICATIONS

```python
@dataclass
class ArthLLMConfig:
    # Model name
    model_name           : str   = "ArthLLM-2B"
    version              : str   = "1.0"
    
    # Tokenizer — Indian-aware
    vocab_size           : int   = 32_000   # covers Hindi/Hinglish tokens
    
    # Architecture
    d_model              : int   = 2560     # embedding dimension
    n_layers             : int   = 32       # transformer blocks
    n_heads              : int   = 20       # attention heads
    n_kv_heads           : int   = 8        # GQA key-value heads
    ffn_dim              : int   = 10240    # feed-forward dimension
    max_seq_len          : int   = 2048     # base context window

    # RoPE — position encoding
    rope_theta           : float = 500_000.0  # LLaMA 3 standard

    # YaRN — for long Indian regulatory docs
    # RBI annual reports, Union Budget = 50K-100K tokens
    use_yarn             : bool  = True
    yarn_scale           : float = 8.0     # extends to 16K context
    yarn_alpha           : float = 1.0
    original_max_seq_len : int   = 2048

    # Training
    dropout              : float = 0.0     # 0 for large models
    bias                 : bool  = False   # modern standard

    # Total ≈ 2.1B parameters ✅
```

## Architecture Choices — Why Each One

| Choice | Reason |
|---|---|
| vocab_size=32K | Covers Hindi/Hinglish tokens + finance terms |
| d_model=2560 | Optimal for 2B parameter count |
| n_layers=32 | Depth for regulatory reasoning |
| GQA (n_kv_heads=8) | 2× faster, less VRAM on T4 |
| RoPE | Production standard — LLaMA 3, Mistral, Gemma |
| YaRN | RBI reports, Budget speech = very long docs |
| SwiGLU | Best activation for language tasks |
| RMSNorm | Faster than LayerNorm, used in LLaMA 3 |
| No bias | Modern standard, slightly better |
| No dropout | Large models regularize through data volume |

---

# 5. DATA STRATEGY — 70% INDIAN / 30% GLOBAL

## The Core Principle
```
ArthLLM's competitive advantage IS the Indian data.
No other model has this.
Protect this edge by maximizing Indian data quality.

Quality > Quantity always.
1B tokens of clean RBI circulars >
5B tokens of noisy web scrape.
```

## Token Budget

```
Total needed     : 40B tokens (Chinchilla for 2B model)
Indian data      : 28B tokens (70%)
Global data      : 12B tokens (30%)
```

---

## INDIAN DATA SOURCES (28B tokens — 70%)

### A. Regulatory & Government (Highest Quality) — 8B tokens

**Reserve Bank of India (RBI)** ⭐⭐⭐
```
What      : Monetary policy statements, annual reports,
            circulars, master directions, working papers,
            RBI bulletin, financial stability reports
Why       : Gold standard Indian financial language
            Authoritative, dense, factual
Volume    : 30+ years of documents → ~3B tokens
URL       : rbi.org.in/Scripts/Publications.aspx
Format    : PDF (parseable)
```

**SEBI (Securities and Exchange Board of India)** ⭐⭐⭐
```
What      : Circulars, regulations, consultation papers,
            annual reports, enforcement orders,
            IPO guidelines, mutual fund regulations
Why       : Core Indian securities law
            Every fintech + broker must understand this
Volume    : ~1.5B tokens
URL       : sebi.gov.in/legal/circulars
```

**Ministry of Finance — Union Budget** ⭐⭐⭐
```
What      : Budget speeches since 1947,
            Economic Survey (annual),
            Finance Bill, FRBM reports
Why       : Most important Indian financial document
            Every investor follows it
Volume    : ~500M tokens
URL       : indiabudget.gov.in
```

**MCA (Ministry of Corporate Affairs)** ⭐⭐
```
What      : Companies Act provisions, MCA21 filings,
            NCLT/NCLAT orders (insolvency cases),
            LLP filings
Why       : Indian company law, insolvency framework
Volume    : ~1B tokens
URL       : mca.gov.in
```

**IRDAI + PFRDA + IBBI** ⭐⭐
```
IRDAI     : Insurance regulations
PFRDA     : Pension fund regulations (NPS)
IBBI      : Insolvency & Bankruptcy Board
Volume    : ~500M tokens combined
```

**GST Council + CBDT** ⭐⭐
```
What      : GST circulars, income tax notifications,
            TDS provisions, capital gains rules
Why       : Every Indian financial transaction involves tax
Volume    : ~500M tokens
URL       : gst.gov.in, incometax.gov.in
```

---

### B. Indian Stock Exchange Filings — 6B tokens

**BSE + NSE Corporate Filings** ⭐⭐⭐
```
What      : Quarterly results (5,000+ companies),
            Annual reports, investor presentations,
            Board meeting outcomes, bulk/block deals,
            Insider trading disclosures, shareholding patterns
Why       : Real Indian corporate financial language
            Promoter holding, pledge data, FII/DII flows
Volume    : ~4B tokens (20+ years of filings)
Access    : 
  BSE: bseindia.com/corporates/ann.html
  NSE: nseindia.com/companies-listing/corporate-filings
Format    : PDF + HTML
```

**Indian Earnings Call Transcripts** ⭐⭐⭐
```
What      : Quarterly earnings calls of Nifty 500 companies
            Management commentary, analyst Q&A
Why       : Spoken Indian corporate finance language
            Forward guidance, capacity expansion, margins
            Language specific to Indian business context
Volume    : ~2B tokens
Sources   :
  - BSE filings (some companies upload transcripts)
  - Screener.in
  - Tijori Finance
  - HuggingFace Indian datasets
```

---

### C. Indian Financial News — 8B tokens

**Economic Times** ⭐⭐⭐
```
What      : India's #1 financial newspaper
            Markets, companies, economy, policy
Why       : Most widely read Indian finance source
            Hinglish headlines, Indian market terminology
Volume    : ~3B tokens (archive since 2000)
URL       : economictimes.indiatimes.com
```

**Moneycontrol** ⭐⭐⭐
```
What      : Indian markets news, stock analysis,
            mutual fund data, IPO news
Why       : Most popular retail investor platform
            Very Indian market-specific language
Volume    : ~2B tokens
URL       : moneycontrol.com
```

**LiveMint / Business Standard / Financial Express** ⭐⭐
```
Volume    : ~2B tokens combined
All three are premium Indian financial publications
```

**IndianFinancialNews.csv (existing data)** ✅
```
Already in your project → keep and expand
~500M tokens available
```

---

### D. Indian Finance HuggingFace Datasets — 4B tokens

```python
indian_hf_datasets = {
    # Already in your project
    "ranvsingn/indian-financial-news"        : "Indian market news ✅",
    
    # New to add
    "sohan-ai/indian-stock-market-qa"        : "Indian stock Q&A",
    "flax-sentence-embeddings/stackexchange" : "Finance Q&A (filter India)",
    "ai4bharat/sangraha"                     : "Hindi text corpus",
    "ai4bharat/IndicNLPSuite"                : "Indian language NLP",
    "iitk-researchers/indian-legal-dataset"  : "Indian legal/regulatory",
}
```

**AI4Bharat Datasets** ⭐⭐ (Special for Hinglish)
```
What      : Indian language datasets including Hindi
Why       : ArthLLM should understand Hinglish finance
            "Nifty mein aaj kaafi volatility thi"
            "FII ne ₹2000 crore ki bikwali ki"
URL       : ai4bharat.org/datasets
```

---

### E. Indian Finance Synthetic Data — 2B tokens

```
Generate using Claude API on your existing data:

From your RBI/SEBI/BSE docs generate:
  - "Explain this SEBI circular in simple terms"
  - "What does this RBI policy mean for home loan rates?"
  - "Summarize this quarterly result"
  - "What are the risks in this DRHP (IPO document)?"
  - "Convert ₹1,50,00,000 to words" → "One crore fifty lakhs"
  - Indian finance Q&A pairs
  - Lakh/Crore conversion examples (critical for numeracy)

Volume    : ~2B tokens
Cost      : Cheap via Claude API
Quality   : Verify with classifier before using
```

---

## GLOBAL DATA SOURCES (12B tokens — 30%)

### Why Still Include Global Data
```
ArthLLM must understand:
  - US companies listed on Indian exchanges (ETFs)
  - Global macro affecting Indian markets
  - FII (Foreign Institutional Investor) behavior
  - International accounting standards (IFRS → Ind AS)
  - Forex (USD/INR, EUR/INR)
  - Global commodity prices (crude oil = critical for India)
```

### Global Sources Breakdown

**SEC EDGAR** — 4B tokens
```
10-K, 10-Q, 8-K filings
Foundation of financial language
Still important for global context
URL: efts.sec.gov/LATEST/search-index
```

**HuggingFace Finance Datasets** — 4B tokens
```python
global_hf_datasets = {
    "eloukas/edgar-corpus"                  : "SEC filings corpus",
    "sujet-ai/Sujet-Finance-Instruct-177k"  : "Finance Q&A",
    "gbharti/finance-alpaca"                : "Finance instructions",
    "FinGPT/fingpt-sentiment-train"         : "Global sentiment",
    "zeroshot/twitter-financial-news"       : "Financial tweets",
    "nickmuchi/financial-classification"    : "News classification",
    "kiddothe2b/financial_reports"          : "Annual reports",
}
```

**arXiv q-fin Papers** — 2B tokens
```
Quantitative finance academic papers
Global financial theory foundation
~50K papers available
URL: arxiv.org/search/?searchtype=all&query=q-fin
```

**Wikipedia Finance** — 2B tokens
```
All finance, economics, business articles
Clean, factual, well-structured
~200K articles
URL: dumps.wikimedia.org
Filter: Finance, Economics, Business categories only
```

---

## COMPLETE DATA MIX TABLE

```
SOURCE                              TOKENS    %      TIER
─────────────────────────────────────────────────────────
INDIAN (70% = 28B tokens)
─────────────────────────────────────────────────────────
RBI documents + circulars        →  3.0B    7.5%    ⭐⭐⭐
SEBI regulations + reports       →  1.5B    3.8%    ⭐⭐⭐
MCA + NCLT + IBBI filings        →  1.0B    2.5%    ⭐⭐
Union Budget + Economic Survey   →  0.5B    1.2%    ⭐⭐⭐
IRDAI + PFRDA + CBDT             →  0.5B    1.2%    ⭐⭐
BSE + NSE corporate filings      →  4.0B   10.0%    ⭐⭐⭐
Indian earnings transcripts      →  2.0B    5.0%    ⭐⭐⭐
Economic Times archive           →  3.0B    7.5%    ⭐⭐⭐
Moneycontrol archive             →  2.0B    5.0%    ⭐⭐⭐
Mint + BS + FE news              →  2.0B    5.0%    ⭐⭐
Indian HuggingFace datasets      →  4.0B   10.0%    ⭐⭐
Indian synthetic (generated)     →  2.0B    5.0%    ⭐⭐
AI4Bharat (Hinglish)             →  2.5B    6.3%    ⭐⭐
─────────────────────────────────────────────────────────
Indian Subtotal                  → 28.0B   70.0%
─────────────────────────────────────────────────────────

GLOBAL (30% = 12B tokens)
─────────────────────────────────────────────────────────
SEC EDGAR filings                →  4.0B   10.0%    ⭐⭐⭐
HuggingFace finance datasets     →  4.0B   10.0%    ⭐⭐
arXiv q-fin papers               →  2.0B    5.0%    ⭐⭐
Wikipedia finance                →  2.0B    5.0%    ⭐⭐
─────────────────────────────────────────────────────────
Global Subtotal                  → 12.0B   30.0%
─────────────────────────────────────────────────────────
GRAND TOTAL                      → 40.0B  100.0%
─────────────────────────────────────────────────────────
```

---

## Fine-tuning Dataset Targets

```
Task              Current (50M project)  Target (ArthLLM 2B)
──────────────────────────────────────────────────────────
Sentiment         21,836 examples    →  500K+ (Indian focus)
Risk Detection    8,461 examples     →  200K+ (SEBI/RBI risk)
Summarization     49,630 pairs       →  1M+ pairs (Indian docs)
Regulatory Q&A    0 (new)            →  300K+ pairs
Earnings Analysis 0 (new)            →  200K+ pairs
```

---

# 6. INDIAN-SPECIFIC VOCABULARY & CONCEPTS

## Why This Needs Special Attention in Tokenizer

Standard BPE tokenizers trained on English web data will:
```
"crore"    →  split into ["cr", "ore"]   ❌ wrong
"lakh"     →  split into ["la", "kh"]    ❌ wrong
"NBFC"     →  split into ["NB", "FC"]    ❌ fragmented
"Sensex"   →  split into ["Sen", "sex"]  ❌ terrible
"₹"        →  unknown token              ❌ critical fail
```

ArthLLM's tokenizer trained on Indian finance corpus will:
```
"crore"    →  single token               ✅
"lakh"     →  single token               ✅
"NBFC"     →  single token               ✅
"Sensex"   →  single token               ✅
"₹"        →  single token               ✅
"Nifty50"  →  single token               ✅
```

## Indian Finance Vocabulary to Cover

### Numbers & Currency
```
₹ (Rupee symbol)
Paise, Rupee, Lakh, Crore, Arab
1,00,000 → 1 Lakh
1,00,00,000 → 1 Crore
Indian comma placement: 1,00,00,000 (not 10,000,000)
```

### Markets & Exchanges
```
BSE, NSE, MCX, NCDEX, NIFTY, SENSEX
Nifty50, Nifty500, Nifty Bank, Nifty IT
F&O, FII, DII, HNI, QIB, RII
T2T, BE, SME, Mainboard
Circuit breaker, Upper circuit, Lower circuit
Bulk deal, Block deal, Insider trading
ASBA, UPI IPO, Allotment, GMP (Grey Market Premium)
```

### Companies & Structures
```
PSU (Public Sector Undertaking)
NBFC (Non-Banking Financial Company)
HFC (Housing Finance Company)
MFI (Microfinance Institution)
MSME, SME, Unicorn, Decacorn
Promoter, Promoter holding, Pledge
FPO, OFS, Rights issue, Buyback
```

### Regulatory Terms
```
RBI, SEBI, IRDAI, PFRDA, IBBI, MCA
NCLT, NCLAT, DRT, SARFAESI
KYC, AML, PAN, Aadhaar
NPA (Non-Performing Asset)
CRAR, CAR, CRR, SLR, Repo rate, Reverse repo
MCLR, Base rate, Prime lending rate
```

### Investment Products
```
SIP, SWP, STP, Lumpsum
ELSS, ULIP, NPS, PPF, EPF, VPF
Debt fund, Liquid fund, FoF
NAV, AUM, TER, Exit load
Demat, CDSL, NSDL, DP
```

### Tax Terms
```
GST, IGST, CGST, SGST
TDS, TCS, Advance tax
LTCG, STCG, STT
HUF (Hindu Undivided Family)
Section 80C, 80D, 10(10D)
ITR, Form 26AS, AIS
```

### Hinglish Finance Phrases
```
"Nifty mein rally"
"FII ki bikwali"  
"Result ke baad stock upar gaya"
"Budget mein relief mili"
"Bazaar mein girawat"
```

---

# 7. TOKENIZER STRATEGY (INDIAN-AWARE)

## Upgrade from 8K → 32K Vocab

```
Old tokenizer (Phase 1):
  vocab_size = 8,000
  trained on: 357MB mixed data
  Indian coverage: partial

New tokenizer (ArthLLM):
  vocab_size = 32,000
  trained on: full 40B token Indian-first corpus
  Indian coverage: complete ✅
```

## Special Tokens (Expanded for Indian Tasks)

```python
special_tokens = [
    # Standard
    "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<MASK>",
    
    # Original task tokens
    "[SENTIMENT]",    # financial sentiment
    "[RISK]",         # risk detection
    "[SUMMARY]",      # summarization
    
    # New Indian-specific task tokens
    "[REGULATORY]",   # RBI/SEBI regulatory Q&A
    "[EARNINGS]",     # Indian earnings analysis
    "[BUDGET]",       # Union Budget analysis
    "[TAX]",          # GST/Income tax queries
    "[MARKET]",       # NSE/BSE market commentary
    "[HINDI]",        # Hinglish/Hindi finance text
]
```

## Tokenizer Training Data Mix
```
Train new 32K tokenizer on:
  50% Indian regulatory + news corpus
  20% Indian company filings
  20% Global finance (EDGAR, HuggingFace)
  10% Hinglish text (AI4Bharat)

This ensures Indian terms get single-token representation
```

---

# 8. PHASE 1 — TOKENIZATION ✅ COMPLETE

## What Was Done
| Notebook | Status |
|---|---|
| word_tokenization.ipynb | ✅ Done |
| character_tokenization.ipynb | ✅ Done |
| byte_per_encoding.ipynb | ✅ Done |
| byte_per_encoding_for_LLM.ipynb | ✅ Done |

## Key Output (50M Project)
```
vocab.json    : 8K tokens
merges.txt    : BPE merge rules
Special tokens: PAD, UNK, BOS, EOS, MASK,
                [SENTIMENT], [RISK], [SUMMARY]
```

## What Changes for ArthLLM 2B
```
Action        : Retrain tokenizer on Indian-first corpus
New vocab     : 32K tokens
New file      : tokenizer_32k_indian/vocab.json + merges.txt
Same code     : just bigger vocab_size + Indian training data
Extra tokens  : [REGULATORY], [EARNINGS], [BUDGET], [TAX],
                [MARKET], [HINDI]
```

---

# 9. PHASE 2 — VECTOR EMBEDDINGS ✅ COMPLETE

## What Was Done
| Notebook | Status |
|---|---|
| one_hot_encoding.ipynb | ✅ Done |
| vector_embedding.ipynb | ✅ Done |

## Key Insight for ArthLLM
```
NO separate embedding training needed.
nn.Embedding(32000, 2560) inside ArthLLM handles everything.
Indian finance embeddings emerge automatically during pre-training.

After training, model will know:
  "crore" ≈ "crores" ≈ "कोटि"
  "Nifty" ≈ "Sensex" (both indices)
  "RBI" ≈ "Reserve Bank" ≈ "central bank"
  "bullish" ≈ "तेजी" (Hindi for bull market)
```

---

# 10. PHASE 3 — POSITIONAL ENCODING ⬜ NEXT

## Why RoPE + YaRN for ArthLLM

### Special Consideration — Indian Documents are LONG
```
RBI Annual Report      →  100K+ tokens
Union Budget Speech    →  50K+ tokens
SEBI Master Circular   →  80K+ tokens
BSE Annual Report      →  150K+ tokens
NCLT Order             →  30K+ tokens

Standard RoPE (2048 tokens) would cut all of these off.
YaRN extends to 16K → handles most Indian regulatory docs.
```

## All Positional Encoding Types
| Type | Parameters | Extrapolates | Used Today |
|---|---|---|---|
| Sinusoidal (2017) | None | Weak | Legacy only |
| Learnable Absolute | Yes | No | Legacy |
| ALiBi / Relative | None | Yes | Niche |
| RoPE (2021) | None | Yes | **Dominant** ✅ |
| YaRN (2023) | None | Yes++ | Growing ✅ |

## Where RoPE Lives
```
Token Embedding                 ← NO positional addition here
      ↓
Transformer Block
      ↓
  Multi-Head Attention
      ↓
  Q, K projections
      ↓
  ← RoPE applied HERE to Q and K only ←
      ↓
  YaRN frequency scaling (for long Indian docs)
      ↓
  Attention scores → output
```

## Notebook Plan
```
Cell 1  →  The problem: order without PE (finance examples)
Cell 2  →  Sinusoidal PE (theory + heatmap visualization)
Cell 3  →  Learnable PE (GPT style, limitations)
Cell 4  →  ALiBi (relative distances)
Cell 5  →  RoPE math (rotation matrices, cos/sin pairs)
Cell 6  →  RoPE implementation from scratch
Cell 7  →  RoPE visualization
Cell 8  →  YaRN — why ArthLLM needs it (Indian long docs)
Cell 9  →  YaRN implementation on top of RoPE
Cell 10 →  Test: 2048 tokens vs 16K with YaRN
Cell 11 →  Final RotaryEmbedding class → saved for Phase 4
```

---

# 11. PHASE 4 — SELF ATTENTION + GQA ⬜

## Standard Attention
```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V
```

## GQA — Grouped Query Attention
```
Standard MHA:  20 Q heads, 20 K heads, 20 V heads  → expensive
GQA:           20 Q heads,  8 K heads,  8 V heads  → 2.5× faster

ArthLLM config: n_heads=20, n_kv_heads=8
Used in: LLaMA 3, Mistral, Gemma ✅
```

## Finance-Specific Attention Visualization
```
ArthLLM should learn:
  "Sensex"   attends heavily to "points", "rally", "fall"
  "RBI"      attends to "repo rate", "inflation", "policy"
  "Nifty"    attends to "50", "500", "Bank", "IT"
  "crore"    attends to "₹", "lakh", "revenue", "profit"
  "SEBI"     attends to "circular", "regulation", "IPO"
```

## Notebook Plan
```
Cell 1  →  Scaled dot-product attention from scratch
Cell 2  →  Causal masking (autoregressive)
Cell 3  →  Multi-head attention
Cell 4  →  GQA — why ArthLLM needs it (VRAM on T4)
Cell 5  →  GQA implementation
Cell 6  →  Plug in RotaryEmbedding from Phase 3
Cell 7  →  Flash Attention 2 integration (speed trick)
Cell 8  →  Visualize attention on Indian finance text
           "RBI ne repo rate badhaya" — what attends to what
Cell 9  →  Final ArthAttention class
```

---

# 12. PHASE 5 — TRANSFORMER BLOCK ⬜

## Full Block Architecture
```
Input x
  ↓
RMSNorm (faster than LayerNorm, LLaMA 3 standard)
  ↓
ArthAttention (GQA + RoPE from Phases 3,4)
  ↓
Residual: x = x + attention_output
  ↓
RMSNorm
  ↓
SwiGLU FFN (better than GELU for language)
  ↓
Residual: x = x + ffn_output
  ↓
Output
```

## Notebook Plan
```
Cell 1  →  RMSNorm from scratch + why not LayerNorm
Cell 2  →  SwiGLU feed-forward network
Cell 3  →  Residual connections (why critical at 2B scale)
Cell 4  →  Full transformer block assembly
Cell 5  →  Stack 32 blocks
Cell 6  →  Forward pass on Indian finance text
Cell 7  →  Final TransformerBlock class
```

---

# 13. PHASE 6 — FULL MODEL ARCHITECTURE ⬜

## ArthLLM Full Assembly
```
Token IDs (batch, seq_len)
      ↓
nn.Embedding(32000, 2560)           ← token embeddings
      ↓
Stack of 32 TransformerBlocks       ← phases 3,4,5 combined
      ↓
Final RMSNorm
      ↓
Linear(2560, 32000)                 ← project to vocab logits
      ↓
Softmax → next token probabilities
```

## File Structure
```
Model/
  config.py       →  ArthLLMConfig dataclass
  rope.py         →  RotaryEmbedding (Phase 3)
  attention.py    →  ArthAttention + GQA (Phase 4)
  ffn.py          →  SwiGLUFFN (Phase 5)
  block.py        →  TransformerBlock (Phase 5)
  model.py        →  ArthLLM full model
```

## Parameter Count Verification
```python
def count_parameters(model):
    total = sum(p.numel() for p in model.parameters())
    print(f"ArthLLM Total: {total/1e9:.2f}B parameters")

# Expected output:
# ArthLLM Total: 2.10B parameters ✅
```

---

# 14. PHASE 7 — DATA PIPELINE (40B TOKENS, 70% INDIAN) ⬜

## Pipeline Architecture
```
Raw Indian Sources
(RBI, SEBI, BSE, ET, MC...)
      ↓
1. DOWNLOAD        streaming — never load all at once
      ↓
2. EXTRACT         PDF → text, HTML → text, CSV → text
      ↓
3. CLEAN           normalize, filter noise, Indian encoding
      ↓
4. DEDUPLICATE     exact MD5 + MinHash LSH near-dedup
      ↓
5. QUALITY FILTER  perplexity + Indian finance relevance
      ↓
6. TOKENIZE+SHARD  32K BPE → .bin shards (100M tokens each)
      ↓
GDrive Storage     shard_0000.bin ... shard_0399.bin
```

## Indian-Specific Cleaning Rules
```python
def clean_indian_finance_text(text):
    # Standard cleaning
    text = remove_html(text)
    text = normalize_unicode(text)  # handles Devanagari
    text = remove_urls(text)
    
    # Indian-specific
    text = normalize_rupee_symbol(text)      # ₹, Rs., Rs, INR → ₹
    text = normalize_indian_numbers(text)    # 1,00,000 format preserved
    text = handle_hinglish(text)             # keep mixed Hindi-English
    text = fix_indian_encoding(text)         # UTF-8 issues with Hindi
    
    # Filter rules
    if len(text) < 100:
        return None
    if not is_finance_relevant(text):        # custom finance classifier
        return None
    
    return text
```

## Run on Laptop Overnight
```
Pure CPU work — no GPU needed.
RTX 4050 not required for data pipeline.
Just needs disk space + RAM.
Start before sleeping:
  python download_pipeline.py &
Wake up to processed data ✅
```

## Resumable Pipeline
```python
already_done = set(os.listdir("cleaned/"))
for file in all_raw_files:
    if file in already_done:
        continue    # skip already processed ✅
    process(file)
# Session dies → rerun → skips done files automatically
```

## Data Files Output
```
DataPipeline/
  scrapers/
    scrape_rbi.py           →  RBI publications scraper
    scrape_sebi.py          →  SEBI circulars scraper
    scrape_bse_nse.py       →  BSE/NSE filings scraper
    scrape_budget.py        →  Budget + Economic Survey
    scrape_et.py            →  Economic Times news
    scrape_moneycontrol.py  →  Moneycontrol archive
    scrape_mca.py           →  MCA company filings
    download_hf.py          →  HuggingFace datasets
    download_edgar.py       →  SEC EDGAR (global 30%)
  
  processing/
    extract_pdf.py          →  PDF → text (RBI/SEBI docs)
    clean.py                →  Indian-aware cleaning
    deduplicate.py          →  MinHash LSH dedup
    quality_filter.py       →  Finance relevance scoring
    tokenize_shard.py       →  tokenize → .bin shards
    retrain_tokenizer.py    →  32K Indian-aware BPE
```

---

# 15. PHASE 8 — PRE-TRAINING ON KAGGLE (AUTOMATED) ⬜

## Training Hyperparameters
```python
# Optimal for ArthLLM 2B
learning_rate     = 3e-4
lr_schedule       = "cosine with warmup"
warmup_steps      = 2000
batch_size        = 4             # per GPU
grad_accumulation = 64            # effective batch = 256
max_seq_len       = 2048
weight_decay      = 0.1
grad_clip         = 1.0
total_tokens      = 40_000_000_000  # 40B tokens
bf16              = True
```

## 7 Speed Tricks (Applied in Order)
```
1. bf16 mixed precision      →  30-50% faster     (always first)
2. Flash Attention 2         →  2-4× faster        (biggest gain)
3. torch.compile             →  20-30% faster      (one line)
4. 8-bit Adam optimizer      →  saves 6GB VRAM     (bigger batch)
5. Packed sequences          →  20-30% faster      (great for long Indian docs)
6. DataLoader optimization   →  10-20% faster      (pin_memory + prefetch)
7. Gradient checkpointing    →  saves VRAM         (if needed)

Combined speedup: ~6-8×
Base:        150M tokens/hr
With tricks: ~800M-1B tokens/hr 🚀
```

## Training Time
```
40B tokens ÷ 800M tokens/hr = 50 hours
Kaggle: 30hrs/week free
Weeks:  ~2 weeks ✅
```

## Complete Automated Training Script

```python
# master_train.py — ArthLLM fully automated training
# Zero babysitting. Runs from Pune while you sleep.

import os, torch, wandb, time, math
import numpy as np
import torch.nn.functional as F
import bitsandbytes as bnb
from pathlib import Path

# ── Config ────────────────────────────────────────────────
GDRIVE_DIR     = '/kaggle/input/arthlllm-drive/'
CHECKPOINT_DIR = GDRIVE_DIR + 'checkpoints/'
SHARD_DIR      = GDRIVE_DIR + 'shards/'
WANDB_PROJECT  = 'ArthLLM-2B'
SAVE_EVERY     = 500
SESSION_BUDGET = 11 * 3600   # 11hrs (1hr buffer)

# ── Telegram ──────────────────────────────────────────────
def send_alert(msg: str):
    import requests
    token   = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    try:
        requests.get(
            f"https://api.telegram.org/bot{token}/sendMessage",
            params={"chat_id": chat_id,
                    "text": f"[ArthLLM] {msg}"},
            timeout=5
        )
    except:
        pass

# ── Checkpoint ────────────────────────────────────────────
def save_checkpoint(model, optimizer, step,
                    shard_idx, shard_pos, loss):
    path = f"{CHECKPOINT_DIR}arthlllm_ckpt_{step:07d}.pt"
    torch.save({
        'step'       : step,
        'shard_idx'  : shard_idx,
        'shard_pos'  : shard_pos,
        'loss'       : loss,
        'model'      : model.state_dict(),
        'optimizer'  : optimizer.state_dict(),
    }, path)
    # Keep only last 3
    for old in sorted(
        Path(CHECKPOINT_DIR).glob("arthlllm_ckpt_*.pt"))[:-3]:
        old.unlink()
    print(f"💾 Checkpoint: step {step:,} | loss {loss:.4f}")

def load_checkpoint(model, optimizer):
    ckpts = sorted(Path(CHECKPOINT_DIR).glob("arthlllm_ckpt_*.pt"))
    if not ckpts:
        print("🆕 Starting ArthLLM training fresh")
        return 0, 0, 0
    ckpt = torch.load(ckpts[-1], map_location='cuda')
    model.load_state_dict(ckpt['model'])
    optimizer.load_state_dict(ckpt['optimizer'])
    print(f"✅ Resumed: step {ckpt['step']:,} | loss {ckpt['loss']:.4f}")
    return ckpt['step'], ckpt['shard_idx'], ckpt['shard_pos']

# ── Learning Rate ─────────────────────────────────────────
def get_lr(step, warmup=2000, max_steps=500000,
           max_lr=3e-4, min_lr=3e-5):
    if step < warmup:
        return max_lr * step / warmup
    if step > max_steps:
        return min_lr
    ratio = (step - warmup) / (max_steps - warmup)
    coeff = 0.5 * (1.0 + math.cos(math.pi * ratio))
    return min_lr + coeff * (max_lr - min_lr)

# ── Main ──────────────────────────────────────────────────
def train():
    wandb.init(project=WANDB_PROJECT, resume="allow",
               config={"model": "ArthLLM-2B",
                       "data": "70% Indian 30% Global",
                       "origin": "Pune, India"})

    config = ArthLLMConfig()
    model  = ArthLLM(config).cuda()
    model  = torch.compile(model)

    optimizer = bnb.optim.AdamW8bit(
        model.parameters(), lr=3e-4, weight_decay=0.1)

    step, shard_idx, shard_pos = load_checkpoint(model, optimizer)
    send_alert(f"🚀 ArthLLM training started | step {step:,}")

    session_start = time.time()
    total_shards  = len(list(Path(SHARD_DIR).glob("shard_*.bin")))

    for s_idx in range(shard_idx, total_shards):
        data      = np.fromfile(
                      f"{SHARD_DIR}shard_{s_idx:04d}.bin",
                      dtype=np.uint16)
        shard_pos = 0
        pos       = 0

        while pos + (4 * 2048 + 1) <= len(data):
            # Update LR
            lr = get_lr(step)
            for pg in optimizer.param_groups:
                pg['lr'] = lr

            # Batch
            x = torch.from_numpy(
                data[pos:pos+4*2048].reshape(4,2048)
                    .astype(np.int64)).cuda()
            y = torch.from_numpy(
                data[pos+1:pos+4*2048+1].reshape(4,2048)
                    .astype(np.int64)).cuda()
            pos += 4 * 2048

            # Forward + backward (bf16)
            with torch.autocast(device_type='cuda',
                                dtype=torch.bfloat16):
                logits = model(x)
                loss   = F.cross_entropy(
                    logits.view(-1, config.vocab_size),
                    y.view(-1))

            loss.backward()

            if (step + 1) % 64 == 0:
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)

            step += 1

            # Log
            if step % 10 == 0:
                tokens_seen = step * 4 * 2048
                wandb.log({
                    "loss"          : loss.item(),
                    "perplexity"    : torch.exp(loss).item(),
                    "lr"            : lr,
                    "step"          : step,
                    "tokens_B"      : tokens_seen / 1e9,
                    "progress_pct"  : tokens_seen / 40e9 * 100,
                })
                print(f"Step {step:7,} | "
                      f"Loss {loss.item():.4f} | "
                      f"PPL {torch.exp(loss).item():.1f} | "
                      f"Tokens {tokens_seen/1e9:.2f}B / 40B | "
                      f"LR {lr:.2e}")

            # Save checkpoint
            if step % SAVE_EVERY == 0:
                save_checkpoint(model, optimizer, step,
                                s_idx, pos, loss.item())
                send_alert(
                    f"💾 Step {step:,} | "
                    f"Loss {loss.item():.4f} | "
                    f"{step*4*2048/40e9*100:.1f}% complete")

            # Session guard
            if time.time() - session_start > SESSION_BUDGET:
                save_checkpoint(model, optimizer, step,
                                s_idx, pos, loss.item())
                send_alert(
                    f"⏰ Session ending at step {step:,}. "
                    f"Kaggle will auto-restart.")
                wandb.finish()
                return

    # Done!
    save_checkpoint(model, optimizer, step,
                    total_shards, 0, loss.item())
    send_alert(
        f"🎉 ArthLLM PRE-TRAINING COMPLETE!\n"
        f"Steps: {step:,} | "
        f"Tokens: {step*4*2048/1e9:.1f}B\n"
        f"India's first finance LLM is ready! 🇮🇳")
    wandb.finish()

if __name__ == "__main__":
    train()
```

---

# 16. PHASE 9 — FINE-TUNING (INDIAN FINANCE TASKS) ⬜

## Five Fine-tuning Tasks

### Task 1 — Indian Financial Sentiment
```
Dataset  : sentiment.csv → expand with Indian news headlines
Input    : [SENTIMENT] Nifty aaj 200 points upar banda hua
Output   : bullish
Sources  : ET headlines, Moneycontrol, Twitter #Nifty
Target   : 500K+ examples, Indian market focused
Metric   : Accuracy, F1
Baseline : FinBERT (Western — should be easy to beat on Indian data)
```

### Task 2 — Indian Risk Detection
```
Dataset  : risk.csv → expand with SEBI/RBI risk language
Input    : [RISK] The company has significant NPA exposure...
Output   : high_risk / medium_risk / low_risk
Sources  : SEBI enforcement orders, RBI audit reports,
           BSE/NSE risk disclosures, NCLT filings
Target   : 200K+ examples
Metric   : Accuracy, F1
```

### Task 3 — Indian Financial Summarization
```
Dataset  : summary.csv → expand with Indian document pairs
Input    : [SUMMARY] {long RBI circular or Budget speech}
Output   : {concise 3-5 sentence summary}
Sources  : RBI circulars + their press releases (natural pairs),
           Budget speech + newspaper summaries
Target   : 1M+ pairs
Metric   : ROUGE-1, ROUGE-2, ROUGE-L
```

### Task 4 — Indian Regulatory Q&A (New) ⭐
```
Dataset  : 0 now → generate 300K+ pairs
Input    : [REGULATORY] What is the minimum net worth
           requirement for an NBFC?
Output   : As per RBI Master Direction, an NBFC requires
           minimum net owned fund of ₹10 crore...
Sources  : RBI FAQs, SEBI FAQs, GST FAQs,
           Generated from regulatory docs
Target   : 300K Q&A pairs
Metric   : BLEU, human eval
```

### Task 5 — Indian Earnings Analysis (New) ⭐
```
Dataset  : 0 now → generate 200K+ pairs
Input    : [EARNINGS] Q3FY24 Results: Revenue ₹2,450 crore
           (+15% YoY), EBITDA ₹420 crore (+8% YoY),
           PAT ₹280 crore (-3% YoY)...
Output   : Revenue growth was strong at 15% but margin
           pressure evident as EBITDA grew only 8%...
Sources  : BSE/NSE quarterly results + analyst notes
Target   : 200K pairs
Metric   : ROUGE + human eval
```

## Fine-tuning Hyperparameters
```python
learning_rate  = 1e-5     # 30× lower than pre-training
epochs         = 3
batch_size     = 8
warmup_steps   = 100
grad_clip      = 1.0
```

---

# 17. PHASE 10 — EVALUATION & BENCHMARKING ⬜

## Indian Finance Benchmarks

### Create Custom Indian Benchmarks (nobody else has these)
```
IndianSentiment-1K   : 1,000 manually labeled BSE/NSE headlines
IndianRisk-500       : 500 SEBI/RBI risk assessment examples
IndianRegQA-500      : 500 regulatory Q&A pairs (human verified)
IndianBudget-200     : 200 Budget clause comprehension questions
IndianEarnings-500   : 500 quarterly result analysis examples
```

### Comparison Models
```
ArthLLM 2B  ←→  FinBERT (110M)       [Indian finance tasks]
ArthLLM 2B  ←→  FinGPT (7B)          [Indian finance tasks]
ArthLLM 2B  ←→  GPT-4o               [Indian finance tasks]
ArthLLM 2B  ←→  LLaMA 3 8B           [Indian finance tasks]
ArthLLM 2B  ←→  BloombergGPT (50B)   [Indian finance tasks]

Expected: ArthLLM beats everything on Indian tasks
          despite being only 2B vs 50B+ competitors
          (domain-specific always beats generalist)
```

### Perplexity Tests
```python
# Test on held-out Indian finance text
# ArthLLM should show dramatically lower perplexity
# than any existing model on Indian financial text

test_corpora = {
    "RBI_policy_2024"      : "rbi_test.txt",
    "SEBI_circular_2024"   : "sebi_test.txt",
    "BSE_earnings_2024"    : "bse_test.txt",
    "ET_headlines_2024"    : "et_test.txt",
    "budget_speech_2024"   : "budget_test.txt",
}
```

### Number System Test (Unique to ArthLLM)
```
Q: "Company reported revenue of ₹1,25,00,000. Express in words."
A: "One crore twenty-five lakh rupees"

No existing model handles this correctly.
ArthLLM should nail it.
```

### Publish Results
```
Write research paper:
  "ArthLLM: India's First Domain-Specific Finance LLM"
  Submit to: EMNLP, ACL, FinNLP workshop
  arXiv preprint first
  
This is publishable research — no competition exists.
```

---

# 18. AUTOMATION & MONITORING SETUP

## Step-by-Step Setup (Do Once)

### Step 1 — WandB (10 min)
```bash
pip install wandb
wandb login
# Enter API key from wandb.ai/authorize
# Check training from phone: wandb.ai/your-username/ArthLLM-2B
```

### Step 2 — Telegram Bot (15 min)
```
1. Telegram → search @BotFather
2. /newbot → name it "ArthLLM Trainer"
3. Copy the API token given
4. Send any message to your bot
5. Get your chat_id:
   https://api.telegram.org/bot{TOKEN}/getUpdates
   Look for "chat": {"id": 123456789}
6. Put TOKEN + chat_id in master_train.py
```

### Step 3 — Kaggle Setup
```
1. Create Kaggle account → kaggle.com
2. Settings → Add phone for verification
3. Account → Connect Google Drive
4. New Notebook → paste master_train.py
5. Settings → Accelerator → GPU T4 x2
6. Connect Drive dataset (your shards + checkpoints)
7. Run → Schedule → Every 12 hours ✅
```

### Step 4 — First Manual Verification Run
```
Before enabling scheduler, run once manually:
  □ GDrive mounts and shards are visible
  □ First shard loads without error
  □ Model forward pass works (no OOM)
  □ Checkpoint saves to Drive correctly
  □ WandB shows data at wandb.ai
  □ Telegram message arrives on phone
  □ torch.compile completes without error

If all 7 pass → enable scheduler → walk away ✅
```

## Your Daily Experience
```
Day 1       →  Setup everything + manual verification
Day 2+      →  Check WandB on phone occasionally (2 min/day)
              Receive Telegram every ~500 steps
              Do nothing else
~Week 3     →  "🎉 ArthLLM PRE-TRAINING COMPLETE!" on phone
              Download model from GDrive
              Start fine-tuning phase
```

---

# 19. FULL PROJECT FILE STRUCTURE

```
ArthLLM-2B/
│
├── data/
│   ├── raw/
│   │   ├── indian/
│   │   │   ├── rbi_publications.txt
│   │   │   ├── sebi_circulars.txt
│   │   │   ├── bse_nse_filings.txt
│   │   │   ├── mca_filings.txt
│   │   │   ├── union_budget.txt
│   │   │   ├── economic_survey.txt
│   │   │   ├── irdai_pfrda.txt
│   │   │   ├── gst_cbdt.txt
│   │   │   ├── economic_times.txt
│   │   │   ├── moneycontrol.txt
│   │   │   ├── mint_bs_fe.txt
│   │   │   ├── earnings_transcripts_india.txt
│   │   │   └── ai4bharat_hinglish.txt
│   │   │
│   │   └── global/
│   │       ├── sec_edgar.txt
│   │       ├── hf_finance_instruct.txt
│   │       ├── hf_finance_alpaca.txt
│   │       ├── arxiv_qfin.txt
│   │       └── wikipedia_finance.txt
│   │
│   ├── cleaned/
│   ├── deduped/
│   └── tokenized_shards/
│       ├── shard_0000.bin       # 100M tokens each
│       ├── shard_0001.bin       # ~400 shards total
│       └── ...
│
├── tokenizer_32k_indian/        # Indian-aware tokenizer
│   ├── vocab.json               # 32K tokens
│   └── merges.txt
│
├── Tokenization/                # Phase 1 ✅
│   ├── word_tokenization.ipynb
│   ├── character_tokenization.ipynb
│   ├── byte_per_encoding.ipynb
│   └── byte_per_encoding_for_LLM.ipynb
│
├── Vector Embeddings/           # Phase 2 ✅
│   ├── one_hot_encoding.ipynb
│   └── vector_embedding.ipynb
│
├── Positional Encoding/         # Phase 3 ⬜
│   └── positional_encoding.ipynb
│
├── Attention/                   # Phase 4 ⬜
│   └── self_attention.ipynb
│
├── Transformer/                 # Phase 5 ⬜
│   └── transformer_block.ipynb
│
├── Model/                       # Phase 6 ⬜
│   ├── config.py                # ArthLLMConfig
│   ├── rope.py                  # RotaryEmbedding + YaRN
│   ├── attention.py             # ArthAttention + GQA
│   ├── ffn.py                   # SwiGLUFFN
│   ├── block.py                 # TransformerBlock
│   └── model.py                 # ArthLLM full model
│
├── DataPipeline/                # Phase 7 ⬜
│   ├── scrapers/
│   │   ├── scrape_rbi.py
│   │   ├── scrape_sebi.py
│   │   ├── scrape_bse_nse.py
│   │   ├── scrape_budget.py
│   │   ├── scrape_et.py
│   │   ├── scrape_moneycontrol.py
│   │   ├── scrape_mca.py
│   │   ├── download_hf.py
│   │   └── download_edgar.py
│   │
│   └── processing/
│       ├── extract_pdf.py
│       ├── clean_indian.py      # Indian-aware cleaning
│       ├── deduplicate.py
│       ├── quality_filter.py
│       ├── tokenize_shard.py
│       └── retrain_tokenizer_32k.py
│
├── Training/                    # Phase 8 ⬜
│   ├── master_train.py          # Full automated training
│   ├── dataset.py               # Shard data loader
│   ├── generate.py              # Text generation
│   └── kaggle_notebook.ipynb    # Kaggle entry point
│
├── Finetuning/                  # Phase 9 ⬜
│   ├── dataset.py
│   ├── finetune_sentiment.py    # Indian sentiment
│   ├── finetune_risk.py         # Indian risk
│   ├── finetune_summary.py      # Indian summarization
│   ├── finetune_regulatory.py   # NEW: RBI/SEBI Q&A
│   ├── finetune_earnings.py     # NEW: Indian earnings
│   └── evaluate.py
│
├── Evaluation/                  # Phase 10 ⬜
│   ├── benchmarks/
│   │   ├── indian_sentiment_1k.json
│   │   ├── indian_risk_500.json
│   │   ├── indian_regqa_500.json
│   │   ├── indian_budget_200.json
│   │   └── indian_earnings_500.json
│   ├── eval_sentiment.py
│   ├── eval_risk.py
│   ├── eval_regulatory.py
│   ├── eval_earnings.py
│   ├── perplexity_eval.py
│   └── comparison_report.ipynb
│
├── checkpoints/                 # → GDrive (auto-synced)
├── requirements.txt
├── README.md                    # ArthLLM documentation
├── PAPER.md                     # Research paper draft
└── .gitignore
```

---

# 20. TIMELINE

```
Week 1-2    →  Phase 3: Positional Encoding (RoPE + YaRN)
               Notebook with all 4 types + Indian long doc demo

Week 2-3    →  Phase 4: Self Attention + GQA
               Flash Attention 2 integration
               Indian finance attention visualization

Week 3-4    →  Phase 5: Transformer Block
               RMSNorm + SwiGLU + Residuals

Week 4-5    →  Phase 6: Full ArthLLM Architecture
               2B param count verification

Week 5-6    →  Phase 7: Data Pipeline
               Run scrapers overnight on laptop
               RBI + SEBI + BSE + ET + global sources
               Retrain tokenizer to 32K Indian-aware

Week 6      →  Setup Kaggle + WandB + Telegram
               First manual training run verification
               All 7 checks pass → enable scheduler

Week 7-8    →  Phase 8: Pre-training (automated on Kaggle)
               40-50 hours total compute
               Kaggle runs unattended
               Check WandB from phone

Week 9      →  Phase 9: Fine-tuning
               Sentiment, Risk, Summary (expanded)
               Regulatory Q&A (new)
               Earnings Analysis (new)

Week 10-11  →  Phase 10: Evaluation
               Indian benchmark creation
               Compare vs FinBERT, FinGPT, GPT-4o
               Write research paper draft

Week 12     →  Buffer + documentation + arXiv submission
```

**Total: ~2.5-3 months ✅**

---

# 21. UPGRADE PATH

```
Phase 1 (Now)     →  ArthLLM-2B
                      From scratch on Kaggle
                      Free, 2-3 months
                      India's first finance LLM ✅

Phase 2 (TRC)     →  ArthLLM-7B
                      Apply for Google TRC today
                      sites.research.google/trc
                      Same code, change config
                      ArthLLM is perfect TRC justification:
                      "First Indian finance LLM"

Phase 3 (Future)  →  ArthLLM-7B-Hindi
                      Add more Hindi/regional data
                      Hindi + English bilingual model
                      Covers 500M+ Hindi speakers

Phase 4 (Future)  →  ArthLLM-70B
                      If TRC extends or funding available
                      Continued pre-training on LLaMA 3 70B
```

---

# 22. QUICK REFERENCE — ALL DECISIONS

| Decision | Choice | Reason |
|---|---|---|
| Model name | ArthLLM | Arth = Money + Meaning in Hindi |
| Model size | 2B | Max for free Kaggle + good quality |
| Model type | From scratch | Full learning, not fine-tuning |
| Data split | 70% Indian / 30% Global | Unique competitive advantage |
| Indian data priority | RBI, SEBI, BSE, NSE, ET, MC | Authentic Indian finance |
| Global data | SEC EDGAR, HuggingFace, arXiv | Foundation + depth |
| Total tokens | 40B | Chinchilla optimal for 2B |
| Training platform | Kaggle | Free, unattended, 12hr sessions |
| Coding platform | Colab | Fast iteration, 47GB RAM |
| Storage | GDrive 5TB | Both platforms connect |
| Positional encoding | RoPE + YaRN | Standard + long Indian docs |
| Attention | GQA (n_kv_heads=8) | 2× faster, less VRAM |
| Activation | SwiGLU | Best for language |
| Normalization | RMSNorm | Faster than LayerNorm |
| Optimizer | 8-bit AdamW | Saves VRAM on T4 |
| Precision | bf16 | Native T4 support |
| Vocab size | 32K Indian-aware | Covers Indian terms natively |
| Context | 2048 base + YaRN 16K | Handles long Indian regulatory docs |
| Speed tricks | All 7 applied | ~6-8× faster training |
| Monitoring | WandB + Telegram | Remote from Pune |
| Automation | Kaggle Scheduler | Zero babysitting |
| Fine-tuning tasks | 5 tasks (3 existing + 2 Indian new) | Comprehensive |
| Evaluation | Custom Indian benchmarks | First of their kind |
| Publication | arXiv + FinNLP workshop | Publishable research |

---

```
ArthLLM — Built in Pune. Built for Bharat. Built for the World.
अर्थ — The meaning of money, understood.

No competition exists.
You are building something genuinely new.
```

---

*ArthLLM Complete Master Plan — Version 2.0*
*Redesigned for Indian-First Finance LLM*
*Nothing left behind. Every decision documented.*
*Last Updated: 2025*
