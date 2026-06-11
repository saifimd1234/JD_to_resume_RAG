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
    st.markdown("""
        <div style='text-align:center; margin-top:48px; margin-bottom:8px;'>
            <div style='display:inline-flex; align-items:center; justify-content:center;
                        width:52px; height:52px; border-radius:14px; background:#EEF0FE;
                        color:#4F46E5; font-weight:800; font-size:1.4rem; margin-bottom:14px;'>R</div>
            <h1 style='margin:0; font-size:1.8rem; font-weight:800; letter-spacing:-0.03em; color:#1A2033;'>
                Welcome to ResumeForge</h1>
            <p style='color:#555D72; font-size:0.98rem; margin-top:6px;'>
                Tailored, ATS-ready resumes from any job description — powered by your own experience.</p>
        </div>
    """, unsafe_allow_html=True)

    # Auth card styling (forms inside the card stay flat)
    st.markdown("""
        <style>
        .auth-container {
            background: #FFFFFF;
            border: 1px solid #E6E8EF;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(16, 24, 40, 0.07);
        }
        div[data-testid="stForm"] {
            border: none;
            background: transparent;
            padding: 0;
            box-shadow: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 1.3, 1])
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
    st.markdown("# ResumeForge")
    role = st.session_state.user['role']
    role_class = "rf-pill-accent" if role == "admin" else ""
    st.markdown(
        f"<div style='margin:4px 0 12px 0;'>"
        f"<div style='font-weight:600; font-size:0.9rem; color:#1A2033;'>{st.session_state.user['email']}</div>"
        f"<span class='rf-pill {role_class}' style='margin-top:6px;'>{role.capitalize()}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

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
first_name = (st.session_state.user.get("full_name") or st.session_state.user["email"].split("@")[0]).split(" ")[0]
st.markdown(f"""
<div class='rf-page-header'>
    <p class='rf-page-title'>Good to see you, {first_name}</p>
    <p class='rf-page-sub'>Here's everything you need to land your next role.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Feature cards
f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    st.markdown("""
    <div class='rf-feature'>
    <div class='rf-feature-icon'>JD</div>
    <div class='rf-feature-title'>Paste Your JD</div>
    <div class='rf-feature-desc'>Paste any job description and get a perfectly tailored resume in seconds.</div>
    </div>""", unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class='rf-feature'>
    <div class='rf-feature-icon'>ATS</div>
    <div class='rf-feature-title'>ATS-Optimized</div>
    <div class='rf-feature-desc'>Keyword-aligned resumes that pass ATS filters with gap analysis and scoring.</div>
    </div>""", unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class='rf-feature'>
    <div class='rf-feature-icon'>KB</div>
    <div class='rf-feature-title'>Your Knowledge Base</div>
    <div class='rf-feature-desc'>Secure, private vector database just for your data.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Quick Start
st.markdown("## Quick start")
st.markdown("""
1. **Manage your Knowledge Base** — Add your skills, experience, and projects in the Manage KB page.
2. **Run Ingestion** — Click "Rebuild Vector DB" to index your data.
3. **Paste a JD** — Go to Generate Resume and paste a job description.
4. **Generate & Analyze** — Get your tailored resume + gap analysis + ATS score.
""")
# End of app.py
