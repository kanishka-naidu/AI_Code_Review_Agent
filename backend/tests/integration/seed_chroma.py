"""Helper to seed a minimal Chroma DB used by integration tests.

This script attempts to import chromadb and create a persistent collection in the
provided directory. It writes a couple of small documents representing OWASP snippets.
If chromadb is not installed, it raises ImportError so tests can skip.
"""
from __future__ import annotations

from typing import List


def seed_chroma(persistence_dir: str) -> None:
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except Exception as e:
        raise ImportError("chromadb is required to seed database: %s" % e)

    # Use Chroma client with a persistent directory (duckdb+parquet backend when available)
    try:
        client = chromadb.Client(chromadb.config.Settings(persist_directory=persistence_dir, chroma_db_impl="duckdb+parquet"))
    except Exception:
        # Fallback to default settings
        client = chromadb.Client()

    # create or get collection
    from app.core.config import get_settings
    settings = get_settings()
    collection_name = settings.rag_collection or "owasp_kb"
    collection = client.get_or_create_collection(name=collection_name)

    docs = [
        {
            "id": "owasp-1",
            "text": "SQL Injection occurs when untrusted input is concatenated into SQL queries.",
            "meta": {"topic": "sql_injection"},
        },
        {
            "id": "owasp-2",
            "text": "Cross-site scripting (XSS) arises when output is not properly escaped.",
            "meta": {"topic": "xss"},
        },
    ]

    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metadatas = [d["meta"] for d in docs]

    # persist
    collection.add(ids=ids, documents=texts, metadatas=metadatas)

    # flush to disk if supported
    try:
        client.persist()
    except Exception:
        pass
