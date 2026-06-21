import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def init_audit_db():
    """
    Initializes the SQLite audit logging database.
    """
    db_dir = os.path.dirname(config.AUDIT_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(config.AUDIT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            provider TEXT,
            response_time_ms REAL,
            error_status TEXT,
            tokens_used INTEGER,
            user_action TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_ai_call(provider: str, response_time_ms: float, error_status: str, tokens_used: int, user_action: str):
    """
    Inserts a record of an AI call into the audit database.
    """
    # Ensure database is initialized
    init_audit_db()
    
    conn = sqlite3.connect(config.AUDIT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_audit_log (provider, response_time_ms, error_status, tokens_used, user_action)
        VALUES (?, ?, ?, ?, ?)
    """, (provider, response_time_ms, error_status, tokens_used, user_action))
    conn.commit()
    conn.close()

def get_recent_logs(limit: int = 50) -> pd.DataFrame:
    """
    Retrieves the most recent audit logs.
    """
    init_audit_db()
    conn = sqlite3.connect(config.AUDIT_DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM ai_audit_log ORDER BY timestamp DESC LIMIT ?", 
            conn, 
            params=(limit,)
        )
        return df
    finally:
        conn.close()

def get_audit_stats() -> Dict[str, Any]:
    """
    Calculates aggregated statistics for providers from the audit log.
    Calculations:
      - Average latency per provider
      - Success rates per provider
      - Total cost per provider in USD (input + output tokens estimated)
      - Total call count and total token count
    """
    init_audit_db()
    conn = sqlite3.connect(config.AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    # Query summary metrics per provider
    # Note: tokens_used stores total tokens. For cost estimation, we split tokens into
    # 70% input and 30% output roughly, or use provider cost structure.
    stats = {}
    
    try:
        cursor.execute("SELECT DISTINCT provider FROM ai_audit_log")
        providers = [row[0] for row in cursor.fetchall()]
        
        for p in providers:
            # Latency
            cursor.execute("SELECT AVG(response_time_ms) FROM ai_audit_log WHERE provider = ? AND error_status = 'Success'", (p,))
            avg_latency = cursor.fetchone()[0] or 0.0
            
            # Total Calls
            cursor.execute("SELECT COUNT(*) FROM ai_audit_log WHERE provider = ?", (p,))
            total_calls = cursor.fetchone()[0] or 0
            
            # Success Calls
            cursor.execute("SELECT COUNT(*) FROM ai_audit_log WHERE provider = ? AND error_status = 'Success'", (p,))
            success_calls = cursor.fetchone()[0] or 0
            success_rate = (success_calls / total_calls * 100.0) if total_calls > 0 else 100.0
            
            # Total Tokens
            cursor.execute("SELECT SUM(tokens_used) FROM ai_audit_log WHERE provider = ?", (p,))
            total_tokens = cursor.fetchone()[0] or 0
            
            # Calculate cost
            p_lower = p.lower()
            costs_config = config.PROVIDER_COSTS.get(p_lower, {"input": 0.0, "output": 0.0})
            # Assume 75% of tokens are input and 25% are output for estimation
            input_tokens = total_tokens * 0.75
            output_tokens = total_tokens * 0.25
            total_cost_usd = (input_tokens * costs_config["input"]) + (output_tokens * costs_config["output"])
            
            stats[p] = {
                "avg_latency_ms": round(avg_latency, 2),
                "total_calls": total_calls,
                "success_rate_pct": round(success_rate, 2),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost_usd, 6)
            }
            
        # Overall metrics
        cursor.execute("SELECT COUNT(*) FROM ai_audit_log WHERE error_status != 'Success'")
        error_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT timestamp) FROM ai_audit_log") # Rough estimate for sessions
        
        stats["overall"] = {
            "error_count": error_count,
            "total_calls_all": sum(stats[p]["total_calls"] for p in stats if p != "overall"),
            "total_tokens_all": sum(stats[p]["total_tokens"] for p in stats if p != "overall"),
            "total_cost_usd_all": sum(stats[p]["total_cost_usd"] for p in stats if p != "overall")
        }
    except Exception as e:
        stats["overall"] = {"error_count": 0, "total_calls_all": 0, "total_tokens_all": 0, "total_cost_usd_all": 0.0}
    finally:
        conn.close()
        
    return stats
