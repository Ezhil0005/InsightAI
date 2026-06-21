# AI Audit Logging Specification

InsightAI logs all downstream AI provider queries inside a dedicated audit database to monitor usage, speeds, and cost.

## Database Schema (`logs/ai_audit_log.db`)

Table: `ai_audit_log`
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `timestamp`: DATETIME DEFAULT CURRENT_TIMESTAMP
- `provider`: TEXT (e.g. OpenAI, Gemini, Groq)
- `response_time_ms`: REAL (latency in milliseconds)
- `error_status`: TEXT (Success or error details)
- `tokens_used`: INTEGER (Total prompt & completion tokens)
- `user_action`: TEXT (e.g. analyze_feedback, transcribe_audio)

## Usage Tracking
Token counts are mapped to costs stored in `config.py` to calculate exact operational spend.
