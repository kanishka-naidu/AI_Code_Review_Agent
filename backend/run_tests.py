"""Run pytest and capture output properly."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-x", "-q", "--no-header", "--tb=short", "-p", "no:cacheprovider"],
    capture_output=True,
    text=True,
    cwd=".",
    timeout=120,
)

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print(f"Return code: {result.returncode}")