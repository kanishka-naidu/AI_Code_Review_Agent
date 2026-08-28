"""Verify PDF content has the new sections."""
import subprocess
import sys

# Try to use PyPDF2 or pdfplumber if available
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("pypdf not available - installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pypdf", "-q"], check=False)
        from pypdf import PdfReader

with open("downloaded_report.pdf", "rb") as f:
    reader = PdfReader(f)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

print("=== PDF CONTENT CHECK ===")
checks = {
    "Code Analysis Report": "Code Analysis Report" in text,
    "Severity Breakdown": "Severity Breakdown" in text,
    "Pull Request Summary": "Pull Request Summary" in text,
    "Remediation Roadmap": "Remediation Roadmap" in text,
    "Recommendations": "Recommendations" in text,
    "SQL injection": "SQL injection" in text.lower() or "sql injection" in text.lower(),
    "OWASP": "owasp" in text.lower(),
    "Quality Score": "Quality Score" in text,
    "Security Score": "Security Score" in text,
}

for name, passed in checks.items():
    print(f"  {'✅' if passed else '❌'} {name}")

print(f"\nTotal PDF text length: {len(text)} chars")
print("\n=== SAMPLE TEXT ===")
print(text[:2000])