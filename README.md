# QuickCart Customer Feedback Intelligence System

A production-grade customer feedback ingestion, cleaning, AI enrichment, storage, and reporting pipeline built with Python and Streamlit. This system turns raw, messy customer messages into structured, decision-ready intelligence.

---

## 🌟 Key Features

1. **Full Data Isolation (Clean Slate Execution)**:
   - **Upload Reset**: Uploading a new file immediately wipes the SQLite database table (`DELETE FROM feedback_analysis;`) and deletes all output artifacts from previous runs from the disk.
   - **Reset Button**: A manual "Reset & Unload File" action performs a full reset, clearing the database, removing files, and returning the Streamlit UI to the landing page.
   - **Crash Safe**: If a pipeline execution fails (e.g. due to a wrong file schema), the system is safely left in an empty database state with no stale reports or data leaks.

2. **3-Tier AI Enrichment Fallback Engine**:
   - **Tier 1 (Google Gemini API / OpenAI API)**: Supports Google Gemini API (using `gemini-1.5-flash` under the free developer tier) and OpenAI API (`gpt-3.5-turbo`). Includes automatic retry loops, silent fallback, and allows users to set keys via environment variables or secure password fields directly in the UI.
   - **Tier 2 (Local Hugging Face Transformers)**: Local zero-shot classifiers (`valhalla/distilbart-mnli-12-1`) and sentiment pipelines (`distilbert-base-uncased-finetuned-sst-2-english`) run locally if API keys are missing.
   - **Tier 3 (Rule-Based Deterministic Fallback)**: A deterministic keyword NLP fallback, active by default. Operates offline, instantly, with zero setup.

3. **Robust Data Cleaning & Deduplication**:
   - Standardizes rating bounds (coerces out-of-bounds to `NULL`).
   - Standardizes timestamps to `YYYY-MM-DD HH:MM:SS` across 20+ date formats.
   - Normalizes and removes near-duplicate reviews using source precedence rules (`support_ticket` > `app_store_review` > `survey_comment`) and latest timestamps.
   - Filters meaningless blocklisted spam (e.g., `ok`, `test`, `nan`, `.`) while preserving domain-relevant short text (e.g., `refund late`).

4. **Sleek Executive Dashboard & Styled Excel Reports**:
   - Dynamic Streamlit dashboard with KPI counters, Plotly interactive sentiment donut chart, complaint categories bar chart, representative comments tabs, and search explorer.
   - Multi-sheet Excel workbook (`report.xlsx`) with automated column widths, zebra-striped rows, soft-colored sentiment highlights, KPI cards, and embedded Matplotlib distribution charts.
   - Leadership-ready markdown report with trend analysis showing if customer experience is improving or worsening.

---

## 📁 Directory Structure

```
QuickCart_System/
│
├── app.py                      # Streamlit UI Entry Point & State Controller
├── requirements.txt            # Package Dependencies
├── README.md                   # System Documentation (This file)
│
├── data/
│   └── raw_uploads/            # Storage for active uploaded feedback file
│
├── database/
│   └── feedback.db             # sqlite3 database storing cleaned & enriched rows
│
├── output/
│   ├── cleaned_data.csv        # Intermediate cleaned dataset
│   ├── enriched_data.csv       # AI-enriched intermediate dataset
│   ├── category_distribution.png
│   ├── sentiment_distribution.png
│   ├── summary_report.md       # Leadership markdown summary report
│   ├── report.xlsx             # Styled multi-tab Excel spreadsheet report
│   └── pipeline.log            # Running execution logs
│
└── src/
    ├── ingestion.py            # CSV/Excel reader & data profiling
    ├── cleaning.py             # Deduplication, rating & timestamp standardization
    ├── ai_engine.py            # 3-Tier AI sentiment & category classifier
    ├── suggestions.py          # Priority-based business recommendation compiler
    ├── storage.py              # SQLite storage controller
    └── reporting.py            # Matplotlib charts & openpyxl Excel compiler
```

---

## 🚀 How to Run the System

### 1. Install Dependencies
Make sure you have Python 3.8+ installed. Navigate to the `QuickCart_System` directory and run:
```bash
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard
Execute the following command in your terminal:
```bash
streamlit run app.py
```
This launches the application. Access the portal in your browser at `http://localhost:8501`.

### 3. Run via Command Line
You can also run the data pipeline orchestrator directly from your terminal:
```bash
python src/pipeline.py --raw-data ../data/customer_feedback_raw.csv
```

Configure AI models using CLI flags:
```bash
# To run with Google Gemini (Requires setting your GEMINI_API_KEY environment variable)
python src/pipeline.py --raw-data ../data/customer_feedback_raw.csv --use-gemini

# To run with OpenAI (Requires setting your OPENAI_API_KEY environment variable)
python src/pipeline.py --raw-data ../data/customer_feedback_raw.csv --use-openai

# To run with local Hugging Face zero-shot models
python src/pipeline.py --raw-data ../data/customer_feedback_raw.csv --use-hf
```

---

## 🧠 Engineering Rules & Error Validation

* **Validation Bounds**: The cleaning module checks for column names matching `feedback_text`, `rating`, `timestamp`, `source`, and `id`. If no feedback text column is found, the pipeline aborts immediately.
* **Database Wiping**: Wiping the SQLite database runs `DELETE FROM feedback_analysis;` rather than dropping the table, keeping the primary key schema intact.
* **Strict Overwrite**: Outputs like `cleaned_data.csv`, `enriched_data.csv`, and `report.xlsx` are overwritten from scratch on every run, avoiding row duplicates or appended tabs.
