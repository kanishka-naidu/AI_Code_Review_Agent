# Code Injection Prevention Cheat Sheet

## Overview
Code injection occurs when an application sends untrusted data to an interpreter or execution engine. This can lead to arbitrary code execution, data theft, or system compromise.

**OWASP Reference:** A03:2021 – Injection

## Primary Defense: Avoid Dynamic Code Execution
Never execute untrusted user input as code.

### Python - eval() and exec()
```python
# VULNERABLE — eval() with user input
user_input = request.form.get('code')
result = eval(user_input)

# VULNERABLE — exec() with user input
user_input = request.form.get('code')
exec(user_input)

# SAFE — Use proper parsing and validation
import ast
def safe_eval(user_input):
    try:
        tree = ast.parse(user_input, mode='eval')
        # Validate AST nodes before execution
        if not is_safe_expression(tree):
            raise ValueError("Unsafe expression")
        return eval(compile(tree, '<string>', 'eval'))
    except (SyntaxError, ValueError):
        return None
```

### Python - os.system() and subprocess
```python
# VULNERABLE — direct user input in system command
user_input = request.form.get('filename')
os.system(f"cat {user_input}")

# SAFE — Use subprocess with argument list
import subprocess
user_input = request.form.get('filename')
subprocess.run(['cat', user_input], check=True)

# SAFER — Validate and sanitize
import os
user_input = request.form.get('filename')
if not user_input.replace('_', '').replace('.', '').isalnum():
    raise ValueError("Invalid filename")
subprocess.run(['cat', user_input], check=True)
```

## Defense 2: Input Validation and Sanitization
- Whitelist allowed characters and patterns
- Validate input length and format
- Use parameterized queries instead of string concatenation
- Never concatenate user input into command strings

## Defense 3: Principle of Least Privilege
- Run applications with minimal required permissions
- Use containerization or sandboxing for code execution
- Implement resource limits (CPU, memory, file system access)

## Defense 4: Secure APIs and Libraries
- Use well-vetted libraries instead of manual parsing
- Prefer high-level APIs over low-level system calls
- Keep all dependencies updated

## Detection Indicators
- Use of eval(), exec(), or os.system() with user input
- String concatenation in command execution
- Direct user input in subprocess calls
- Missing input validation before code execution
- Dynamic imports with user-controlled module names

## Remediation Steps
1. Identify all instances of dynamic code execution
2. Replace with safe alternatives (AST parsing, subprocess with lists)
3. Implement strict input validation
4. Add security-focused code reviews
5. Use static analysis tools to detect code injection patterns
6. Implement sandboxing for necessary code execution