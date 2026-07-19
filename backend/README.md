# Backend - AI Code Review & Security Analysis Agent

## Overview

The `backend` folder contains the complete backend implementation of the AI Code Review & Security Analysis Agent.

It is responsible for handling API requests, processing submitted source code, coordinating multiple AI agents, performing code analysis, integrating with the RAG pipeline, and generating detailed review reports.

---

# Backend Responsibilities

The backend handles:

- REST API development using FastAPI
- Source code submission and validation
- Programming language detection
- Multi-agent orchestration
- Code quality analysis
- Security vulnerability detection
- RAG-based knowledge enrichment
- Report generation

---


---

# Module Description

## agents/

Contains specialized AI analysis agents responsible for detecting different categories of issues.

### Code Analysis Agents

Detect maintainability and code quality problems:

- Long Functions
- Long Methods
- Large Classes
- Deep Nesting
- High Cyclomatic Complexity
- Missing Documentation
- Too Many Parameters


### Security Agents

Detect security vulnerabilities:

- Hardcoded Secrets
- SQL Injection
- Unsafe `eval()`
- Unsafe `exec()`
- Command Injection
- Weak Random Generation
- Runtime Command Execution

---

## orchestrator/

Responsible for coordinating multiple agents.

Responsibilities:

- Executes multiple analysis agents
- Combines findings from different agents
- Generates severity summaries
- Creates final review reports

---

## routes/

Contains FastAPI API endpoints.

Responsibilities:

- Receive user code submissions
- Handle file uploads
- Trigger analysis workflow
- Return JSON responses

---

## services/

Contains application-level business logic.

Responsibilities:

- Code analysis execution
- Report processing
- Communication between API layer and agents

---

## models/

Contains Pydantic data models.

Includes:

- Code submission models
- Finding models
- Final report models

These models ensure structured input and output formats.

---

## knowledge_base/

Handles Retrieval Augmented Generation (RAG) integration.

Responsibilities:

- Retrieve secure coding guidelines
- Fetch OWASP references
- Provide contextual information for detected issues

---

## llm/

Handles Large Language Model integration.

Responsibilities:

- Communicating with Google Gemini API
- Generating explanations
- Providing fixes and secure coding examples

---

## utils/

Contains reusable helper modules.

Includes:

### Language Detector

Automatically identifies:

- Python code
- Java code

### RAG Parser

Extracts structured information from LLM responses:

- Fix recommendations
- OWASP references
- Secure examples

### Severity Handler

Manages vulnerability severity classification.

---



