# AI Agents

## Overview

This folder contains the intelligent agents responsible for analyzing source code and detecting code quality issues and security vulnerabilities.

Each agent focuses on a specific task and is coordinated by the **Orchestrator** to generate a comprehensive code review report.

---

## Available Agents

### Python Code Analysis Agent
Performs static analysis on Python code to detect:
- Long Functions
- Too Many Parameters
- Missing Docstrings
- Large Classes
- Deep Nesting
- High Cyclomatic Complexity

### Python Security Agent
Detects common Python security vulnerabilities such as:
- Hardcoded Secrets
- SQL Injection
- Unsafe `eval()`
- Unsafe `exec()`
- Command Injection

### Java Code Analysis Agent
Performs static analysis on Java code to detect:
- Long Methods
- Too Many Parameters
- Large Classes
- Deep Nesting
- High Cyclomatic Complexity

### Java Security Agent
Detects common Java security vulnerabilities such as:
- Hardcoded Passwords
- Unsafe `Runtime.exec()`
- Weak Random Number Generation

---

## Workflow

```text
Source Code
      │
      ▼
Agent Orchestrator
      │
      ├── Python Code Analysis Agent
      ├── Python Security Agent
      ├── Java Code Analysis Agent
      └── Java Security Agent
      │
      ▼
Combined Findings
      │
      ▼
RAG Enhancement
      │
      ▼
Final Report
```

---

## Output

Each agent returns structured findings containing:

- Issue detected
- Severity
- Description
- Line number (if applicable)
- Recommended fix
- OWASP reference
- Secure coding example