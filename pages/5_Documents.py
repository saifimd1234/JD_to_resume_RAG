import sys
import os
from pathlib import Path
import streamlit as st

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import add_user_document, get_user_documents, delete_user_document
from utils.styles import get_custom_css

st.set_page_config(
    page_title="Documents | ResumeForge AI",
    page_icon="📄",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user_id = st.session_state.user['id']

USER_DOCS_DIR = Path(__file__).parent.parent / "data" / "user_docs" / str(user_id)
os.makedirs(USER_DOCS_DIR, exist_ok=True)

# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# Manage Documents")
st.markdown("Upload and manage documents to attach to your CV later (e.g., certifications, portfolios).")
st.markdown("---")

# ─── Upload Section ────────────────────────────────────────────────────────
with st.form("upload_doc_form", clear_on_submit=True):
    st.markdown("### Upload New Document")
    doc_title = st.text_input("Document Title *", placeholder="e.g., AWS Architect Certificate")
    uploaded_file = st.file_uploader("Select File (PDF, Image) *", type=["pdf", "png", "jpg", "jpeg"])
    
    submit_doc = st.form_submit_button("Upload Document")
    
    if submit_doc:
        if not doc_title.strip() or not uploaded_file:
            st.error("Please provide a title and select a file.")
        else:
            file_type = uploaded_file.type
            # Secure filename
            import re
            safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', uploaded_file.name)
            # Add timestamp to ensure uniqueness
            import time
            unique_filename = f"{int(time.time())}_{safe_filename}"
            file_path = USER_DOCS_DIR / unique_filename
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            add_user_document(user_id, doc_title.strip(), str(file_path), file_type)
            st.success(f"Document '{doc_title}' uploaded successfully!")
            st.rerun()

st.markdown("---")
st.markdown("### Your Documents")

docs = get_user_documents(user_id)

if not docs:
    st.info("You haven't uploaded any documents yet.")
else:
    for doc in docs:
        col_title, col_type, col_action = st.columns([4, 2, 1])
        with col_title:
            st.markdown(f"**{doc['title']}**")
        with col_type:
            st.caption(f"Type: {doc['file_type'].split('/')[-1].upper()} | Added: {doc['created_at'][:10]}")
        with col_action:
            if st.button("Delete", key=f"del_{doc['id']}"):
                delete_user_document(doc['id'], user_id)
                st.rerun()
        st.markdown("---")
