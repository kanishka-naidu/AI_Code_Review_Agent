import ast
from backend.models.finding import Finding


class CodeAnalysisAgent:
    def __init__(self):
        self.findings = []

    def analyze(self, code: str):
        self.findings = []

        try:
            tree = ast.parse(code)

        except SyntaxError as e:
            return {
                "agent": "Code Analysis Agent",
                "findings": [
                    Finding(
                        issue="Syntax Error",
                        severity="High",
                        line=e.lineno,
                        message=str(e)
                    ).to_dict()
                ]
            }

        for node in ast.walk(tree):

            # Long Function
            if isinstance(node, ast.FunctionDef):
                self.check_long_function(node)

            # Too Many Parameters
            if isinstance(node, ast.FunctionDef):
                self.check_parameters(node)

            # Missing Docstring
            if isinstance(node, ast.FunctionDef):
                self.check_docstring(node)

            # Large Class
            if isinstance(node, ast.ClassDef):
                self.check_large_class(node)

            # Deep Nesting
            if isinstance(node, ast.FunctionDef):
                self.check_deep_nesting(node)

            # Cyclomatic Complexity
            if isinstance(node, ast.FunctionDef):
                self.check_complexity(node)

        return {
            "agent": "Code Analysis Agent",
            "findings": self.findings
        }

    def check_long_function(self, node):
        if hasattr(node, "end_lineno"):

            length = node.end_lineno - node.lineno

            if length > 30:
                self.findings.append(
                    Finding(
                        issue="Long Function",
                        severity="Medium",
                        line=node.lineno,
                        message=f"Function '{node.name}' has {length} lines."
                    ).to_dict()
                )

    def check_parameters(self, node):
        if len(node.args.args) > 5:

            self.findings.append(
                Finding(
                    issue="Too Many Parameters",
                    severity="Low",
                    line=node.lineno,
                    message=f"Function '{node.name}' has {len(node.args.args)} parameters."
                ).to_dict()
            )

    def check_docstring(self, node):
        if ast.get_docstring(node) is None:

            self.findings.append(
                Finding(
                    issue="Missing Docstring",
                    severity="Low",
                    line=node.lineno,
                    message=f"Function '{node.name}' has no docstring."
                ).to_dict()
            )

    def check_large_class(self, node):

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        if len(methods) > 10:

            self.findings.append(
                Finding(
                    issue="Large Class",
                    severity="Medium",
                    line=node.lineno,
                    message=f"Class '{node.name}' contains {len(methods)} methods."
                ).to_dict()
            )

    def check_deep_nesting(self, node):

        max_depth = self.get_max_depth(node)

        if max_depth > 3:

            self.findings.append(
                Finding(
                    issue="Deep Nesting",
                    severity="Medium",
                    line=node.lineno,
                    message=f"Function '{node.name}' has nesting depth of {max_depth}."
                ).to_dict()
            )

    def get_max_depth(self, node, depth=0):

        max_depth = depth

        for child in ast.iter_child_nodes(node):

            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):

                max_depth = max(
                    max_depth,
                    self.get_max_depth(child, depth + 1)
                )

            else:

                max_depth = max(
                    max_depth,
                    self.get_max_depth(child, depth)
                )

        return max_depth

    def check_complexity(self, node):

        complexity = self.calculate_complexity(node)

        if complexity >= 10:

            self.findings.append(
                Finding(
                    issue="High Cyclomatic Complexity",
                    severity="Medium",
                    line=node.lineno,
                    message=f"Function '{node.name}' has complexity of {complexity}."
                ).to_dict()
            )

    def calculate_complexity(self, node):

        complexity = 1

        decision_nodes = (
            ast.If,
            ast.For,
            ast.While,
            ast.Try,
            ast.ExceptHandler,
            ast.With,
            ast.BoolOp,
            ast.IfExp,
            ast.Match
        )

        for child in ast.walk(node):

            if isinstance(child, decision_nodes):
                complexity += 1

        return complexity