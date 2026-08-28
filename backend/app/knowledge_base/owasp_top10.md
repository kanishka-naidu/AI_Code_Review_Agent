# OWASP Top 10 - 2021

## A01:2021 – Broken Access Control
Access control enforces policy so users cannot act outside their intended permissions.
Failures typically lead to unauthorized information disclosure, modification, or destruction.

**Prevention:**
- Deny by default except for public resources.
- Implement access control mechanisms centrally and reuse throughout the application.
- Log access-control failures and alert admins when appropriate.
- Rate limit API and controller access to minimise automated attack tooling.

---

## A02:2021 – Cryptographic Failures
Previously "Sensitive Data Exposure". Focus on failures related to cryptography that
often lead to exposure of sensitive data.

**Prevention:**
- Classify data processed, stored, or transmitted and apply controls based on classification.
- Don't store sensitive data unnecessarily. Discard it as soon as possible.
- Ensure up-to-date and strong standard algorithms, protocols, and keys are in place.
- Disable caching for responses that contain sensitive data.
- Use strong adaptive salted hashing functions (Argon2, scrypt, bcrypt) for passwords.

---

## A03:2021 – Injection
Injection flaws (SQL, NoSQL, OS, LDAP) occur when untrusted data is sent to an
interpreter as part of a command or query.

**Prevention:**
- Use a safe API that avoids the use of the interpreter entirely.
- Use parameterized queries / prepared statements for SQL.
- Use positive server-side input validation.
- Escape special characters using the correct escaping syntax for that interpreter.

---

## A04:2021 – Insecure Design
A new category for 2021 focusing on risks related to design and architectural flaws.

**Prevention:**
- Use threat modeling for critical authentication, access control, business logic, and key flows.
- Integrate security language and controls into user stories.
- Write unit and integration tests to validate that critical flows are resistant to threat model.

---

## A05:2021 – Security Misconfiguration
Commonly seen when default configurations are used, unnecessary features are enabled,
or error handling reveals too much information.

**Prevention:**
- Implement a repeatable hardening process.
- Remove or do not install unused features and frameworks.
- Ensure error messages don't reveal stack traces to users.

---

## A06:2021 – Vulnerable and Outdated Components
Components with known vulnerabilities may undermine application defences.

**Prevention:**
- Remove unused dependencies, features, components, files, and documentation.
- Continuously inventory the versions of client-side and server-side components.
- Only obtain components from official sources over secure links.

---

## A07:2021 – Identification and Authentication Failures
Previously "Broken Authentication". Weaknesses in authentication and session management.

**Prevention:**
- Implement multi-factor authentication where possible.
- Do not deploy with any default credentials.
- Implement weak password checks.
- Use a server-side, secure, built-in session manager.

---

## A08:2021 – Software and Data Integrity Failures
Relates to code and infrastructure that does not protect against integrity violations.
Includes insecure deserialization.

**Prevention:**
- Use digital signatures or similar mechanisms to verify software comes from the expected source.
- Ensure libraries and dependencies are consuming trusted repositories.
- Ensure deserialization of untrusted data is reviewed and validated.

---

## A09:2021 – Security Logging and Monitoring Failures
Insufficient logging and monitoring allows attackers to pivot and maintain persistence.

**Prevention:**
- Ensure all login, access control, and server-side input validation failures can be logged.
- Ensure log data is encoded correctly to prevent injections.
- Ensure high-value transactions have an audit trail.

---

## A10:2021 – Server-Side Request Forgery (SSRF)
SSRF flaws occur whenever a web application is fetching a remote resource without
validating the user-supplied URL.

**Prevention:**
- Sanitise and validate all client-supplied input data.
- Enforce the URL schema, port, and destination with a positive allow list.
- Do not send raw responses to clients.
