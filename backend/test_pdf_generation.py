"""Test PDF generation with the new human-readable 3-page format."""
import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.services.pdf_service import PDFReportService

report = json.load(open(os.path.join(BASE_DIR, "app/reports/02b19803-e898-4183-bccf-6abe23c1151f.json"), encoding="utf-8"))
pdf = PDFReportService.generate(report)
with open(os.path.join(BASE_DIR, "test_output.pdf"), "wb") as f:
    f.write(pdf)
print(f"PDF generated: {len(pdf)} bytes")

# Verify content
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("pypdf not available - skipping content verification")
        sys.exit(0)

with open(os.path.join(BASE_DIR, "test_output.pdf"), "rb") as f:
    reader = PdfReader(f)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

print("=== PDF CONTENT CHECK ===")
checks = {
    "1. Executive Summary": "1. Executive Summary" in text,
    "2. Overall Scores": "2. Overall Scores" in text,
    "3. Severity Breakdown": "3. Severity Breakdown" in text,
    "4. Findings & Evidence": "4. Findings & Evidence" in text,
    "5. Remediation Roadmap": "5. Remediation Roadmap" in text,
    "6. Prioritized Fixes": "6. Prioritized Fixes" in text,
    "7. Secure Recommendations": "7. Secure Recommendations" in text,
    "No raw JSON (rule_id)": "rule_id" not in text,
    "No raw JSON (finding_metadata)": "finding_metadata" not in text,
    "No raw JSON (tool_source)": "tool_source" not in text,
    "Human-readable severity CRITICAL": "CRITICAL" in text.upper(),
    "Human-readable severity HIGH": "HIGH" in text.upper(),
    "Human-readable severity MEDIUM": "MEDIUM" in text.upper(),
    "Human-readable severity LOW": "LOW" in text.upper(),
    "Quality score": "quality" in text.lower(),
    "Security score": "security" in text.lower(),
}

for name, passed in checks.items():
    print(f"  {'PASS' if passed else 'FAIL'} {name}")

print(f"\nTotal PDF pages: {len(reader.pages)}")
print(f"Total PDF text length: {len(text)} chars")
print("\n=== SAMPLE TEXT (first 1500 chars) ===")
print(text[:1500])