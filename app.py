"""
ResumeForge AI — Main Streamlit Application
AI-Powered JD-to-Resume Generator using RAG
"""

import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from utils.styles import get_custom_css
from backend.ingest import get_kb_metadata, check_kb_changes


# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResumeForge AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth State ──────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Auth UI ───────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>ResumeForge AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>AI-Powered JD-to-Resume Generator</p>", unsafe_allow_html=True)
    
    # Add custom CSS for Auth UI
    st.markdown("""
        <style>
        .auth-container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
        }
        div[data-testid="stForm"] {
            border: none;
            background: transparent;
            padding: 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Forgot Password"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Log In", use_container_width=True)
                
                if submit:
                    from backend.database import authenticate_user
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user = user
                        
                        if user["role"] == "admin":
                            from backend.database import sync_disk_to_admin_kb
                            sync_disk_to_admin_kb(user["id"])
                            
                            from backend.retriever import get_chunk_count_for_user
                            if get_chunk_count_for_user(user["id"]) == 0:
                                from backend.ingest import run_ingestion
                                run_ingestion(user["id"])
                                
                        st.success(f"Welcome back, {email}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                        
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input("Password", type="password")
                new_submit = st.form_submit_button("Sign Up", use_container_width=True)
                
                if new_submit:
                    if len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        from backend.database import create_user
                        if create_user(new_email, new_password):
                            st.success("Account created successfully! Please log in.")
                        else:
                            st.error("Email already exists.")
                            
        with tab3:
            st.markdown("### Reset Password")
            # State management for reset flow
            if "reset_token_sent" not in st.session_state:
                st.session_state.reset_token_sent = False
                
            if not st.session_state.reset_token_sent:
                with st.form("forgot_password_form"):
                    reset_email = st.text_input("Enter your registered email")
                    reset_submit = st.form_submit_button("Send Reset Link", use_container_width=True)
                    
                    if reset_submit:
                        from backend.database import create_reset_token
                        token = create_reset_token(reset_email)
                        if token:
                            # Simulate email send
                            st.success("Reset link sent! (Simulated below)")
                            st.info(f"Your reset token is: **{token}**")
                            st.session_state.reset_token_sent = True
                        else:
                            st.error("Email not found.")
            else:
                with st.form("reset_password_form"):
                    token_input = st.text_input("Enter Reset Token")
                    new_pass = st.text_input("Enter New Password", type="password")
                    confirm_submit = st.form_submit_button("Reset Password", use_container_width=True)
                    
                    if confirm_submit:
                        from backend.database import verify_reset_token, reset_password
                        user_id = verify_reset_token(token_input)
                        if user_id:
                            if len(new_pass) < 6:
                                st.error("Password must be at least 6 characters.")
                            else:
                                reset_password(user_id, new_pass)
                                st.success("Password reset successfully! Please log in.")
                                st.session_state.reset_token_sent = False
                        else:
                            st.error("Invalid or expired token.")
                            
                if st.button("Cancel", use_container_width=True):
                    st.session_state.reset_token_sent = False
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
                            
    st.stop()

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ResumeForge AI")
    st.markdown(f"**User**: `{st.session_state.user['email']}`")
    st.markdown(f"**Role**: `{st.session_state.user['role'].upper()}`")
    
    if st.button("Log Out"):
        st.session_state.user = None
        st.rerun()
        
    st.markdown("---")

    st.markdown("### System Status")
    try:
        from backend.retriever import get_chunk_count_for_user, get_all_categories_for_user
        user_id = st.session_state.user['id']
        chunk_count = get_chunk_count_for_user(user_id)
        categories = get_all_categories_for_user(user_id)
        kb_meta = get_kb_metadata(user_id)
        kb_changes = check_kb_changes(user_id)

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
    except Exception as e:
        st.markdown(
            f'<span class="status-badge status-empty">System Error</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("""
    - **Generate Resume** — JD → Resume
    - **Manage KB** — Update your knowledge
    """)

# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# ResumeForge AI Dashboard")
st.markdown("### Welcome back!")
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
    <div style='font-size:1.8rem; margin-bottom:8px;'>[DB]</div>
    <div style='font-weight:700; color:#e0e0ff; margin-bottom:6px;'>Your Knowledge Base</div>
    <div style='color:#888; font-size:0.85rem;'>Secure, private vector database just for your data.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Quick Start
st.markdown("## Quick Start")
st.markdown("""
1. **Manage your Knowledge Base** — Add your skills, experience, and projects in the Manage KB page.
2. **Run Ingestion** — Click "Rebuild Vector DB" to index your data.
3. **Paste a JD** — Go to Generate Resume and paste a job description.
4. **Generate & Analyze** — Get your tailored resume + gap analysis + ATS score.
""")
# End of app.py
