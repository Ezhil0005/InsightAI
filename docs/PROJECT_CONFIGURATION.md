# Project Configuration - InsightAI Platform

This registry lists all configurations, api settings, dashboard attributes, and environment parameters used in **InsightAI**.

---

## Environment Variables

The system relies on the following environment variables. They can be set in your operating system or local shell:

- `OPENAI_API_KEY`: Required to activate **Tier 1 OpenAI GPT API** models and Whisper Speech-to-Text.
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`): Required to activate **Tier 1 Google Gemini API** content models and Gemini Audio transcription.
- `PYTHONIOENCODING`: Recommended to set to `utf-8` on Windows machines to avoid standard console unicode encoding crashes.

---

## Dependencies

Crucial dependencies required for the execution of the engine:
- `streamlit`: Serves the web-based interactive Enterprise Portal UI.
- `pandas`: Structured data handling, filtering, and database operations.
- `numpy`: Numerical analysis and mathematical least-squares fallbacks.
- `plotly`: Renders interactive graphs, indicator dials, and root cause tree maps.
- `scikit-learn`: LinearRegression models for daily volume and CSAT forecasts.
- `openpyxl`: Required by Pandas to generate styled `.xlsx` reports.

*Note: Python standard library modules used include `sqlite3`, `urllib.request`, `json`, `re`, `random`, `logging`, and `datetime`.*

---

## API Keys Configuration

API key authorization and fallback cascades:
- If `OPENAI_API_KEY` or `GEMINI_API_KEY` is present, the app automatically enables Cloud Model completions.
- Streamlit's interface provides temporary API input text fields if the environment lacks active keys.
- If no keys are registered, the app seamlessly falls back to **Tier 3 Rules-Based Heuristics** to execute classifications offline, ensuring zero crashes.

---

## Database Settings

- **File Path**: `database/feedback_active.db`
- **Table Name**: `feedback_analysis`
- **Storage Type**: SQLite (Serverless Local Database File)
- **Automatic Migration**: The schema checks and adds missing columns automatically during instantiation (`storage.py`).

---

## Dashboard Settings

- **Framework**: Streamlit
- **Theme**: Light Mode UI with custom Outfit font styling
- **Layout**: Wide layout containing a sidebar configuration center and main panel dashboards.
- **Visuals**: Dynamic Plotly donut charts, bar diagrams, indicator gauges, treemaps, and scatter quadrant grids.

---

## Forecasting Settings

- **Horizon**: 7-Day daily forecasts.
- **Models**: `sklearn.linear_model.LinearRegression`.
- **Fallback**: Built-in numpy ordinary least-squares matrix solver (`y = mx + c` fit).
- **Aggregations**: Calculated daily.

---

## Demo Mode Settings

- **Populates**: 225 total records in the SQLite database.
- **Mix**:
  - 50 Delivery Complaints (Negative)
  - 50 Billing Complaints (Negative)
  - 50 Support Complaints (Negative)
  - 25 Tamil Reviews (Mixed ratings)
  - 25 Hindi Reviews (Mixed ratings)
  - 25 Positive Reviews (English, ratings 4/5)
- **Timestamps**: Evenly distributed over the last 30 days.
- **Enrichments**: Instantly computed using `RulesFallbackEngine` offline.

---

## Supported Languages

The AI Translation layer supports:
- **English**: Processed directly.
- **Tamil**: Auto-detected (Tamil Unicode Block `\u0B80-\u0BFF`), translated to English for processing, and stored as `language="Tamil"`.
- **Hindi**: Auto-detected (Devanagari Unicode Block `\u0900-\u097F`), translated to English for processing, and stored as `language="Hindi"`.
