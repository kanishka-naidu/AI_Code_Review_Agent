from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from backend/.env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2
)


def review_code(context, code):
    """
    Reviews the entire code using the provided OWASP context.
    (Used in Milestone 1)
    """

    prompt = f"""
You are an OWASP Security Expert.

Use ONLY the OWASP context below while reviewing.

OWASP Context:
{context}

Python Code:
{code}

Review the code.

Find security issues.

Explain why they are dangerous.

Suggest secure alternatives.
"""

    response = llm.invoke(prompt)

    return response.content


def enrich_finding(context, issue, message):
    """
    Enriches a detected finding with remediation information.
    (Used in Milestone 2 RAG Integration)
    """

    prompt = f"""
You are an OWASP Security Expert.

Use ONLY the OWASP context below.

OWASP Context:
{context}

Detected Issue:
{issue}

Details:
{message}

Provide ONLY the following:

1. Fix
   - Explain the remediation clearly.

2. Exact OWASP Reference
   - Mention the OWASP Top 10 2021 category if applicable.
   - Mention the OWASP Cheat Sheet name if applicable.

3. Secure Example
   - Provide ONLY the corrected code.
   - Do NOT include explanations.
   - Do NOT wrap the code inside markdown code fences (```).

Return ONLY in this exact format:

Fix:
...

OWASP Reference:
...

Secure Example:
...
"""

    response = llm.invoke(prompt)

    return response.content


if __name__ == "__main__":

    context = """
OWASP says:

Use parameterized queries.

Never concatenate SQL strings.
"""

    code = """
username = input()

query = "SELECT * FROM users WHERE name='" + username + "'"
"""

    result = review_code(context, code)

    print(result)