from backend.utils.rag_parser import parse_rag_response

sample = """
Fix:
Use parameterized queries.

OWASP Reference:
OWASP SQL Injection Prevention Cheat Sheet.

Secure Example:
cursor.execute(
    "SELECT * FROM users WHERE name = ?",
    (username,)
)
"""

result = parse_rag_response(sample)

print(result)