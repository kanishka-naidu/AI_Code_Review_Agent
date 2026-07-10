# AI Code Review & Security Analysis Agent

AI-powered code review and security analysis system developed as part of the Infosys Springboard Internship.
## Project Overview

Manual code reviews require time and expertise. This project aims to automate the review process using an AI Agent that can analyze code, detect potential problems, and provide meaningful feedback based on secure coding practices.

The system uses AI reasoning and a security knowledge base to assist developers in writing cleaner and safer code.

---

## Features

✅ AI-based code analysis  
✅ Code quality and style checking  
✅ Security vulnerability detection  
✅ OWASP-based secure coding recommendations  
✅ Knowledge base integration using RAG pipeline  
✅ Automated improvement suggestions  

---
##  Project Structure


AI_Code_Review_Agent/

│
├── backend/
│ ├── knowledge_base/
│ ├── build_knowledge_base.py
│ ├── reviewer.py
│ ├── main.py
│ └── requirements.txt
│
├── README.md
└── .gitignore


---

## Security Knowledge Base

The project uses OWASP security documentation to improve vulnerability detection.

Currently covered areas:

- SQL Injection
- Cross-Site Scripting (XSS)
- Authentication Issues
- Broken Access Control
- Hardcoded Secrets
- Secure Coding Practices

---

