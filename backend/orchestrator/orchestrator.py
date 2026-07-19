from concurrent.futures import ThreadPoolExecutor
from backend.knowledge_base.retriever import retrieve_context
from backend.llm.reviewer import enrich_finding
from backend.agents.code_analysis_agent import CodeAnalysisAgent
from backend.agents.security_agent import SecurityAgent
from backend.models.report import Report
from backend.utils.language_detector import LanguageDetector
from backend.agents.java_code_analysis_agent import JavaCodeAnalysisAgent
from backend.agents.java_security_agent import JavaSecurityAgent
from backend.utils.rag_parser import parse_rag_response
class Orchestrator:

    def __init__(self):
        # Python Agents
        self.python_code_agent = CodeAnalysisAgent()
        self.python_security_agent = SecurityAgent()

        # Java Agents
        self.java_code_agent = JavaCodeAnalysisAgent()
        self.java_security_agent = JavaSecurityAgent()
    def analyze(self, code):
        
        print("******** ORCHESTRATOR RUNNING ********")
        language = LanguageDetector.detect(code)
        if language == "Python":

            code_agent = self.python_code_agent
            security_agent = self.python_security_agent

        elif language == "Java":

            code_agent = self.java_code_agent
            security_agent = self.java_security_agent

        else:

            return {
                "status": "error",
                "message": "Unsupported language."
            }

        with ThreadPoolExecutor() as executor:

            code_future = executor.submit(
                code_agent.analyze,
                code
            )

            security_future = executor.submit(
                security_agent.analyze,
                code
            )

            code_result = code_future.result()
            security_result = security_future.result()

        findings = code_result["findings"] + security_result["findings"]
        for finding in findings:

            context = retrieve_context(finding["issue"])

            try:
                rag_response = enrich_finding(
                    context,
                    finding["issue"],
                    finding["message"]
                )

                parsed = parse_rag_response(rag_response)

            except Exception:
                parsed = {
                    "fix": "Not available",
                    "owasp_reference": "Not available",
                    "secure_example": "Not available"
                }

            finding["fix"] = parsed["fix"]
            finding["owasp_reference"] = parsed["owasp_reference"]
            finding["secure_example"] = parsed["secure_example"]

        summary = {
            "total_findings": len(findings),
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for finding in findings:

            severity = finding["severity"].lower()

            if severity == "high":
                summary["high"] += 1

            elif severity == "medium":
                summary["medium"] += 1

            elif severity == "low":
                summary["low"] += 1

        report = Report(
            status="success",
            language=language,
            summary=summary,
            findings=findings
        )

        return report.to_dict()