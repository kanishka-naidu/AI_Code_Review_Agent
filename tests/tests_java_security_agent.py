import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.agents.java_security_agent import JavaSecurityAgent

code = """
import java.util.Random;

public class Demo {

    public void generate() {

        Random random = new Random();

    }

}
"""

agent = JavaSecurityAgent()

print(agent.analyze(code))