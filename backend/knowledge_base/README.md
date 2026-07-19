# Knowledge Base

## Overview

This folder contains the security knowledge base used by the Retrieval-Augmented Generation (RAG) pipeline.

The documents stored here are indexed into a vector database (ChromaDB) and are used to provide contextual information for detected code issues.

---

## Contents

The knowledge base includes resources such as:

- OWASP Top 10
- OWASP Cheat Sheets
- Secure Coding Guidelines
- Security Best Practices
- Programming Standards

---

## Purpose

The retrieved knowledge is used to enrich detected findings with:

- Recommended fixes
- OWASP references
- Secure coding examples
- Best practice recommendations

---

## Workflow

```text
Knowledge Documents
        │
        ▼
Document Processing
        │
        ▼
ChromaDB Vector Store
        │
        ▼
Semantic Retrieval
        │
        ▼
Gemini LLM
        │
        ▼
Enhanced Code Review Report
```

> **Note:** The generated ChromaDB vector database is excluded from version control and can be recreated using the knowledge base documents.