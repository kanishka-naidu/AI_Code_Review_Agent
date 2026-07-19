# Tests

## Overview

This folder contains the test cases used to validate the functionality of the **AI Code Review & Security Analysis Agent**.

The tests verify code analysis, security detection, language identification, RAG integration, and multi-agent orchestration.

---

## Test Files

| Test File | Purpose |
|-----------|---------|
| `tests_agent.py` | Tests Python code analysis agent |
| `tests_security.py` | Tests Python security agent |
| `tests_java_agent.py` | Tests Java code analysis agent |
| `tests_java_security_agent.py` | Tests Java security agent |
| `tests_language_detector.py` | Tests automatic language detection |
| `tests_orchestrator.py` | Tests multi-agent orchestration |
| `tests_rag.py` | Tests RAG enrichment pipeline |
| `tests_rag_parser.py` | Tests RAG response parsing |

---

## Sample Files

- `sample_code.py` – Sample Python code for testing
- `sample_java.java` – Sample Java code for testing

---

## Validation Coverage

The implemented tests verify:

- Python code quality analysis
- Java code quality analysis
- Security vulnerability detection
- Automatic language detection
- Multi-agent orchestration
- RAG-based enrichment
- JSON report generation

---

## Expected Result

All test cases should execute successfully and verify that the generated findings match the expected output for each analysis module.