# Router Flow - InsightAI Platform

This document describes the multi-page routing structure, state machine transitions, and page views rendering logic in **InsightAI**.

---

## 🗺️ State Routing Flow

Streamlit runs the script from top to bottom on every user interaction. InsightAI manages a custom page routing router using the session state variable `st.session_state["current_page"]`.

```
                  ┌───────────────┐
                  │ 1. Landing    │
                  └───────┬───────┘
                          │ Ingest File / Demo Mode
                          ▼
                  ┌───────────────┐
                  │ 2. Ingest/    │
                  │    Validate   │
                  └───────┬───────┘
                          │ Proceed Click
                          ▼
                  ┌───────────────┐
                  │ 3. Decision   │
                  │    Center     │
                  └─┬─────┬─────┬─┘
     Drill Module   │     │     │   Review Insights
  ┌─────────────────┘     │     └────────────────┐
  ▼                       ▼                      ▼
┌───────────────┐ ┌───────────────┐      ┌───────────────┐
│ 4. Analytics  │ │ 5. System     │      │ 6. Executive  │
│    Dashboards │ │    Insights   │      │    Actions    │
└───────────────┘ └───────────────┘      └───────────────┘
```

---

## 🚦 Navigation Commands & Controllers

Conditional blocks render page layouts based on the current state of `st.session_state["current_page"]`:

- `"landing"`: Renders the SaaS Dark Hero landing page.
- `"upload"`: Ingests CSV/Excel data and transcribes WAV/MP3 complaints.
- `"validation"`: Displays dataset parameters, language distributions, and category distributions.
- `"hub"`: Displays the Decision Intelligence Center grid consisting of 10 modern analysis modules.
- `"exec_summary"`, `"kpi_overview"`, `"sentiment"`, `"churn"`, `"impact"`, `"forecasting"`, `"root_cause"`, `"priority_matrix"`, `"download"`: Drills down into the specific dashboard modules.
- `"insights"`: Renders System Insights (historical metrics, forecasting metrics, and critical issues list).
- `"exec_action_center"`: Renders Executive Action Center (revenue exposure risk, priority scoring rankings, and checklists).
- `"settings"`: Configures API keys.
- `"help"`: User manual documentation.

---

## 🔄 Redirection Guidelines

State triggers handle automatic navigations:
1. **Demo Ingest**: Activates the 550 records generator, saves session information, sets `active_df`, and redirects directly to the **Decision Intelligence Center** (`st.session_state["current_page"] = "hub"`).
2. **File Processing**: Successful pipeline runs save data to SQLite and cache the active dataframe, redirecting the user to the **Data Validation Center** (`st.session_state["current_page"] = "validation"`).
3. **Data Proceed**: Clicking the proceed button on validation redirects to the Decision Center.
4. **Platform Logo Click**: Clicking the platform logo globally returns the user to the Decision Center (if data is loaded) or the Landing Page.
5. **Back Controls**: Top bar back buttons return users to previous workflow stages.
