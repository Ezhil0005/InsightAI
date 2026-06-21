CREATE TABLE IF NOT EXISTS voice_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_id INTEGER,
    file_name TEXT,
    file_type TEXT,
    duration_seconds REAL,
    transcript TEXT,
    detected_language TEXT,
    translated_text TEXT,
    translation_confidence REAL,
    voice_emotion TEXT,
    emotion_confidence REAL,
    urgency_score REAL,
    stt_provider TEXT,
    stt_latency_ms INTEGER,
    fallback_used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
