# Java Security Best Practices

## Overview
Java applications are commonly targeted for injection, deserialization, and access control vulnerabilities. Following secure coding practices in Java helps prevent these issues.

**OWASP Reference:** A03:2021 – Injection, A08:2021 – Software and Data Integrity Failures

## Defense 1: Use Prepared Statements
Never concatenate user input into SQL queries. Always use `PreparedStatement` with parameter binding.

```java
// VULNERABLE
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id = " + userId);

// SAFE
PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
pstmt.setInt(1, userId);
ResultSet rs = pstmt.executeQuery();
```

## Defense 2: Avoid Dangerous Deserialization
Java deserialization of untrusted data can lead to remote code execution. Never deserialize data from untrusted sources.

```java
// VULNERABLE — deserializing untrusted data
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();

// SAFE — validate and use allowlists, or use JSON
ObjectMapper mapper = new ObjectMapper();
MyData data = mapper.readValue(inputStream, MyData.class);
```

## Defense 3: Prevent Command Injection
Never pass user input directly to `Runtime.exec()` or `ProcessBuilder` with a shell.

```java
// VULNERABLE
String cmd = "ls " + userInput;
Process p = Runtime.getRuntime().exec(cmd);

// SAFE — use ProcessBuilder with argument list
ProcessBuilder pb = new ProcessBuilder("ls", userInput);
Process p = pb.start();
```

## Defense 4: Secure File Handling
- Validate file paths to prevent path traversal.
- Use `Paths.get(baseDir).resolve(userPath).normalize()` and verify the result stays within the base directory.
- Never trust user-supplied filenames.

## Defense 5: Secure Configuration
- Never hardcode credentials, API keys, or database passwords in source code.
- Use environment variables or a secrets manager.
- Disable verbose error messages that reveal stack traces to users.

## Defense 6: Access Control
- Enforce authorization on every request, not just the UI.
- Use role-based access control (RBAC) and deny by default.
- Validate that the current user has permission to access the requested resource.

## Detection Indicators
- String concatenation in SQL queries
- `Runtime.exec()` or `ProcessBuilder` with user input
- `ObjectInputStream.readObject()` on untrusted data
- Hardcoded credentials or secrets
- Missing input validation before file operations