import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.security_agent import SecurityAgent

with open("tests/sample_code.py", "r") as file:
    code = file.read()

agent = SecurityAgent()

result = agent.analyze(code)

print(result)