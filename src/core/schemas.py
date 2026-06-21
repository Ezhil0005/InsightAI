"""Pydantic-style lightweight schemas for internal data objects.

Small dataclasses used across storage and pipelines to ensure shape
consistency without heavy dependencies.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FeedbackPayload:
    id: Optional[int]
    source_type: str
    original_text: str
    translated_text: Optional[str]
    detected_language: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class VoicePayload:
    id: Optional[int]
    file_name: str
    duration_seconds: float
    transcript: str
    detected_language: Optional[str]
    metadata: Dict[str, Any]
