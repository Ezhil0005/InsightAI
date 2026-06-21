# System Health Guide - InsightAI Platform

This document describes the diagnostics parameters, threshold values, and maintenance actions for the **InsightAI** System Health Monitoring Center.

---

## 1. System Components Monitored

The `check_system_health()` utility periodically audits 6 major operational channels:

1. **Database Status**:
   - *Audits*: Read/write integrity of SQLite `feedback_analysis` tables.
   - *Healthy*: Database file is writeable and connections open under 50ms.
   - *Warning*: High file locks or write latencies.
   - *Critical*: Database file corrupted, missing, or read-only (Safe Mode will be triggered).
2. **Voice System Status**:
   - *Audits*: Intact initialization of `VoiceManager` classes and mock WAV audio ingestion.
   - *Healthy*: Audio quality calculators and lexical emotion modules are online.
   - *Critical*: Missing voice dependencies or module load errors.
3. **Active Provider Cascade**:
   - *Audits*: Confirms keys for OpenAI, Gemini, and Groq.
   - *Healthy*: Multiple API keys verified.
   - *Warning*: Falling back to Heuristics/Rules Engine because keys are missing or invalid.
4. **Forecast Engine Status**:
   - *Audits*: Least-squares linear regression solver loads.
   - *Healthy*: `TrendForecastingEngine` is initialized and imports resolve.
5. **Translation Engine Status**:
   - *Audits*: Script character matching and dictionary translations.
   - *Healthy*: Text correctly translates to English before classification.
6. **Background Queue Status**:
   - *Audits*: Thread state of the `BackgroundJobManager`.

---

## 2. Threshold Matrix

The overall status is mapped using the following metrics:

| Overall Status | Condition Trigger | Visual Indicator | Action Recommended |
| :--- | :--- | :--- | :--- |
| **Healthy** | All 6 components report Online. | Green Badge (`#10B981`) | Normal operations. No actions required. |
| **Warning** | Missing API keys (falling back to Rules Engine) OR Safe Mode forced manually. | Orange Badge (`#F59E0B`) | Configure missing API keys in Settings. Check disk space. |
| **Critical** | SQLite database file locked/unwritable. | Red Badge (`#EF4444`) | Re-initialize database or restart container to clear file locks. |

---

## 3. Maintenance Diagnostic Commands

To perform a manual system diagnostic, run the verification suite:
```bash
python verify_insight_ai.py
```
Check generated files `verification_report.txt` and `reports/verification_summary.txt` to verify all components pass checkouts.
