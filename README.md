# Development of Smart Code Inspection Platform with Vulnerability Detection System

## Overview
This workspace contains a modular FastAPI backend for AI-assisted code review and security analysis. The current implementation includes:

- FastAPI REST API
- Upload and analysis endpoints
- Language-aware analyzer pipeline for Python and Java
- Structured report models
- Basic test coverage

## Backend setup

```bash
cd backend
python -m pip install -r requirements.txt pytest
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Configuration is driven through environment variables and the repository `configuration/` JSON files. An example `.env` is provided as `.env.example` in the repository root.

Important runtime configuration:

- ANALYZER_FAILURE_MODE: `partial` (default) or `strict`.
  - partial: continue pipeline on analyzer errors, return partial results, include analyzer status and errors in report metadata, and avoid misleading 100/100 scores (conservative fallback applied).
  - strict: abort the analysis and return HTTP 500 if any analyzer fails during execution. Use this in production when you prefer fail-fast behaviour.

- STARTUP_FAIL_ON_MISSING_ANALYZERS: `true`/`false`. When true the application will fail startup if required analyzer binaries/modules or configuration files are missing.

See `.env.example` for other environment variables such as LLM configuration, Redis, and analyzer options.

## API endpoints
- GET /health
- POST /upload
- POST /analyze
- POST /assistant
- GET /report/{report_id}

## Testing

```bash
pytest tests/test_api.py
```
