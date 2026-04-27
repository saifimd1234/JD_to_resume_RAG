"""
Ingestion pipeline: Load KB documents from SQLite, chunk, embed into FAISS per user.
"""

import os
import json
from pathlib import Path
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from backend.config import (
    VECTOR_DB_DIR,
    DEFAULT_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from backend.database import get_kb_entries

def get_user_vector_dir(user_id: int) -> str:
    """Get the specific FAISS directory for a user."""
    return os.path.join(VECTOR_DB_DIR, f"user_{user_id}")

def get_user_metadata_file(user_id: int) -> str:
    """Get the specific metadata file for a user."""
    return os.path.join(get_user_vector_dir(user_id), "kb_metadata.json")

def get_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL) -> OpenAIEmbeddings:
    """Get embedding function."""
    return OpenAIEmbeddings(model=model_name)

def get_kb_metadata(user_id: int) -> dict:
    """Load KB metadata for a user."""
    meta_file = get_user_metadata_file(user_id)
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            return json.load(f)
    return {}

def _save_kb_metadata(user_id: int, stats: dict):
    """Save KB metadata after ingestion."""
    meta_file = get_user_metadata_file(user_id)
    metadata = {
        "last_ingestion": datetime.now().isoformat(),
        "stats": stats,
    }
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

def check_kb_changes(user_id: int) -> dict:
    """
    Check if any KB entries have changed since last ingestion.
    """
    metadata = get_kb_metadata(user_id)
    last_ingestion_str = metadata.get("last_ingestion")
    
    entries = get_kb_entries(user_id)
    has_changes = False
    
    if not last_ingestion_str:
        has_changes = len(entries) > 0
    else:
        last_ingestion = datetime.fromisoformat(last_ingestion_str)
        for entry in entries:
            # updated_at from sqlite is string, we need to compare safely
            updated_at = datetime.fromisoformat(entry['updated_at'])
            if updated_at > last_ingestion:
                has_changes = True
                break
                
    return {
        "has_changes": has_changes,
        "total_files": len(entries),
    }

def fetch_documents(user_id: int) -> list:
    """Load all markdown entries from SQLite for this user."""
    entries = get_kb_entries(user_id)
    documents = []

    for entry in entries:
        content = f"# {entry['title']}\n"
        if entry['github_url']:
            content += f"GitHub URL: {entry['github_url']}\n"
        content += f"\n{entry['content']}"
        
        doc = Document(
            page_content=content,
            metadata={
                "doc_type": entry["category"],
                "title": entry["title"],
                "github_url": entry["github_url"] or ""
            }
        )
        documents.append(doc)

    print(f"Loaded {len(documents)} entries for user {user_id}")
    return documents

def create_chunks(
    documents: list,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list:
    """Split documents into chunks."""
    if not documents:
        return []
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks

def create_vector_store(
    user_id: int,
    chunks: list,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> FAISS:
    """Embed chunks and persist to user's FAISS directory."""
    vector_dir = get_user_vector_dir(user_id)
    os.makedirs(vector_dir, exist_ok=True)
    
    if not chunks:
        # If chunks is empty, we create a dummy FAISS index to avoid errors, or just return None
        return None
        
    embeddings = get_embeddings(embedding_model)
    vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
    vectorstore.save_local(vector_dir)
    print(f"Vector store saved: {len(chunks):,} vectors at '{vector_dir}'")
    return vectorstore

def run_ingestion(
    user_id: int,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> dict:
    """Full ingestion pipeline: load from DB → chunk → embed → save."""
    # Clear retriever cache for this user
    from backend.retriever import clear_cache_for_user
    clear_cache_for_user(user_id)

    documents = fetch_documents(user_id)
    chunks = create_chunks(documents, chunk_size, chunk_overlap)
    
    vector_dir = get_user_vector_dir(user_id)
    os.makedirs(vector_dir, exist_ok=True)
    
    if not chunks:
        stats = {
            "status": "empty",
            "documents_loaded": 0,
            "chunks_created": 0,
            "vectors_stored": 0,
        }
    else:
        create_vector_store(user_id, chunks, embedding_model)
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
    _save_kb_metadata(user_id, stats)
    return stats
