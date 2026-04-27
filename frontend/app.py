"""
ResumeForge AI — Main Streamlit Application
AI-Powered JD-to-Resume Generator using RAG
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from frontend.utils.styles import get_custom_css
from backend.retriever import get_chunk_count, get_all_categories
from backend.ingest import get_kb_metadata, check_kb_changes


# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResumeForge AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ResumeForge AI")
    st.markdown("---")

    st.markdown("### System Status")
    try:
        chunk_count = get_chunk_count()
        categories = get_all_categories()
        kb_meta = get_kb_metadata()
        kb_changes = check_kb_changes()

        if chunk_count > 0:
            st.markdown(
                '<span class="status-badge status-ready">Vector DB Ready</span>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            c1.metric("Chunks", f"{chunk_count:,}")
            c2.metric("Categories", len(categories))

            if kb_meta.get("last_ingestion"):
                st.caption(f"Last indexed: {kb_meta['last_ingestion'][:16]}")

            if kb_changes["has_changes"]:
                st.warning("Knowledge Base changed — rebuild recommended")

            with st.expander("Categories"):
                for cat in categories:
                    st.markdown(f"- `{cat}`")
        else:
            st.markdown(
                '<span class="status-badge status-empty">Vector DB Empty</span>',
                unsafe_allow_html=True,
            )
            st.info("Run ingestion on the **Generate Resume** page.")
    except Exception:
        st.markdown(
            '<span class="status-badge status-empty">Vector DB Not Found</span>',
            unsafe_allow_html=True,
        )
        st.info("Run ingestion to create the vector DB.")

    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("""
    - **Generate Resume** — JD → Resume
    - **Evaluator** — Tune RAG params
    """)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.75rem;'>"
        "Built with LangChain + FAISS + Streamlit</div>",
        unsafe_allow_html=True,
    )


# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# ResumeForge AI")
st.markdown("### AI-Powered Resume Generator using RAG")
st.markdown("---")

# Feature cards
f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("""
    <div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:20px; min-height:140px;'>
    <div style='font-size:1.8rem; margin-bottom:8px;'>[JD]</div>
    <div style='font-weight:700; color:#e0e0ff; margin-bottom:6px;'>Paste Your JD</div>
    <div style='color:#888; font-size:0.85rem;'>Paste any job description and get a perfectly tailored resume in seconds.</div>
    </div>""", unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:20px; min-height:140px;'>
    <div style='font-size:1.8rem; margin-bottom:8px;'>[ATS]</div>
    <div style='font-weight:700; color:#e0e0ff; margin-bottom:6px;'>ATS-Optimized</div>
    <div style='color:#888; font-size:0.85rem;'>Keyword-aligned resumes that pass ATS filters with gap analysis and scoring.</div>
    </div>""", unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:20px; min-height:140px;'>
    <div style='font-size:1.8rem; margin-bottom:8px;'>[Export]</div>
    <div style='font-weight:700; color:#e0e0ff; margin-bottom:6px;'>Export Anywhere</div>
    <div style='color:#888; font-size:0.85rem;'>Download as DOCX, PDF, or Markdown with professional formatting.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Quick Start
st.markdown("## Quick Start")
st.markdown("""
1. **Edit your Knowledge Base** — Update the `.md` files in `knowledge_base/` with your real data
2. **Run Ingestion** — Click "Rebuild Vector DB" on the Generate Resume page
3. **Paste a JD** — Enter a job description
4. **Generate & Analyze** — Get your tailored resume + gap analysis + ATS score
5. **Export** — Download as DOCX, PDF, or Markdown
""")

st.markdown("---")

# Phase 2 features highlight
st.markdown("## Phase 2 Features")

p1, p2, p3 = st.columns(3)

with p1:
    st.markdown("""
    <div style='background:rgba(123,47,247,0.06); border:1px solid rgba(123,47,247,0.15);
    border-radius:12px; padding:20px; min-height:120px;'>
    <div style='font-weight:700; color:#b0b0ff; margin-bottom:8px;'>Gap Analysis</div>
    <div style='color:#888; font-size:0.85rem;'>Compare JD requirements vs your KB. See matching, missing, and weak skills.</div>
    </div>""", unsafe_allow_html=True)

with p2:
    st.markdown("""
    <div style='background:rgba(0,212,255,0.06); border:1px solid rgba(0,212,255,0.15);
    border-radius:12px; padding:20px; min-height:120px;'>
    <div style='font-weight:700; color:#80e0ff; margin-bottom:8px;'>ATS Score</div>
    <div style='color:#888; font-size:0.85rem;'>Skills match, keyword density, formatting check, and experience relevance scoring.</div>
    </div>""", unsafe_allow_html=True)

with p3:
    st.markdown("""
    <div style='background:rgba(0,200,83,0.06); border:1px solid rgba(0,200,83,0.15);
    border-radius:12px; padding:20px; min-height:120px;'>
    <div style='font-weight:700; color:#80ffa0; margin-bottom:8px;'>Resume Upload</div>
    <div style='color:#888; font-size:0.85rem;'>Upload your existing resume as a reference for smarter generation.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

st.markdown(
    "<div style='text-align:center; color:rgba(255,255,255,0.4); padding:20px;'>"
    "Navigate to <b>Generate Resume</b> from the sidebar to get started →"
    "</div>",
    unsafe_allow_html=True,
)
