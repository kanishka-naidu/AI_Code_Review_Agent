from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DB = "knowledge_base/chroma_db"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_db = Chroma(
    persist_directory=CHROMA_DB,
    embedding_function=embeddings
)


def retrieve_context(query):
    results = vector_db.similarity_search(query, k=3)

    context = ""

    for doc in results:
        context += doc.page_content + "\n\n"

    return context

if __name__ == "__main__":
    context = retrieve_context("How to prevent SQL Injection?")

    print(context)