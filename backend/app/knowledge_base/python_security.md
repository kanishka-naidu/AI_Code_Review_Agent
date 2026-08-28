# Python Security Best Practices

## Overview
Python is widely used for web applications, automation, and data processing. Following secure coding practices in Python helps prevent common vulnerabilities such as injection, unsafe deserialization, and exposure of sensitive data.

**OWASP Reference:** A03:2021 – Injection, A02:2021 – Cryptographic Failures

## Defense 1: Avoid Dangerous Functions
Never use `eval()`, `exec()`, or `compile()` on untrusted input. These functions execute arbitrary code and can lead to remote code execution.

```python
# VULNERABLE
user_input = request.form.get('code')
result = eval(user_input)

# SAFE — use ast.literal_eval for trusted literals only
import ast
try:
    result = ast.literal_eval(user_input)
except (ValueError, SyntaxError):
    result = None
```

## Defense 2: Use Parameterized Queries
Always use parameterized queries or ORM methods that escape input automatically. Never concatenate user input into SQL strings.

```python
# VULNERABLE
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# SAFE
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
```

## Defense 3: Secure File Handling
- Validate file paths to prevent path traversal (`../`).
- Use `os.path.realpath()` and ensure the resolved path stays within an allowed directory.
- Never trust user-supplied filenames directly.

```python
import os

base_dir = "/app/uploads"
user_path = request.form.get('filename')
full_path = os.path.realpath(os.path.join(base_dir, user_path))
if not full_path.startswith(os.path.realpath(base_dir)):
    raise ValueError("Invalid path")
```

## Defense 4: Secure Deserialization
Avoid `pickle` on untrusted data. Prefer `json` for data interchange.

```python
# VULNERABLE — pickle can execute arbitrary code
import pickle
data = pickle.loads(untrusted_bytes)

# SAFE — use JSON
import json
data = json.loads(untrusted_string)
```

## Defense 5: Secrets Management
- Never hardcode passwords, API keys, or tokens in source code.
- Use environment variables or a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).
- Rotate secrets regularly and revoke compromised ones immediately.

## Defense 6: Dependency Management
- Keep all third-party packages updated to patched versions.
- Use `pip-audit` or `safety` to scan for known vulnerabilities.
- Pin dependencies with hashes where possible.

## Detection Indicators
- Use of `eval()`, `exec()`, or `os.system()` with user input
- String concatenation or f-strings in SQL queries
- `pickle.loads()` on untrusted data
- Hardcoded credentials or API keys
- Missing input validation before file or command operations