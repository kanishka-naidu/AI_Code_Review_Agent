import re


def parse_rag_response(text):
    result = {
        "fix": "",
        "owasp_reference": "",
        "secure_example": ""
    }

    current = None

    for line in text.splitlines():

        line = line.strip()

        # Remove markdown formatting
        clean_line = re.sub(r"[*#`]", "", line).strip()

        if clean_line.lower().startswith("fix:"):
            current = "fix"
            result[current] = clean_line.split(":", 1)[1].strip()

        elif clean_line.lower().startswith("owasp reference:"):
            current = "owasp_reference"
            result[current] = clean_line.split(":", 1)[1].strip()

        elif clean_line.lower().startswith("secure example:"):
            current = "secure_example"
            result[current] = clean_line.split(":", 1)[1].strip()

        elif current:
            result[current] += "\n" + clean_line

    # Trim whitespace
    for key in result:
        result[key] = result[key].strip()

    # Remove markdown code fences
    result["secure_example"] = (
        result["secure_example"]
        .replace("```python", "")
        .replace("```java", "")
        .replace("```", "")
        .strip()
    )

    return result