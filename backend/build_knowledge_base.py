import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PDF_FOLDER = "knowledge_base/owasp"
CHROMA_DB = "knowledge_base/chroma_db"


def load_documents():
    documents = []

    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf"):
            path = os.path.join(PDF_FOLDER, filename)

            loader = PyPDFLoader(path)
            documents.extend(loader.load())

    return documents

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    return chunks

def create_embeddings():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return embeddings

def create_vector_database(chunks):
    embeddings = create_embeddings()

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB
    )

    return vector_db

def test_retrieval():
    embeddings = create_embeddings()

    vector_db = Chroma(
        persist_directory=CHROMA_DB,
        embedding_function=embeddings
    )

    query = "How can I prevent SQL Injection?"

    results = vector_db.similarity_search(query, k=3)

    print("\n===== Retrieval Results =====\n")

    for i, doc in enumerate(results, start=1):
        print(f"Result {i}")
        print("-" * 50)
        print("Source:", doc.metadata["source"])
        print(doc.page_content[:500])
        print()

if __name__ == "__main__":
    docs = load_documents()

    chunks = split_documents(docs)

    print(f"Loaded Pages : {len(docs)}")
    print(f"Chunks Created : {len(chunks)}")

    print("\nCreating Vector Database...")

    vector_db = create_vector_database(chunks)

    print("Knowledge Base Created Successfully!")

    test_retrieval()