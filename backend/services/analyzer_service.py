from backend.orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()


def analyze_code(code: str):
    return orchestrator.analyze(code)