# Project Configuration, Architecture & Governance Guide

This document serves as the master guide for the configuration, folder structures, AI provider cascades, deployment pipelines, troubleshooting procedures, and future roadmaps of the **InsightAI** Decision Intelligence Platform.

---

## 1. Platform Configuration

### Environment Variables & API Keys
Configure the platform by creating a `.env` file in the root directory:

```bash
# AI Provider Keys
OPENAI_API_KEY=sk-proj-...       # Required for OpenAI Whisper and GPT models
GEMINI_API_KEY=AIzaSy...         # Required for Gemini Audio and Flash models
GROQ_API_KEY=gsk_...             # Optional Groq API Key

# System Path Configurations
DATABASE_PATH=database/feedback_active.db
AUDIT_LOG_PATH=logs/ai_audit_log.db
```

### Provider Routing
All AI completions and audio transcriptions flow through a **Unified Provider Manager** (`src/providers.py`). The router ranks available providers on startup based on success rates and latencies from the audit log, dynamically building a cascade queue:
* `Auto-Select`: Auto-routes to the best-performing provider (Gemini or OpenAI).
* `Fallback Cascade`: Cascades gracefully from the selected provider down the queue, ending in the offline local heuristic rules engine.

### Database Paths & Storage Settings
* **Active DB**: `database/feedback_active.db` (Contains all reviews, scores, and timeline records).
* **Backup Copies**: `database/feedback_copy.db` (Cached template loaded during safe mode recovery).

---

## 2. Architecture & Folder Structure

### Directory Tree
```
QuickCart_System/
│
├── app.py                     # Streamlit Frontend Web App
├── config.py                  # Global Constants, Cost Models, defaults
├── verify_insight_ai.py       # Comprehensive Verification Tests
├── requirements.txt           # Python Project Dependencies
├── Dockerfile                 # Docker Build Recipe
├── docker-compose.yml         # Container Orchestration config
│
├── database/                  # SQLite Databases
│   └── feedback_active.db     
│
├── logs/                      # Audit Databases
│   └── ai_audit_log.db        
│
├── reports/                   # Compiled PDF Exports
│
├── docs/                      # Governance & Rules Markdown Guides
│   ├── VOICE_INTELLIGENCE_BUSINESS_RULES.md
│   ├── PROJECT_CONFIGURATION_GUIDE.md
│   └── IMPLEMENTATION_HISTORY.md
│
└── src/                       # Backend Source Code Modules
    ├── storage.py             # SQLite Schemas & Migration engines
    ├── providers.py           # Provider Router & Cascade client
    ├── voice.py               # Voice Quality, STT, Translation, Emotion, Alerts
    ├── ai_engine.py           # Heuristics rules fallback parser
    ├── business_metrics.py    # CSI, Loyalty, Churn, Risk, Health math formulas
    ├── forecasting.py         # Least-squares Trend Predictor
    ├── reports.py             # ReportLab PDF compilation layout
    ├── security.py            # API Validators & CSV Injection sanitizers
    ├── audit.py               # SQL audit logger
    └── jobs.py                # Background job worker queues
```

---

## 3. AI Providers & Offline Fallbacks

* **OpenAI (Whisper-1 / GPT-3.5-Turbo)**:
  Used for speech-to-text transcriptions and deep sentiment enrichment. Requires `OPENAI_API_KEY`.
* **Google Gemini (1.5-Flash / Audio)**:
  REST payload integrations for high-speed voice transcription and json schema outputs. Requires `GEMINI_API_KEY`.
* **Groq (Llama-3)**:
  High-speed chat completion endpoint. Requires `GROQ_API_KEY`.
* **Offline Rules Engine**:
  deterministic keyword regex parser. Instantly activated if keys are missing, requests timeout, or web calls fail. Guaranteed to return valid predictions.

---

## 4. Deployment Guides

### Local Machine Setup
1. Clone the repository and navigate to the project directory:
   ```bash
   cd QuickCart_System
   ```
2. Set up virtual environment and install requirements:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

### Docker Setup
1. Build the Docker container image:
   ```bash
   docker build -t insight-ai-platform .
   ```
2. Start the container with ports exposed:
   ```bash
   docker run -p 8501:8501 --env-file .env insight-ai-platform
   ```

---

## 5. Maintenance & Backup

### Troubleshooting Guide
* **Streamlit Port Blocked**: If port 8501 is locked, specify a different port on startup: `streamlit run app.py --server.port 8502`.
* **No Database Table Column Errors**: If database alterations are blocked, verify write permissions on the `database/` folder or let the script run startup migrations automatically.

### Backup Strategy & Recovery
* The platform retains a copy of the base database at `database/feedback_copy.db`.
* **Safe Mode Recovery**: If active database operations fail or tables corrupt, use the Safe Mode tab in the Operations Center to overwrite `feedback_active.db` with the copy template.

---

## 6. Future Roadmap

1. **Local Whisper Integration**: Transition from OpenAI Whisper API calls to local CPU-bound whisper.cpp or PyTorch inference weights.
2. **Predictive Churn Trigger Alerts**: Connect the alert engine directly to corporate webhook receivers (Slack/Microsoft Teams) to dispatch alerts instantly to customer success desks.
3. **Advanced LLM Agents**: Deploy crewed subagents to handle automated support calls based on recommended Roadmap actions.
