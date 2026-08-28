# Authentication and Session Management Cheat Sheet

## Overview
Broken authentication remains one of the most critical vulnerabilities. Weaknesses
in credentials, session management, or token handling can allow attackers to
compromise user accounts.

**OWASP Reference:** A07:2021 – Identification and Authentication Failures

## Defense 1: Strong Password Policy
- Minimum 12 characters.
- Allow passphrases and special characters.
- Check passwords against known-breached password lists (e.g., HaveIBeenPwned API).
- Do not set arbitrary maximum length limits (allow long passphrases).

## Defense 2: Secure Password Storage
NEVER store passwords in plain text or with reversible encryption.

```python
# VULNERABLE — plain text
user.password = request.password

# VULNERABLE — MD5/SHA1 (weak, no salt)
user.password = hashlib.md5(password.encode()).hexdigest()

# SAFE — bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

## Defense 3: Multi-Factor Authentication (MFA)
Implement TOTP-based MFA (RFC 6238) for all sensitive operations.

## Defense 4: Secure Session Management
- Generate session tokens with a CSPRNG (at least 128 bits of entropy).
- Invalidate session tokens on logout.
- Set session expiry.
- Use `Secure`, `HttpOnly`, `SameSite=Strict` flags on session cookies.

## Defense 5: Brute-Force Protection
- Implement account lockout after N failed attempts OR use progressive delays.
- Rate-limit authentication endpoints.
- Log failed authentication attempts.

## Defense 6: Default Credentials
- Never deploy with default usernames/passwords.
- Force credential change on first login for admin accounts.

## Detection Indicators
- Hardcoded credentials in source code
- Use of MD5 or SHA1 for password hashing
- Secrets or API keys in environment variables without rotation policy
- Missing rate limiting on login endpoints
- Session tokens in URLs
