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
    "gpt-4o-mini (Fast & Cheap)": "gpt-4o-mini",
    "gpt-3.5-turbo (Balanced)": "gpt-3.5-turbo",
    "gpt-4o (Best Quality)": "gpt-4o",
}

EMBEDDING_MODELS = {
    "text-embedding-3-large (Best)": "text-embedding-3-large",
    "text-embedding-3-small (Fast)": "text-embedding-3-small",
}

# Defaults
DEFAULT_GENERATION_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"

# ─── RAG Parameters ─────────────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
RETRIEVAL_K = 10

# ─── Resume Templates ───────────────────────────────────────────────────────
TEMPLATES_DIR = ROOT_DIR / "templates"

RESUME_TEMPLATES = {
    "Harvard Resume": "harvard_resume",
    "ATS Professional": "ats_professional",
    "Modern Executive": "modern_executive",
    "Minimal Corporate": "minimal_corporate",
    "Software Engineer Template": "software_engineer",
}

# Template PDF previews (stored in public/)
TEMPLATE_PREVIEWS = {
    "Harvard Resume": "harvard_resume.pdf",
    "ATS Professional": "ats_professional.pdf",
    "Modern Executive": "modern_executive.pdf",
    "Minimal Corporate": "minimal_corporate.pdf",
    "Software Engineer Template": "software_engineer.pdf",
}

# ─── Constraints ─────────────────────────────────────────────────────────────
MAX_JD_CHARACTERS = 10000
