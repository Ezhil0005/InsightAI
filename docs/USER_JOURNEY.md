# User Journey - InsightAI Platform

This document describes the operational guided 5-step workflow journey that users navigate in the **InsightAI** platform.

---

## 🗺️ The Five-Step Guided Workflow Journey

InsightAI structures feedback analysis into a logical, corporate SaaS workflow:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    STEP 1    │───>│    STEP 2    │───>│    STEP 3    │───>│    STEP 4    │───>│    STEP 5    │
│ Upload Data  │    │ Validate Data│    │ Analyze Fdbk │    │ Review Intel │    │ Exec Actions │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 1. Step 1: Upload Data (Ingestion)
- **Action**: Ingest raw review CSV/Excel sheets or WAV/MP3 audio files. Configure API key configurations (Gemini/OpenAI) or local heuristics models.
- **Goal**: Ingest feedback and trigger processing pipelines.

### 2. Step 2: Validate Data (Diagnostics)
- **Action**: Review dataset stats (rows, columns, file sizes), missing values, duplicate reviews, language distributions, and category distributions.
- **Goal**: Assess data quality and suitability scores before proceeding.

### 3. Step 3: Analyze Feedback (Decision Intelligence Center)
- **Drill Down**: Open specific analytics modules (Sentiment, Churn, Business Impact, Root Causes, Forecasting) to explore charts and KPIs.
- **Goal**: Review core metrics and pinpoint category bottlenecks.

### 4. Step 4: Review Intelligence (System Insights)
- **Action**: Analyze management-level health indicators, CSAT forecasts, and critical severity issues.
- **Goal**: Formulate a complete business overview.

### 5. Step 5: Executive Actions (Roadmap Compilation)
- **Action**: Check immediate, short-term, and long-term strategic recommendations compiled by the AI Advisor.
- **Goal**: Export the compiled business action plan as a markdown file.
