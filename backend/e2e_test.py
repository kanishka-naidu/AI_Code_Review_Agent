"""E2E test for the analyze endpoint."""
import json
import time
import sys
import requests

CODE = """
import sqlite3
import os

def unsafe_query(user_input):
    db = sqlite3.connect('test.db')
    cursor = db.cursor()
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)
    return cursor.fetchall()

def get_secret():
    api_key = 'sk-1234567890abcdef'
    return api_key

def dangerous():
    user_input = input('Enter command: ')
    os.system(user_input)
"""

start = time.time()

try:
    r = requests.post(
        "http://127.0.0.1:8000/analyze",
        json={"language": "python", "code": CODE},
        timeout=180,
    )
    elapsed = time.time() - start
    print(f"Status: {r.status_code}, Elapsed: {elapsed:.1f}s")

    if r.status_code == 200:
        data = r.json()
        report = data.get("report", {})
        print(f"Report ID: {report.get('report_id')}")
        print(f"Quality: {report.get('quality_score')}")
        print(f"Security: {report.get('security_score')}")
        findings = report.get("findings", [])
        print(f"Total findings: {len(findings)}")
        for f in findings[:8]:
            print(f"  - [{f.get('severity')}] {f.get('rule_id')}: {f.get('title')}")
        pr = report.get("pr_summary") or ""
        print(f"PR Summary lines: {len([l for l in pr.splitlines() if l.strip()])}")
        rd = report.get("metadata", {})
        print(f"Metadata keys: {list(rd.keys())[:5]}")
        # Save report for PDF test
        with open("last_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print("Saved report to last_report.json")
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

print(f"Total elapsed: {time.time() - start:.1f}s")