"""
Retriever: Query the FAISS vector store per user with caching for performance.
"""

import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from backend.config import VECTOR_DB_DIR, DEFAULT_EMBEDDING_MODEL, RETRIEVAL_K
from backend.ingest import get_user_vector_dir

# ─── Cached Singleton ──────────────────────────────────────────────────────

_vectorstore_cache = {}
_embeddings_cache = {}


def _get_embeddings(embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> OpenAIEmbeddings:
    """Get cached embedding function."""
    if embedding_model not in _embeddings_cache:
        _embeddings_cache[embedding_model] = OpenAIEmbeddings(model=embedding_model)
    return _embeddings_cache[embedding_model]


def get_vectorstore(user_id: int, embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> FAISS:
    """Load the persisted FAISS vector store for a specific user."""
    vector_dir = get_user_vector_dir(user_id)
    index_path = os.path.join(vector_dir, "index.faiss")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"Vector DB not found at '{vector_dir}'. "
            "Run ingestion first."
        )

    cache_key = f"{user_id}_{embedding_model}"
    if cache_key not in _vectorstore_cache:
        embeddings = _get_embeddings(embedding_model)
        _vectorstore_cache[cache_key] = FAISS.load_local(
            vector_dir,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return _vectorstore_cache[cache_key]


def clear_cache_for_user(user_id: int):
    """Clear the vectorstore cache for a specific user (call after re-ingestion)."""
    keys_to_remove = [k for k in _vectorstore_cache.keys() if k.startswith(f"{user_id}_")]
    for k in keys_to_remove:
        del _vectorstore_cache[k]


def clear_cache():
    """Clear all vectorstore caches."""
    _vectorstore_cache.clear()


def retrieve_relevant_chunks(
    user_id: int,
    jd_text: str,
    k: int = RETRIEVAL_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[Document]:
    """Retrieve the top-K most relevant chunks for a user."""
    vectorstore = get_vectorstore(user_id, embedding_model)
    return vectorstore.similarity_search(jd_text, k=k)


def retrieve_with_scores(
    user_id: int,
    jd_text: str,
    k: int = RETRIEVAL_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[tuple[Document, float]]:
    """Retrieve chunks with similarity scores (higher = more similar) for a user."""
    vectorstore = get_vectorstore(user_id, embedding_model)
    results = vectorstore.similarity_search_with_score(jd_text, k=k)

    scored_results = []
    for doc, distance in results:
        similarity = 1.0 / (1.0 + distance)
        scored_results.append((doc, similarity))
    return scored_results


def retrieve_by_category(
    user_id: int,
    jd_text: str,
    category: str,
    k: int = 5,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[Document]:
    """Retrieve chunks filtered by doc_type category for a user."""
    vectorstore = get_vectorstore(user_id, embedding_model)
    results = vectorstore.similarity_search(jd_text, k=k * 5)
    filtered = [doc for doc in results if doc.metadata.get("doc_type") == category]
    return filtered[:k]


def get_all_categories_for_user(user_id: int, embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> list[str]:
    """Get all unique document categories for a user."""
    try:
        vectorstore = get_vectorstore(user_id, embedding_model)
        categories = set()
        for doc_id in vectorstore.docstore._dict:
            doc = vectorstore.docstore._dict[doc_id]
            if hasattr(doc, "metadata") and "doc_type" in doc.metadata:
                categories.add(doc.metadata["doc_type"])
        return sorted(categories)
    except FileNotFoundError:
        return []


def get_chunk_count_for_user(user_id: int, embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Get total number of chunks in the vector store for a user."""
    try:
        vectorstore = get_vectorstore(user_id, embedding_model)
        return vectorstore.index.ntotal
    except FileNotFoundError:
        return 0
