"""
Ingestion pipeline: Load KB documents, chunk, embed into FAISS.
Includes KB metadata tracking for versioning.
"""

import os
import glob
import json
from pathlib import Path
from datetime import datetime

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from backend.config import (
    KNOWLEDGE_BASE_DIR,
    VECTOR_DB_DIR,
    DEFAULT_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

KB_METADATA_FILE = os.path.join(VECTOR_DB_DIR, "kb_metadata.json")


def get_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL) -> OpenAIEmbeddings:
    """Get embedding function."""
    return OpenAIEmbeddings(model=model_name)


def _get_file_timestamps() -> dict:
    """Get last-modified timestamps for all KB files."""
    timestamps = {}
    for md_file in KNOWLEDGE_BASE_DIR.rglob("*.md"):
        rel_path = str(md_file.relative_to(KNOWLEDGE_BASE_DIR))
        timestamps[rel_path] = os.path.getmtime(md_file)
    return timestamps


def get_kb_metadata() -> dict:
    """Load KB metadata (last ingestion info)."""
    if os.path.exists(KB_METADATA_FILE):
        with open(KB_METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_kb_metadata(stats: dict, file_timestamps: dict):
    """Save KB metadata after ingestion."""
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    metadata = {
        "last_ingestion": datetime.now().isoformat(),
        "stats": stats,
        "file_timestamps": file_timestamps,
    }
    with open(KB_METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def check_kb_changes() -> dict:
    """
    Check if KB files have changed since last ingestion.
    Returns dict with: has_changes, new_files, modified_files, deleted_files
    """
    current_timestamps = _get_file_timestamps()
    metadata = get_kb_metadata()
    old_timestamps = metadata.get("file_timestamps", {})

    new_files = [f for f in current_timestamps if f not in old_timestamps]
    deleted_files = [f for f in old_timestamps if f not in current_timestamps]
    modified_files = [
        f for f in current_timestamps
        if f in old_timestamps and current_timestamps[f] != old_timestamps[f]
    ]

    return {
        "has_changes": bool(new_files or modified_files or deleted_files),
        "new_files": new_files,
        "modified_files": modified_files,
        "deleted_files": deleted_files,
        "total_files": len(current_timestamps),
    }


def fetch_documents() -> list:
    """Load all markdown files from the knowledge base."""
    folders = glob.glob(str(KNOWLEDGE_BASE_DIR / "*"))
    documents = []

    for folder in folders:
        if not os.path.isdir(folder):
            continue
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)

    print(f"Loaded {len(documents)} documents from {len(folders)} folders")
    return documents


def create_chunks(
    documents: list,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list:
    """Split documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def create_vector_store(
    chunks: list,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> FAISS:
    """Embed chunks and persist to FAISS."""
    embeddings = get_embeddings(embedding_model)
    vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
    vectorstore.save_local(VECTOR_DB_DIR)
    print(f"Vector store saved: {len(chunks):,} vectors at '{VECTOR_DB_DIR}'")
    return vectorstore


def run_ingestion(
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> dict:
    """Full ingestion pipeline: load → chunk → embed → save."""
    # Clear retriever cache
    from backend.retriever import clear_cache
    clear_cache()

    documents = fetch_documents()
    chunks = create_chunks(documents, chunk_size, chunk_overlap)
    create_vector_store(chunks, embedding_model)

    stats = {
        "status": "success",
        "documents_loaded": len(documents),
        "chunks_created": len(chunks),
        "vectors_stored": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": embedding_model,
    }

    # Save metadata for versioning
    _save_kb_metadata(stats, _get_file_timestamps())

    return stats


if __name__ == "__main__":
    stats = run_ingestion()
    print(f"\n✅ Ingestion complete!")
    for key, value in stats.items():
        print(f"  {key}: {value}")
