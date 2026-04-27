"""
Centralized configuration for the JD-to-Resume RAG system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Fallback: Load from Streamlit secrets if not in environment
if "OPENAI_API_KEY" not in os.environ:
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

# ─── Configuration ─────────────────────────────────────────────────────────────
ADMIN_EMAIL = "saifimd1234@gmail.com"

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = ROOT_DIR / "knowledge_base"
VECTOR_DB_DIR = str(ROOT_DIR / "vector_db")
PUBLIC_DIR = ROOT_DIR / "public"

# ─── OpenAI Models ──────────────────────────────────────────────────────────
GENERATION_MODELS = {
    "gpt-4.1-nano (Fast & Cheap)": "gpt-4.1-nano",
    "gpt-4.1-mini (Balanced)": "gpt-4.1-mini",
    "gpt-4.1 (Best Quality)": "gpt-4.1",
}

EMBEDDING_MODELS = {
    "text-embedding-3-large (Best)": "text-embedding-3-large",
    "text-embedding-3-small (Fast)": "text-embedding-3-small",
}

# Defaults
DEFAULT_GENERATION_MODEL = "gpt-4.1-nano"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"

# ─── RAG Parameters ─────────────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
RETRIEVAL_K = 10

# ─── Resume Templates ───────────────────────────────────────────────────────
RESUME_TEMPLATES = {
    "Minimal": "minimal",
    "Corporate": "corporate",
    "Modern": "modern",
}

# Template PDF previews (stored in public/)
TEMPLATE_PREVIEWS = {
    "Corporate": "corporate.pdf",
}

# ─── Constraints ─────────────────────────────────────────────────────────────
MAX_JD_CHARACTERS = 10000
