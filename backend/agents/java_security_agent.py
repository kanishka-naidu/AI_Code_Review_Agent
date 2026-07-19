import javalang
from backend.models.finding import Finding


class JavaSecurityAgent:

    def __init__(self):
        self.findings = []

    def analyze(self, code: str):

        self.findings = []

        try:
            tree = javalang.parse.parse(code)

        except javalang.parser.JavaSyntaxError:

            return {
                "agent": "Java Security Agent",
                "findings": []
            }
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            self.check_hardcoded_password(node)

        for _, node in tree.filter(javalang.tree.MethodInvocation):
            self.check_sql_injection(node)

        for _, node in tree.filter(javalang.tree.MethodInvocation):
            self.check_runtime_exec(node)

        for _, node in tree.filter(javalang.tree.ClassCreator):
            self.check_process_builder(node)

        for _, node in tree.filter(javalang.tree.ClassCreator):
            self.check_weak_random(node)
        return {
            "agent": "Java Security Agent",
            "findings": self.findings
        }
    def check_hardcoded_password(self, node):

        keywords = ["password", "passwd", "pwd"]

        for declarator in node.declarators:

            variable_name = declarator.name.lower()

            if any(keyword in variable_name for keyword in keywords):

                if declarator.initializer and isinstance(
                    declarator.initializer,
                    javalang.tree.Literal
                ):

                    self.findings.append(
                        Finding(
                            issue="Hardcoded Password",
                            severity="High",
                            line=node.position.line if node.position else 0,
                            message=f"Variable '{declarator.name}' contains a hardcoded password."
                        ).to_dict()
                    )
    def check_sql_injection(self, node):

        sql_methods = [
            "executeQuery",
            "executeUpdate",
            "execute",
            "prepareStatement"
        ]

        if node.member in sql_methods:

            if node.arguments:

                first_arg = node.arguments[0]

                if isinstance(first_arg, javalang.tree.BinaryOperation):

                    self.findings.append(
                        Finding(
                            issue="SQL Injection",
                            severity="High",
                            line=node.position.line if node.position else 0,
                            message=f"Possible SQL Injection in '{node.member}'."
                        ).to_dict()
                    )
    def check_runtime_exec(self, node):

        if node.member == "exec":

            self.findings.append(
                Finding(
                    issue="Runtime.exec() Usage",
                    severity="High",
                    line=node.position.line if node.position else 0,
                    message="Use of Runtime.exec() may lead to command injection."
                ).to_dict()
            )

    def check_process_builder(self, node):

        if getattr(node.type, "name", "") == "ProcessBuilder":

            self.findings.append(
                Finding(
                    issue="ProcessBuilder Usage",
                    severity="High",
                    line=node.position.line if node.position else 0,
                    message="Use of ProcessBuilder may lead to command injection if inputs are not validated."
                ).to_dict()
            )
    def check_weak_random(self, node):

        if getattr(node.type, "name", "") == "Random":

            self.findings.append(
                Finding(
                    issue="Weak Random",
                    severity="Medium",
                    line=node.position.line if node.position else 0,
                    message="java.util.Random is not cryptographically secure. Consider using SecureRandom."
                ).to_dict()
            )