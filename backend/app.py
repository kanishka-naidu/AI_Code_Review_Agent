from fastapi import FastAPI, UploadFile, File
from backend.models.request_models import CodeSubmission
from backend.routes.analyzer import router as analyzer_router



import ast
import javalang


app = FastAPI()

app.include_router(analyzer_router)
@app.get("/")
def home():
    return {"message": "Backend is running!"}

@app.post("/submit-code")
def submit_code(data: CodeSubmission):

    # Empty code
    if not data.code.strip():
        return {
            "status": "error",
            "message": "Code cannot be empty"
        }

    # Supported language
    if data.language.lower() not in ["python", "java"]:
        return {
            "status": "error",
            "message": "Only Python and Java are supported"
        }

    # Python Syntax Validation
    if data.language.lower() == "python":
        try:
            ast.parse(data.code)
        except SyntaxError as e:
            return {
                "status": "error",
                "message": "Invalid Python syntax",
                "details": str(e)
            }

    # Java Syntax Validation
    if data.language.lower() == "java":
        try:
            javalang.parse.parse(data.code)
        except Exception as e:
            return {
                "status": "error",
                "message": "Invalid Java syntax",
                "details": str(e)
            }

        # Retrieve relevant OWASP context
    query = f"Review this {data.language} code for OWASP security vulnerabilities."

    context = retrieve_context(query)

    # Get AI review
    review = review_code(context, data.code)

    
        # Retrieve relevant OWASP context
    query = f"Review this {data.language} code for OWASP security vulnerabilities."

    context = retrieve_context(query)

    # Get AI review
    review = review_code(context, data.code)

    return {
        "status": "success",
        "language": data.language,
        "review": review
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Check file extension
    if not (file.filename.endswith(".py") or file.filename.endswith(".java")):
        return {
            "status": "error",
            "message": "Only .py and .java files are allowed"
        }

    # Read uploaded file
    content = await file.read()
    code = content.decode("utf-8")

    # Python Syntax Validation
    if file.filename.endswith(".py"):
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {
                "status": "error",
                "message": "Invalid Python syntax",
                "details": str(e)
            }

    # Java Syntax Validation
    if file.filename.endswith(".java"):
        try:
            javalang.parse.parse(code)
        except Exception as e:
            return {
                "status": "error",
                "message": "Invalid Java syntax",
                "details": str(e)
            }

        # Detect language
    language = "python" if file.filename.endswith(".py") else "java"

    # Retrieve OWASP context
    query = f"Review this {language} code for OWASP security vulnerabilities."

    context = retrieve_context(query)

    # AI review
    review = review_code(context, code)

    return {
        "status": "success",
        "filename": file.filename,
        "language": language,
        "review": review
    }