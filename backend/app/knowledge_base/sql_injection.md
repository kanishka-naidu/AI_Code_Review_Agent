# SQL Injection Prevention Cheat Sheet

## Overview
SQL Injection (SQLi) occurs when untrusted data is sent to an interpreter as part
of a SQL query. The attacker can use this to read, modify, or delete database data,
and in some cases execute OS commands.

**OWASP Reference:** A03:2021 – Injection

## Defense 1: Prepared Statements (Parameterized Queries)

The use of prepared statements with variable binding (parameterized queries) is the
most effective way to prevent SQL injection.

### Python (sqlite3 / psycopg2)
```python
# VULNERABLE — do NOT do this
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# SAFE — parameterized query
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

### Java (JDBC)
```java
// VULNERABLE
Statement stmt = conn.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE id = " + userId);

// SAFE
PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
pstmt.setInt(1, userId);
```

## Defense 2: Stored Procedures
Stored procedures can be safe if they do not include unsafe dynamic SQL generation.

## Defense 3: Input Validation
Validate data type, length, format, and range. However, input validation alone is
insufficient — always use parameterized queries as the primary defense.

## Defense 4: Least Privilege
The database account used by the application should have the minimum necessary permissions.
Avoid using DBA or admin-level accounts.

## Detection Indicators
- Dynamic string concatenation in SQL queries
- Use of string formatting (`%s % user_input`, f-strings) in SQL context
- eval() or exec() used on database-related strings
- Raw user input passed directly to ORM `raw()` or `execute()` methods
