import javalang
from backend.models.finding import Finding


class JavaCodeAnalysisAgent:

    def __init__(self):
        self.findings = []

    def analyze(self, code: str):

        self.findings = []

        try:
            tree = javalang.parse.parse(code)

        except javalang.parser.JavaSyntaxError:

            return {
                "agent": "Java Code Analysis Agent",
                "findings": []
            }

        # Traverse all method declarations
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            self.check_parameters(node)
            self.check_long_method(node)
            self.check_deep_nesting(node)
            self.check_cyclomatic_complexity(node)

        # Traverse all class declarations
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            self.check_large_class(node)

        return {
            "agent": "Java Code Analysis Agent",
            "findings": self.findings
        }

    def check_parameters(self, node):

        if len(node.parameters) > 5:

            self.findings.append(
                Finding(
                    issue="Too Many Parameters",
                    severity="Low",
                    line=node.position.line if node.position else 0,
                    message=f"Method '{node.name}' has {len(node.parameters)} parameters."
                ).to_dict()
            )

    def check_large_class(self, node):

        methods = []

        for member in node.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                methods.append(member)

        if len(methods) > 10:

            self.findings.append(
                Finding(
                    issue="Large Class",
                    severity="Medium",
                    line=node.position.line if node.position else 0,
                    message=f"Class '{node.name}' contains {len(methods)} methods."
                ).to_dict()
            )

    def check_long_method(self, node):

        if node.body and len(node.body) > 20:

            self.findings.append(
                Finding(
                    issue="Long Method",
                    severity="Medium",
                    line=node.position.line if node.position else 0,
                    message=f"Method '{node.name}' contains {len(node.body)} statements."
                ).to_dict()
            )
    def check_deep_nesting(self, node):

        max_depth = self.get_nesting_depth(node.body)

        if max_depth >= 4:

            self.findings.append(
                Finding(
                    issue="Deep Nesting",
                    severity="Medium",
                    line=node.position.line if node.position else 0,
                    message=f"Method '{node.name}' has nesting depth of {max_depth}."
                ).to_dict()
            )
    def get_nesting_depth(self, statements, depth=0):

        if not statements:
            return depth

        max_depth = depth

        for stmt in statements:

            if isinstance(stmt, (javalang.tree.IfStatement,
                                javalang.tree.ForStatement,
                                javalang.tree.WhileStatement,
                                javalang.tree.DoStatement,
                                javalang.tree.SwitchStatement)):

                children = []

                if hasattr(stmt, "then_statement") and stmt.then_statement:
                    children.append(stmt.then_statement)

                if hasattr(stmt, "body") and stmt.body:
                    children.append(stmt.body)

                current_depth = depth + 1

                for child in children:
                    if hasattr(child, "statements"):
                        current_depth = max(
                            current_depth,
                            self.get_nesting_depth(child.statements, depth + 1)
                        )

                max_depth = max(max_depth, current_depth)

        return max_depth
    def check_cyclomatic_complexity(self, node):

        complexity = 1

        for _, child in node:

            if isinstance(child, (
                javalang.tree.IfStatement,
                javalang.tree.ForStatement,
                javalang.tree.WhileStatement,
                javalang.tree.DoStatement,
                javalang.tree.SwitchStatement,
                javalang.tree.CatchClause,
                javalang.tree.TernaryExpression
            )):
                complexity += 1

        if complexity >= 10:

            self.findings.append(
                Finding(
                    issue="High Cyclomatic Complexity",
                    severity="High",
                    line=node.position.line if node.position else 0,
                    message=f"Method '{node.name}' has cyclomatic complexity of {complexity}."
                ).to_dict()
            )