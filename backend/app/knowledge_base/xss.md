# Cross-Site Scripting (XSS) Prevention Cheat Sheet

## Overview
XSS attacks occur when an attacker injects malicious scripts into content delivered
to other users. The browser executes these scripts in the context of the victim's session.

**OWASP Reference:** A03:2021 – Injection

## Types
- **Stored XSS:** Malicious script is permanently stored in the application database.
- **Reflected XSS:** Malicious script is reflected off the web server in an error message or response.
- **DOM-based XSS:** Vulnerability exists in the client-side script itself.

## Primary Defense: Output Encoding
Encode ALL untrusted data before rendering to HTML.

### Context-specific encoding rules
| Output Context | Encoding Required |
|---|---|
| HTML body | HTML entity encode |
| HTML attribute | HTML attribute encode |
| JavaScript | JavaScript encode |
| URL parameter | URL encode |
| CSS | CSS encode |

### Python (Jinja2)
```python
# Jinja2 auto-escapes by default — ensure it is enabled
from jinja2 import Environment
env = Environment(autoescape=True)

# Never use |safe filter on untrusted data
# BAD: {{ user_input | safe }}
# GOOD: {{ user_input }}  (auto-escaped)
```

## Defense 2: Content Security Policy (CSP)
Use the Content-Security-Policy HTTP header to restrict sources of scripts.

```
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com;
```

## Defense 3: Input Validation
Validate that data is of the expected type, format, and length. Reject or sanitize
data that does not conform.

## Defense 4: HttpOnly and Secure Cookies
Use `HttpOnly` flag to prevent JavaScript from reading session cookies.

## Detection Indicators
- Direct use of `innerHTML`, `document.write()`, or `eval()` with user input
- Unescaped template rendering with raw user data
- Missing Content-Security-Policy headers
