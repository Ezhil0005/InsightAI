"""Preprocessing utilities for text and voice pipelines."""
from typing import Dict, Any


def normalize_text(text: str) -> str:
    # Basic normalizer: trim and collapse whitespace; placeholder for advanced cleaning
    return " ".join(text.strip().split())
