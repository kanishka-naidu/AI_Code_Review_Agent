from backend.knowledge_base.retriever import retrieve_context
from backend.llm.reviewer import enrich_finding

issue = "SQL Injection"
message = "SQL query is built using string concatenation."

context = retrieve_context(issue)

result = enrich_finding(context, issue, message)

print(result)