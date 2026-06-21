import os
import re
import pandas as pd
from typing import Tuple

# Import constants from config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def validate_api_key(provider: str, key: str) -> bool:
    """
    Validates formatting and presence of provider API keys.
    """
    if not key or not isinstance(key, str) or len(key.strip()) < 10:
        return False
        
    provider = provider.lower()
    if provider == "openai":
        # e.g., sk-...
        return key.startswith("sk-")
    elif provider == "gemini" or provider == "google":
        # General checks for Google APIs
        return len(key) >= 35
    elif provider == "groq":
        # e.g., gsk_...
        return key.startswith("gsk_")
    return True

def validate_upload_file(file_name: str, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validates file upload format and size limits.
    Returns (is_valid, error_message).
    """
    if not file_name or "." not in file_name:
        return False, "Invalid filename: Missing file extension."
        
    ext = file_name.split(".")[-1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '.{ext}'. Supported files: {', '.join(config.ALLOWED_EXTENSIONS)}"
        
    file_size = len(file_bytes)
    if file_size > config.MAX_FILE_SIZE_BYTES:
        max_mb = config.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        size_mb = file_size / (1024 * 1024)
        return False, f"File size ({size_mb:.2f} MB) exceeds maximum limit of {max_mb:.1f} MB."
        
    return True, ""

def sanitize_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitizes string columns in a DataFrame to prevent CSV Injection attacks.
    CSV injection happens when strings starting with '=', '+', '-', '@', '\t', '\r' 
    are evaluated by Excel/Sheets as formulas.
    We mitigate this by prepending a single quote (') to such fields.
    """
    sanitized_df = df.copy()
    injection_chars = ('=', '+', '-', '@', '\t', '\r')
    
    for col in sanitized_df.columns:
        # Only process object/string columns
        if sanitized_df[col].dtype == 'object':
            sanitized_df[col] = sanitized_df[col].apply(
                lambda val: f"'{val}" if isinstance(val, str) and val.startswith(injection_chars) else val
            )
            
    return sanitized_df
