import os

# Project Directories
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
DATABASE_DIR = os.path.join(APP_DIR, "database")
LOGS_DIR = os.path.join(APP_DIR, "logs")
REPORTS_DIR = os.path.join(APP_DIR, "reports")

# Database Paths
DB_PATH = os.path.join(DATABASE_DIR, "feedback_active.db")
AUDIT_DB_PATH = os.path.join(LOGS_DIR, "ai_audit_log.db")

# Backup Snapshot (Safe Mode Fallback)
BACKUP_SNAPSHOT_PATH = os.path.join(DATA_DIR, "backup_cache.json")

# Ensure necessary directories exist
for directory in [DATA_DIR, DATABASE_DIR, LOGS_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Security Configuration
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "wav", "mp3", "m4a", "ogg"}

# Business Metric Constants
DEFAULT_REVENUE_PER_CUSTOMER = 2500.0  # Base transaction/lifetime value in INR (₹)

# Provider Cost Tracking (USD/Token)
PROVIDER_COSTS = {
    "openai": {
        "input": 0.0000015,  # $1.50 per M tokens
        "output": 0.000002,  # $2.00 per M tokens
    },
    "gemini": {
        "input": 0.000000075, # $0.075 per M tokens
        "output": 0.0000003,   # $0.30 per M tokens
    },
    "groq": {
        "input": 0.00000005,  # $0.05 per M tokens
        "output": 0.0000001,   # $0.10 per M tokens
    },
    "heuristics": {
        "input": 0.0,
        "output": 0.0,
    }
}
