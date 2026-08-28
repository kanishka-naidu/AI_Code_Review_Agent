"""Test PDF download and assistant endpoints."""
import json
import requests
import time


def test_pdf_endpoint() -> None:
    """Test the PDF download endpoint with an actual report."""
    # Load the report that was just generated
    try:
        with open("last_report.json", "r", encoding="utf-8") as f:
            report = json.load(f)
    except FileNotFoundError:
        print("No last_report.json found - running fresh analysis...")
        return

    report_id = report.get("report_id")
    print(f"Testing PDF download for report: {report_id}")

    start = time.time()
    r = requests.get(f"http://127.0.0.1:8000/report/{report_id}/pdf", timeout=30)
    elapsed = time.time() - start
    print(f"Status: {r.status_code}, Elapsed: {elapsed:.1f}s")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"Content-Disposition: {r.headers.get('content-disposition')}")
    if r.status_code == 200:
        pdf_bytes = r.content
        print(f"PDF size: {len(pdf_bytes)} bytes")
        with open("downloaded_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("PDF saved to downloaded_report.pdf")
    else:
        print(f"Error: {r.text[:300]}")


def test_report_endpoint() -> None:
    """Test the report JSON endpoint."""
    try:
        with open("last_report.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        report_id = report.get("report_id")
    except FileNotFoundError:
        print("No report to test")
        return

    r = requests.get(f"http://127.0.0.1:8000/report/{report_id}", timeout=10)
    print(f"Report endpoint status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Report has keys: {list(data.keys())[:8]}")
        print(f"Severity distribution: {data.get('severity_distribution')}")


def test_assistant_health() -> None:
    """Test the assistant endpoint is reachable (without full LLM call)."""
    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
    print(f"Backend health: {r.status_code}")


if __name__ == "__main__":
    test_pdf_endpoint()
    print()
    test_report_endpoint()
    print()
    test_assistant_health()
    print("ALL TESTS COMPLETE")