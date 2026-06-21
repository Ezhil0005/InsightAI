CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_id TEXT,
    session_id TEXT,
    entity_type TEXT,
    entity_id TEXT,
    action TEXT,
    provider_name TEXT,
    success BOOLEAN,
    latency_ms INTEGER,
    error_type TEXT,
    error_message TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
