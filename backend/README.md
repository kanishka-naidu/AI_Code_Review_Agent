# Backend

## Overview

The `backend` folder contains the core implementation of the **AI Code Review & Security Analysis Agent**. It handles API requests, code analysis, security scanning, RAG integration, and report generation.

---

## Folder Structure

```text
backend/
├── agents/           # Code analysis and security agents
├── knowledge_base/   # RAG retrieval using ChromaDB
├── llm/              # Gemini integration
├── models/           # Request and response models
├── orchestrator/     # Multi-agent orchestration
├── routes/           # FastAPI endpoints
├── services/         # Business logic
├── utils/            # Helper utilities
└── app.py            # FastAPI application
```

---

## Responsibilities

- Develop REST APIs using FastAPI
- Detect Python and Java code issues
- Perform security vulnerability analysis
- Coordinate multiple AI agents
- Retrieve OWASP guidance using RAG
- Generate structured JSON reports

---

## Technologies

- Python
- FastAPI
- LangChain
- Google Gemini API
- ChromaDB
- Python AST
- JavaLang Parser

---

## Main API Endpoints

- `POST /submit-code`
- `POST /analyze`

---

## Output

The backend generates a structured report containing:

- Issue detected
- Severity
- Description
- Recommended fix
- OWASP reference
- Secure coding example