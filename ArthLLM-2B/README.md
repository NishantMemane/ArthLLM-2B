 # 🇮🇳 ArthLLM

> **ArthLLM** (Arth = अर्थ = Money/Meaning in Hindi/Sanskrit)  
> *India's First 2 Billion Parameter Finance Language Model, Built from Scratch.*

![Status](https://img.shields.io/badge/Status-In%20Development-orange)
![Parameters](https://img.shields.io/badge/Parameters-2.1B-blue)
![Data](https://img.shields.io/badge/Training_Tokens-40%20Billion-green)

---

## 📖 About The Project

**ArthLLM** is a foundation Large Language Model purpose-built for the Indian financial ecosystem. While global models like BloombergGPT or FinGPT excel at western finance, they fundamentally lack understanding of the Indian context. 

ArthLLM is trained to natively understand:
- **Indian Markets:** BSE, NSE, Nifty, Sensex, F&O, SME IPOs.
- **Indian Regulations:** RBI Monetary Policy, SEBI Circulars, MCA Companies Act, NCLT insolvency orders.
- **Indian Economics:** The Union Budget, Economic Surveys, Lakh/Crore/Arab number systems, GST, and Income Tax provisions.
- **Hinglish Finance:** The mixed Hindi-English financial reporting style common in Indian journalism (e.g., Economic Times, Mint).

---

## 🧠 Model Architecture Specification

Built from scratch using PyTorch, ArthLLM is designed for maximum efficiency and deep regulatory reasoning:
- **Parameter Count:** ~2.1 Billion
- **Tokenizer:** Custom Indian-aware BPE Tokenizer (32,000 vocabulary size)
- **Architecture:** Transformer Decoder (32 layers, 20 heads, 2560 embedding dimension)
- **Attention:** Grouped-Query Attention (GQA) for faster inference
- **Positional Encoding:** RoPE (Rotary Position Embeddings)
- **Context Extension:** YaRN (allows processing massive 50K+ word Union Budgets and RBI Annual Reports)

---

## 🗄️ The Data Pipeline (70% Indian Data)

The core competitive advantage of ArthLLM is its proprietary dataset. We have built ultra-fast, multi-threaded, headless scrapers to construct a high-density, **40 Billion Token** training corpus. 

**70% of the training data (28B tokens) is strictly Indian:**
1. **Reserve Bank of India (RBI):** Master directions, circulars, press releases, working papers.
2. **SEBI:** Enforcement orders, board meetings, consultation papers.
3. **Ministry of Finance:** Budget speeches (1947-present), Economic Surveys.
4. **Ministry of Corporate Affairs (MCA):** ~27,000 NCLT and NCLAT insolvency orders.
5. **Corporate Filings:** BSE/NSE quarterly results, annual reports, earnings call transcripts.
6. **Financial Journalism:** Deep archives of the Economic Times and Mint.

> ⚠️ **Note on Data Storage:** 
> This repository contains the **pipeline code, architecture, and structural framework** for ArthLLM. Because the raw PDF and text data exceeds hundreds of gigabytes, the actual downloaded data files are ignored via `.gitignore`. You can run the included scraper scripts locally to recreate the dataset.

---

## 📂 Repository Structure

```text
ArthLLM/
│
├── Tokenization/                 # Custom BPE & Character Tokenizer code
├── Vector Embeddings/            # Embedding generation and evaluation
├── section2/
│   └── raw/
│       └── indian/               # The heart of the data pipeline
│           ├── mca/              # MCA / NCLT / IBBI scrapers
│           ├── mof/              # Union Budget / Economic Survey scrapers
│           ├── rbi/              # RBI Circulars & Master Directions
│           ├── sebi/             # SEBI Enforcement & Regulations
│           └── other_regulators/ # CBDT, CCI, FEMA, IRDAI, PFRDA
│
├── pipeline_status.md            # Live tracker of downloaded dataset sizes
├── Project_plan.md               # The comprehensive master blueprint
└── requirements.txt              # Environment dependencies
```

---

## 🚀 Current Status

We are currently in the **Data Acquisition Phase**. 
- SEBI Pillar: **Done** (~9 GB / ~35,000 files)
- Ministry of Finance Pillar: **Done** (Budgets & Surveys)
- MCA/NCLT Pillar: **Done** (~27 GB / ~27,000 files)
- RBI Pillar: **In Progress**

Check `pipeline_status.md` for live updates on data collection. Tokenizer training (Phase 1) and Vector Embeddings (Phase 2) are complete. 

---
*Built with ❤️ in Pune. Built for Bharat.*
