"""
Evaluator Page — Tune RAG parameters and inspect retrieval quality.
(Phase 3 — Basic implementation)
"""

import sys
from pathlib import Path

# Add root to path (one level up from pages/)
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from utils.styles import get_custom_css
from backend.config import (
    EMBEDDING_MODELS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RETRIEVAL_K,
)
from backend.retriever import get_chunk_count_for_user, retrieve_with_scores
from backend.ingest import run_ingestion


# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Evaluator | ResumeForge AI",
    page_icon="🧪",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth State ──────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user_id = st.session_state.user['id']

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("# 🧪 RAG Evaluator")
st.markdown("Tune retrieval parameters and inspect chunk quality for your queries.")
st.markdown("---")


# ─── Parameters ─────────────────────────────────────────────────────────────
st.markdown("## ⚙️ RAG Parameters")

param_col1, param_col2, param_col3, param_col4 = st.columns(4)

with param_col1:
    eval_chunk_size = st.slider(
        "Chunk Size",
        min_value=100,
        max_value=2000,
        value=CHUNK_SIZE,
        step=50,
        key="eval_chunk_size",
    )

with param_col2:
    eval_chunk_overlap = st.slider(
        "Chunk Overlap",
        min_value=0,
        max_value=500,
        value=CHUNK_OVERLAP,
        step=25,
        key="eval_chunk_overlap",
    )

with param_col3:
    eval_top_k = st.slider(
        "Top-K Retrieval",
        min_value=1,
        max_value=30,
        value=RETRIEVAL_K,
        key="eval_top_k",
    )

with param_col4:
    eval_embedding = st.selectbox(
        "Embedding Model",
        options=list(EMBEDDING_MODELS.keys()),
        key="eval_embedding",
    )

# ─── Re-Ingest with Custom Params ──────────────────────────────────────────
st.markdown("---")

if st.button("🔄 Re-Ingest with These Parameters", type="secondary", key="eval_reingest"):
    with st.spinner("Re-ingesting knowledge base with custom parameters..."):
        try:
            stats = run_ingestion(
                user_id=user_id,
                chunk_size=eval_chunk_size,
                chunk_overlap=eval_chunk_overlap,
                embedding_model=EMBEDDING_MODELS[eval_embedding],
            )
            st.success(
                f"✅ Re-ingestion complete! "
                f"{stats['chunks_created']} chunks → {stats['vectors_stored']} vectors"
            )
        except Exception as e:
            st.error(f"❌ Re-ingestion failed: {str(e)}")


# ─── Query Test ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🔍 Retrieval Test")

test_query = st.text_area(
    "Enter a test query or JD snippet",
    height=120,
    placeholder="E.g., 'Looking for a Data Engineer with experience in Apache Spark and Kafka...'",
    key="eval_query",
)

if st.button("🔎 Test Retrieval", type="primary", key="eval_search", disabled=not test_query):
    chunk_count = get_chunk_count_for_user(user_id)

    if chunk_count == 0:
        st.warning("⚠️ Vector database is empty. Run ingestion first.")
    else:
        with st.spinner("Retrieving relevant chunks..."):
            try:
                results = retrieve_with_scores(
                    user_id=user_id,
                    jd_text=test_query,
                    k=eval_top_k,
                    embedding_model=EMBEDDING_MODELS[eval_embedding],
                )

                st.success(f"✅ Retrieved {len(results)} chunks")

                # Metrics
                if results:
                    scores = [score for _, score in results]
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric("Chunks Found", len(results))
                    m_col2.metric("Avg Score", f"{sum(scores)/len(scores):.4f}")
                    m_col3.metric("Best Score", f"{max(scores):.4f}")
                    m_col4.metric("Worst Score", f"{min(scores):.4f}")

                st.markdown("---")

                # Display each chunk
                for i, (doc, score) in enumerate(results, 1):
                    doc_type = doc.metadata.get("doc_type", "unknown")

                    # Color code by score
                    if score > 0.5:
                        badge_color = "#00c853"
                        badge_bg = "rgba(0,200,83,0.1)"
                    elif score > 0.3:
                        badge_color = "#ffab00"
                        badge_bg = "rgba(255,171,0,0.1)"
                    else:
                        badge_color = "#ff6b6b"
                        badge_bg = "rgba(255,107,107,0.1)"

                    with st.container():
                        st.markdown(
                            f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); "
                            f"border-radius:12px; padding:16px; margin-bottom:12px;'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>"
                            f"<span style='font-weight:700; color:#e0e0ff;'>#{i}</span>"
                            f"<span style='background:rgba(123,47,247,0.15); color:#b0b0d0; padding:2px 10px; "
                            f"border-radius:12px; font-size:0.8rem;'>{doc_type}</span>"
                            f"<span style='background:{badge_bg}; color:{badge_color}; padding:2px 10px; "
                            f"border-radius:12px; font-size:0.8rem; font-weight:600;'>Score: {score:.4f}</span>"
                            f"</div>"
                            f"<div style='color:#b0b0d0; font-size:0.88rem; line-height:1.5;'>"
                            f"{doc.page_content}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            except Exception as e:
                st.error(f"❌ Retrieval failed: {str(e)}")

# ─── Empty State ────────────────────────────────────────────────────────────
if not test_query:
    st.markdown(
        "<div style='text-align:center; padding:60px 20px; color:rgba(255,255,255,0.3);'>"
        "<div style='font-size:3rem; margin-bottom:10px;'>🧪</div>"
        "<div style='font-size:1.1rem;'>Enter a query above to test retrieval</div>"
        "<div style='font-size:0.85rem; margin-top:8px;'>"
        "Adjust parameters to see how chunk size, overlap, and top-K affect results"
        "</div></div>",
        unsafe_allow_html=True,
    )
