import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from backend.agents.java_code_analysis_agent import JavaCodeAnalysisAgent

code = """
public class Student {

    void m1(){}
    void m2(){}
    void m3(){}
    void m4(){}
    void m5(){}
    void m6(){}
    void m7(){}
    void m8(){}
    void m9(){}
    void m10(){}
    void m11(){}

    public int calculate(
    int a,
    int b,
    int c,
    int d,
    int e,
    int f,
    int g
){

    if(a > 0){}
    if(b > 0){}
    if(c > 0){}
    if(d > 0){}
    if(e > 0){}

    for(int i=0;i<10;i++){}

    while(f > 0){
        f--;
    }

    do{
        g--;
    }while(g > 0);

    switch(a){
        case 1: break;
        case 2: break;
        default: break;
    }

    try{
        int x = 10/0;
    }catch(Exception ex){
    }

    return a+b;
}{
        return a+b;
    }

}
"""

agent = JavaCodeAnalysisAgent()

print(agent.analyze(code))