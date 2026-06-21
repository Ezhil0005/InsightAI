# Deployment Guide

Instructions for Docker, Compose, and cloud targets.
# Deployment Guide Specification

InsightAI is containerized for seamless deployment.

## Deploying using Docker Compose

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and insert your API keys:
   ```env
   OPENAI_API_KEY=sk-...
   GEMINI_API_KEY=AIzaSy...
   GROQ_API_KEY=gsk_...
   ```
2. **Build and Run**:
   Execute compose commands at the root:
   ```bash
   docker-compose up --build -d
   ```
3. **Uptime check**:
   Access the dashboard at `http://localhost:8501`.
   Persistent volumes are mounted under `./database`, `./logs`, and `./reports`.
