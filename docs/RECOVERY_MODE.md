# Recovery Mode (Safe Mode) Specification

InsightAI implements a self-healing **Safe Mode** recovery layer to prevent application crashes during database locks or API timing outages.

## Operations & Failure Recovery

1. **Database Uptime Probes**: At startup, `load_stored_data()` tests connections to `feedback_active.db`.
2. **Safe Mode Reroute**: If SQLite connections throw write/read exceptions or the database file is completely corrupted:
   - Sets `st.session_state["safe_mode"] = True`.
   - Renders a prominent yellow recovery banner.
3. **Data Fallback**: Reads from the static backup snapshot `data/backup_cache.json` containing a pre-compiled dataset of 550 customer feedbacks.
4. **Operations Restriction**: Read-only actions (dashboards, forecasts, recommendations) remain fully active, while write-based operations (uploads, voice imports) are restricted to prevent crash traces.
5. **Auto-Restoration**: Once the database file becomes writable, Safe Mode disables itself automatically upon refresh.
