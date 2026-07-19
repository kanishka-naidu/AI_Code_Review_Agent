# AI Code Review & Security Analysis Agent

An AI-powered code review and security analysis system developed as part of the **Infosys Springboard Internship**. The project automates source code analysis by detecting code quality issues, identifying security vulnerabilities, and providing secure coding recommendations using a Retrieval-Augmented Generation (RAG) pipeline.

---

# Project Overview

Manual code reviews are time-consuming and require significant expertise. This project streamlines the review process by combining static code analysis, specialized AI agents, and a security knowledge base to automatically analyze source code and generate detailed review reports.

The system currently supports both **Python** and **Java** source code.

---

# Features

### Code Quality Analysis

- Long Functions / Methods
- Too Many Parameters
- Large Classes
- Missing Docstrings
- Deep Nesting
- High Cyclomatic Complexity

### Security Analysis

- Hardcoded Secrets
- SQL Injection
- Unsafe `eval()`
- Unsafe `exec()`
- Command Injection
- Unsafe `Runtime.exec()`
- Weak Random Number Generation

### AI & RAG Features

- Multi-Agent Architecture
- Retrieval-Augmented Generation (RAG)
- Google Gemini Integration
- OWASP Knowledge Base
- ChromaDB Vector Store
- Automated Fix Suggestions
- Secure Coding Examples
- OWASP References

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Programming Language | Python |
| Backend | FastAPI |
| LLM | Google Gemini |
| Framework | LangChain |
| Vector Database | ChromaDB |
| Static Analysis | Python AST, JavaLang Parser |
| Knowledge Base | OWASP Security Guidelines |

---

# System Architecture

```text
User Code
    │
    ▼
FastAPI Backend
    │
    ▼
Language Detection
    │
    ▼
Agent Orchestrator
    │
 ┌──────────────┬───────────────┐
 ▼              ▼               ▼
Python      Java          Security
Agents      Agents         Agents
        │
        ▼
Knowledge Base (RAG)
        │
        ▼
Google Gemini
        │
        ▼
Final JSON Report
```

---

# Project Structure

```text
AI_Code_Review_Agent/
│
├── backend/
│   ├── agents/
│   ├── orchestrator/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── utils/
│   ├── llm/
│   └── knowledge_base/
│
├── tests/
│
├── knowledge_base/
│
└── README.md
```

---

# Supported Languages

- Python
- Java

---

# Output

For every detected issue, the system provides:

- Issue Description
- Severity Level
- Line Number (where applicable)
- Recommended Fix
- OWASP Reference
- Secure Coding Example

---

# Testing

The project includes test cases for:

- Python Code Analysis
- Java Code Analysis
- Security Analysis
- Language Detection
- Multi-Agent Orchestration
- RAG Integration
- Report Generation

---

# Future Enhancements

- Support additional programming languages
- AI-based automatic code remediation
- Pull Request review integration
- CI/CD pipeline integration
- Web dashboard for report visualization

---

# Contributors

Developed as part of the **Infosys Springboard Internship Project**.