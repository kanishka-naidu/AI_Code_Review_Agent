import ast
from platform import node
from backend.models.finding import Finding


class SecurityAgent:
    def __init__(self):
        self.findings = []
        self.sql_variables = set()

    def analyze(self, code: str):
        self.findings = []
        self.sql_variables = set()

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "agent": "Security Agent",
                "findings": []
            }

        for node in ast.walk(tree):

            # eval()
            if isinstance(node, ast.Call):
                self.check_eval(node)

            # exec()
            if isinstance(node, ast.Call):
                self.check_exec(node)

            # Command Injection
            if isinstance(node, ast.Call):
                self.check_command_injection(node)

            # Assignment checks
            if isinstance(node, ast.Assign):
                self.check_hardcoded_secret(node)
                self.detect_sql_variable(node)

            # SQL Injection
            if isinstance(node, ast.Call):
                self.check_sql_injection(node)
        return {
            "agent": "Security Agent",
            "findings": self.findings
        }

    def check_eval(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.findings.append({
                "issue": "Unsafe use of eval()",
                "severity": "High",
                "line": node.lineno,
                "message": "Avoid using eval(). It can execute arbitrary code."
            })

    def check_exec(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "exec":
            self.findings.append({
                "issue": "Unsafe use of exec()",
                "severity": "High",
                "line": node.lineno,
                "message": "Avoid using exec(). It can execute arbitrary code."
            })

    def check_hardcoded_secret(self, node):

        keywords = [
            "password",
            "passwd",
            "secret",
            "token",
            "apikey",
            "api_key",
            "key"
        ]

        for target in node.targets:

            if isinstance(target, ast.Name):

                name = target.id.lower()

                if any(word in name for word in keywords):

                    if isinstance(node.value, ast.Constant):

                        self.findings.append({
                            "issue": "Hardcoded Secret",
                            "severity": "High",
                            "line": node.lineno,
                            "message": f"'{target.id}' contains a hardcoded value."
                        })
    def check_sql_injection(self, node):

        if not isinstance(node.func, ast.Attribute):
            return

        if node.func.attr != "execute":
            return

        if len(node.args) == 0:
            return

        query = node.args[0]

        # Case 1: execute(query)
        if isinstance(query, ast.Name):
            if query.id in self.sql_variables:
                self.findings.append({
                    "issue": "Possible SQL Injection",
                    "severity": "High",
                    "line": node.lineno,
                    "message": "Dynamic SQL query detected. Use parameterized queries."
                })

        # Case 2: execute("SELECT..." + user)
        elif isinstance(query, (ast.BinOp, ast.JoinedStr)):
            self.findings.append({
                "issue": "Possible SQL Injection",
                "severity": "High",
                "line": node.lineno,
                "message": "Dynamic SQL query detected. Use parameterized queries."
            })
    def detect_sql_variable(self, node):

        if len(node.targets) != 1:
            return

        target = node.targets[0]

        if not isinstance(target, ast.Name):
            return

        value = node.value

        if isinstance(value, (ast.BinOp, ast.JoinedStr)):
            self.sql_variables.add(target.id)

    def check_command_injection(self, node):

        if not isinstance(node.func, ast.Attribute):
            return

        dangerous_functions = [
            "system",
            "popen",
            "run",
            "call"
        ]

        if node.func.attr in dangerous_functions:

            self.findings.append({
                "issue": "Possible Command Injection",
                "severity": "High",
                "line": node.lineno,
                "message": "Avoid executing system commands with user-controlled input."
            })