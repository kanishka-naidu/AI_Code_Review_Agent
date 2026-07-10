from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2
)


def review_code(context, code):
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

if __name__ == "__main__":

    context = """
OWASP says:

Use parameterized queries.

Never concatenate SQL strings.
"""

    code = """
username=input()

query="SELECT * FROM users WHERE name='"+username+"'"
"""

    result = review_code(context, code)

    print(result)
    