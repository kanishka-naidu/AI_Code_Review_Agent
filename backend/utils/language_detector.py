import ast


class LanguageDetector:

    @staticmethod
    def detect(code: str):

        # Try Python
        try:
            ast.parse(code)
            return "Python"
        except SyntaxError:
            pass

        # Try Java
        java_keywords = [
            "public class",
            "class",
            "public static void main",
            "System.out.println",
            "import java"
        ]

        if any(keyword in code for keyword in java_keywords):
            return "Java"

        return "Unknown"