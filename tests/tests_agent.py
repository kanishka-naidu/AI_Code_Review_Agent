import os
import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.code_analysis_agent import CodeAnalysisAgent

with open("tests/sample_code.py", "r") as file:
    code = file.read()

agent = CodeAnalysisAgent()
result = agent.analyze(code)

print(result)