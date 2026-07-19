import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.utils.language_detector import LanguageDetector

python_code = """
def add(a, b):
    return a + b
"""

java_code = """
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""

print(LanguageDetector.detect(python_code))
print(LanguageDetector.detect(java_code))