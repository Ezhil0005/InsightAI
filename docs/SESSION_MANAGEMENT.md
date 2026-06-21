# Session Management - InsightAI Platform

This document describes the design of `st.session_state` cache parameters, session historical schemas, and database synchronization in **InsightAI**.

---

## 💾 Session State Dictionary Schema

InsightAI upgrades the session history cache into a structured registry mapping active datasets to their corresponding metadata variables:

```python
st.session_state["session_history"][dataset_name] = {
    "dataset_name": str,            # Ingested filename or demo name
    "upload_date": str,             # Formatted timestamp YYYY-MM-DD HH:MM:SS
    "records": int,                 # Total row counts in processed dataframe
    "languages": list,              # Languages parsed (e.g. ["English", "Tamil", "Hindi"])
    "analysis_status": str,         # Processing status ("Ingested", "Completed")
    "business_health_score": int,   # Dynamic health score (0-100) calculated on ingest
    "dataframe": pd.DataFrame       # Cached Pandas DataFrame of processed feedback
}
```

---

## 🎛️ Session Switching & Database Synchronization

The sidebar renders these session structures as interactive corporate widgets. When a user clicks to switch between datasets:
1. The active variables are re-assigned:
   ```python
   st.session_state["active_session"] = selected_dataset_name
   st.session_state["active_df"] = details["dataframe"]
   ```
2. The SQLite database table `feedback_analysis` is updated:
   ```python
   db = FeedbackDatabase(DB_PATH)
   db.save_dataframe(details["dataframe"], replace_all=True)
   db.close()
   ```
   This synchronizes the backend storage model instantly.
3. The Streamlit script executes a rerun (`st.rerun()`), reloading all Plotly visual graphs and KPI scorecards with the newly selected dataset.

---

## 🎙️ Voice Upload Ingestion State

Voice inputs follow a clean isolation flow:
- Uploading audio transcribes and evaluates text, saving parameters to `st.session_state["_voice_transcript"]` and `st.session_state["_voice_analysis"]`.
- When "Save to DB" is pressed, the record is appended to `st.session_state["active_df"]` and synchronized to SQLite, which updates all dashboard charts instantly.
