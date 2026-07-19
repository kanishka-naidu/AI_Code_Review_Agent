import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()

print("=" * 50)
print("PYTHON TEST")
print("=" * 50)

with open("tests/sample_code.py", "r") as file:
    python_code = file.read()

python_result = orchestrator.analyze(python_code)

print(python_result)

print("\n" + "=" * 50)
print("JAVA TEST")
print("=" * 50)

with open("tests/sample_java.java", "r") as file:
    java_code = file.read()

java_result = orchestrator.analyze(java_code)

print(java_result)