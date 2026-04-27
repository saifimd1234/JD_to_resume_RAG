"""
Retriever: Query the FAISS vector store with caching for performance.
"""

import os
import functools
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from backend.config import VECTOR_DB_DIR, DEFAULT_EMBEDDING_MODEL, RETRIEVAL_K

# ─── Cached Singleton ──────────────────────────────────────────────────────

_vectorstore_cache = {}
_embeddings_cache = {}


def _get_embeddings(embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> OpenAIEmbeddings:
    """Get cached embedding function."""
    if embedding_model not in _embeddings_cache:
        _embeddings_cache[embedding_model] = OpenAIEmbeddings(model=embedding_model)
    return _embeddings_cache[embedding_model]


def get_vectorstore(embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> FAISS:
    """Load the persisted FAISS vector store (cached after first load)."""
    index_path = os.path.join(VECTOR_DB_DIR, "index.faiss")
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"Vector DB not found at '{VECTOR_DB_DIR}'. "
            "Run ingestion first."
        )

    if embedding_model not in _vectorstore_cache:
        embeddings = _get_embeddings(embedding_model)
        _vectorstore_cache[embedding_model] = FAISS.load_local(
            VECTOR_DB_DIR,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return _vectorstore_cache[embedding_model]


def clear_cache():
    """Clear the vectorstore cache (call after re-ingestion)."""
    _vectorstore_cache.clear()


def retrieve_relevant_chunks(
    jd_text: str,
    k: int = RETRIEVAL_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[Document]:
    """Retrieve the top-K most relevant chunks."""
    vectorstore = get_vectorstore(embedding_model)
    return vectorstore.similarity_search(jd_text, k=k)


def retrieve_with_scores(
    jd_text: str,
    k: int = RETRIEVAL_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[tuple[Document, float]]:
    """Retrieve chunks with similarity scores (higher = more similar)."""
    vectorstore = get_vectorstore(embedding_model)
    results = vectorstore.similarity_search_with_score(jd_text, k=k)

    scored_results = []
    for doc, distance in results:
        similarity = 1.0 / (1.0 + distance)
        scored_results.append((doc, similarity))
    return scored_results


def retrieve_by_category(
    jd_text: str,
    category: str,
    k: int = 5,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[Document]:
    """Retrieve chunks filtered by doc_type category."""
    vectorstore = get_vectorstore(embedding_model)
    results = vectorstore.similarity_search(jd_text, k=k * 5)
    filtered = [doc for doc in results if doc.metadata.get("doc_type") == category]
    return filtered[:k]


def get_all_categories(embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> list[str]:
    """Get all unique document categories."""
    try:
        vectorstore = get_vectorstore(embedding_model)
        categories = set()
        for doc_id in vectorstore.docstore._dict:
            doc = vectorstore.docstore._dict[doc_id]
            if hasattr(doc, "metadata") and "doc_type" in doc.metadata:
                categories.add(doc.metadata["doc_type"])
        return sorted(categories)
    except FileNotFoundError:
        return []


def get_chunk_count(embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Get total number of chunks in the vector store."""
    try:
        vectorstore = get_vectorstore(embedding_model)
        return vectorstore.index.ntotal
    except FileNotFoundError:
        return 0
