# Safe Mode & Recovery Guide - InsightAI Platform

This document explains the recovery behavior, backup data structures, and restoration processes of the **Safe Mode** system in **InsightAI**.

---

## 1. Safe Mode Recovery Mechanics

Safe Mode acts as an automated software circuit-breaker that isolates disk write and network API actions when structural dependencies fail.

### 1.1 Automatic Activation Triggers
The platform automatically switches into Safe Mode if:
1. **SQLite Database Unavailability**:
   - Connection throws a driver exception.
   - Database directory is read-only or lacks write permissions.
   - Database tables are corrupted.
2. **Critical Module Load Crash**:
   - Critical analytics engines fail to initialize during page routing.

### 1.2 Recovery State Behavior
Once Safe Mode is triggered:
- **Redirection / Banner**: Displays the "Safe Mode Active" diagnostic card in the Operations Monitoring Center and a "Safe Mode: Active" badge in the sidebar.
- **Data Isolation**: Database write queries are bypassed to prevent application tracebacks.
- **Backup Load**: The active dataframe is automatically loaded from the historical backup file:
  `data/customer_feedback_raw.csv`
- **Offline Classification**: Sentiment, category, and priority indices are resolved using local heuristic algorithms.

---

## 2. Testing Safe Mode (Forced Recovery)

To verify the platform's response under database failure conditions:
1. Navigate to the **Operations Monitoring Center** page.
2. Scroll to the bottom and locate the **🚨 Force Safe Mode (Recovery & Backup Activation)** toggle.
3. Toggle it **ON**.
4. Verify that:
   - The System Diagnostics badge in the sidebar changes to **Warning / Safe Mode: Active**.
   - The dataset swaps to **Backup Historical Dataset**.
   - All executive dashboard charts compile and render correctly using the backup dataset.
5. Toggle it **OFF** to restore database operation.
