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
from backend.database import get_kb_entries, get_kb_documents, update_kb_document_stats

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

def _extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract plain text from PDF, TXT, or MD files."""
    if not os.path.exists(file_path):
        return ""
        
    ext = file_path.lower().split('.')[-1]
    text = ""
    
    if ext == 'pdf' or 'pdf' in file_type:
        try:
            import pypdf
            pdf_reader = pypdf.PdfReader(file_path)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"Error parsing PDF file {file_path}: {e}")
    elif ext in ['txt', 'md', 'markdown'] or 'text' in file_type:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
    else:
        # Fallback to reading as text
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            pass
            
    return text.strip()

def fetch_documents(user_id: int) -> list:
    """Load all entries and documents from SQLite for this user."""
    entries = get_kb_entries(user_id)
    documents = []

    # 1. Load structured KB entries
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

    # 2. Load uploaded KB documents
    kb_docs = get_kb_documents(user_id)
    for doc_item in kb_docs:
        file_path = doc_item["file_path"]
        if os.path.exists(file_path):
            text = _extract_text_from_file(file_path, doc_item["file_type"])
            if text:
                content = f"# DOCUMENT: {doc_item['file_name']}\n\n{text}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "doc_type": "document",
                        "title": doc_item["file_name"],
                        "github_url": ""
                    }
                )
                documents.append(doc)

    print(f"Loaded {len(documents)} total documents for user {user_id}")
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
        
        # Count chunks per document and update stats in DB
        doc_chunk_counts = {}
        for chunk in chunks:
            if chunk.metadata.get("doc_type") == "document":
                doc_title = chunk.metadata.get("title")
                doc_chunk_counts[doc_title] = doc_chunk_counts.get(doc_title, 0) + 1
                
        kb_docs = get_kb_documents(user_id)
        for kb_doc in kb_docs:
            title = kb_doc["file_name"]
            count = doc_chunk_counts.get(title, 0)
            update_kb_document_stats(kb_doc["id"], user_id, count, embedding_model)

    # Save metadata for versioning
    _save_kb_metadata(user_id, stats)
    return stats
