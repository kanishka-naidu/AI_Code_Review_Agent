# Secure Coding Guidelines

## Overview
Secure coding practices reduce the risk of introducing vulnerabilities during development. These guidelines apply across languages and frameworks.

**OWASP Reference:** A04:2021 – Insecure Design, A05:2021 – Security Misconfiguration

## Principle 1: Input Validation
Validate all input on the server side. Never trust client-side validation alone.

- Validate data type, length, format, and range.
- Use allowlists (whitelists) rather than denylists (blacklists) where possible.
- Reject invalid input rather than attempting to sanitize it.

```python
# VULNERABLE — no validation
def process(user_input):
    return eval(user_input)

# SAFE — validate before use
import re
def process(user_input):
    if not re.match(r'^[a-zA-Z0-9_]+$', user_input):
        raise ValueError("Invalid input")
    return user_input
```

## Principle 2: Output Encoding
Encode all untrusted data before rendering to prevent injection attacks.

- HTML-encode data rendered in HTML contexts.
- URL-encode data in URL parameters.
- JavaScript-encode data in script contexts.
- Use framework-provided auto-escaping where available.

## Principle 3: Least Privilege
Run applications and services with the minimum permissions required.

- Use dedicated service accounts with limited database permissions.
- Avoid running as root or administrator.
- Grant only the permissions needed for each function.

## Principle 4: Defense in Depth
Layer multiple security controls so that if one fails, others still protect the system.

- Combine input validation with output encoding.
- Use parameterized queries AND validate input.
- Apply authentication AND authorization checks.

## Principle 5: Secure Error Handling
Never expose stack traces, internal paths, or sensitive data in error messages.

```python
# VULNERABLE — exposes internal details
except Exception as e:
    return f"Error: {e}"

# SAFE — log details, return generic message
import logging
except Exception as e:
    logging.error("Operation failed: %s", e)
    return "An unexpected error occurred. Please try again."
```

## Principle 6: Secure Logging
Log security-relevant events without logging sensitive data.

- Log authentication failures, access control failures, and input validation failures.
- Never log passwords, tokens, or personal data.
- Use structured logging for easier analysis.

## Principle 7: Secure Dependencies
Keep all dependencies updated and scan for known vulnerabilities.

- Use automated dependency scanning tools.
- Remove unused dependencies.
- Verify package integrity with checksums or signatures.

## Detection Indicators
- Missing input validation on user-supplied data
- Unescaped output rendering
- Overly permissive permissions or service accounts
- Verbose error messages exposing internal details
- Sensitive data in logs
- Outdated or vulnerable dependencies