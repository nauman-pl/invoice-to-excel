# ⚡ InvoiceFlow — Autonomous Invoice → Excel AI Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Gemini 3.6 Flash](https://img.shields.io/badge/Gemini-3.6%20Flash-orange.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://docs.pytest.org/)

An enterprise-grade document intelligence platform that transforms invoices, receipts, and camera screenshots into consolidated, multi-sheet Excel spreadsheets with customer purchasing memory and mathematical verification.

---

## 🏗️ Architecture

```text
[ PDF Invoices / Images / Screenshots / Camera Snap ]
                        │
                        ▼
   Smart Hybrid Extractor (pypdf + Tesseract OCR)
                        │
                        ▼
   Dual-Engine Parser (Gemini 3.6 Flash OR Deterministic Regex)
                        │
                        ▼
    Zero-Trust Mathematical Validator (Python)
    ├─ Quantity × Unit Price ≈ Line Total
    ├─ Subtotal + Tax ≈ Total
    └─ Duplicate Invoice Detection
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
Permanent Customer Memory       Multi-Sheet Excel
   (SQLite Database)                Exporter
   ├─ Purchase Timeline         ├─ Invoices Summary
   ├─ Itemized History          └─ Line Items Detail
   └─ Lifetime Spend
```

---

## 🌟 Core Features

- **📱 Fully Responsive:** Works on desktop (Mac, Windows, Linux), tablets (iPad, Surface), and mobile phones (iPhone, Android).
- **📸 Multi-Modal Input:** Supports PDF uploads, drag-and-drop, macOS clipboard paste (`Cmd+Ctrl+Shift+4`), and real-time phone camera capture.
- **⚡ Smart Hybrid OCR:** Instant ~5ms digital PDF extraction (`pypdf`) with automatic fallback to high-DPI Tesseract OCR for scanned documents.
- **🤖 Gemini 3.6 Flash AI:** Schema-enforced structured decoding powered by Google GenAI SDK.
- **🛡️ Zero-Trust Financial Validation:** Mathematical discrepancy checking and duplicate payment protection.
- **👤 Customer Intelligence Memory:** SQLite database tracks customer lifetime value, itemized purchase histories, and date-based search.
- **📊 Relational Multi-Tab Excel:** Generates linked `.xlsx` sheets (`Invoices_Summary` and `Line_Items_Detail`).

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Install
```bash
git clone https://github.com/nauman-pl/invoice-to-excel.git
cd invoice-to-excel
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 3. Run the Web Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Automated Tests

Run the complete regression test suite:
```bash
pytest
```

---

## ☁️ 1-Click Cloud Deployment (Streamlit Community Cloud)

1. Fork or push this repository to your GitHub account.
2. Go to **[share.streamlit.io](https://share.streamlit.io/)** and click **New App**.
3. Select your repository (`invoice-to-excel`), branch (`main`), and main file (`app.py`).
4. In **Advanced Settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **Deploy!** Your app will be live on a public URL in 60 seconds.
