"""Test PDF generation service with sample data."""
import json
import sys
import os

sys.path.insert(0, ".")

from app.services.pdf_service import PDFReportService

# Create a sample report that mimics backend structure
sample_report = {
    "report_id": "test-report-123",
    "filename": "sample.py",
    "language": "python",
    "quality_score": 75,
    "security_score": 60,
    "summary": "The code has some security concerns and quality issues that should be addressed before production use.",
    "timestamp": "2024-01-15T12:00:00Z",
    "severity_distribution": {"critical": 0, "high": 2, "medium": 1, "low": 1, "info": 0},
    "pr_summary": "This analysis reviewed sample.py.\nThe code has high severity SQL injection risks.\nFix the vulnerable database queries.\nUse parameterized queries to prevent injection.\nAdd docstrings to public functions.\nOverall merge readiness is conditional.",
    "findings": [
        {
            "rule_id": "B608",
            "title": "SQL injection risk",
            "severity": "high",
            "description": "User input is used directly in a SQL query.",
            "location": "Line 42",
            "owasp_reference": "A03:2021",
            "remediation": "Use parameterized queries instead of string concatenation.",
        },
        {
            "rule_id": "S105",
            "title": "Hardcoded secret",
            "severity": "high",
            "description": "A hardcoded API key was found in the source.",
            "location": "Line 10",
            "owasp_reference": "A07:2021",
            "remediation": "Move the secret to environment variables.",
        },
    ],
    "recommendations": [
        "Fix the SQL injection on line 42 by using parameterized queries.",
        "Move the hardcoded API key to environment variables.",
    ],
    "metadata": {},
}

try:
    pdf_bytes = PDFReportService.generate(sample_report)
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF generated successfully! Size: {len(pdf_bytes)} bytes")
except Exception as e:
    print(f"PDF generation FAILED: {e}")
    import traceback
    traceback.print_exc()