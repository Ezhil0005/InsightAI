# Security Guide

PII handling, secrets, rate limiting, and safe mode.
# Security Guide Specification

InsightAI implements strict security guardrails to defend data and credentials.

## Enforced Security Controls

1. **API Key Validation**: Regex checks prevent invalid or format-corrupted keys (e.g. `sk-` for OpenAI, `gsk_` for Groq, and 35+ chars for Gemini).
2. **File Extension Filters**: Restricts file uploads strictly to: `.csv`, `.xlsx`, `.wav`, `.mp3`, `.m4a`, `.ogg`.
3. **File Size Limits**: Rejects uploads larger than **10MB** to prevent resource starvation.
4. **CSV Injection Sanitization**: Strips or prepends a single quote (`'`) to string fields beginning with `=`, `+`, `-`, `@`, `\t`, or `\r` before saving.
