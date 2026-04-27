import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.styles import get_custom_css
from backend.database import get_total_users, get_total_resumes_generated, get_all_users

st.set_page_config(
    page_title="Admin Dashboard | ResumeForge AI",
    page_icon="👑",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

if st.session_state.user['role'] != 'admin':
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# 👑 Admin Dashboard")
st.markdown("System-wide metrics and user management.")
st.markdown("---")

# Metrics
total_users = get_total_users()
total_resumes = get_total_resumes_generated()

st.markdown("""
<style>
/* Make metric cards smaller and cleaner */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}
div[data-testid="stMetricValue"] {
    font-size: 24px !important;
}
</style>
""", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Total Users", total_users)
m2.metric("Total Resumes Generated", total_resumes)
m3.metric("Active Sessions", "N/A (Stateless)")

st.markdown("---")
st.markdown("### Users Overview")

users = get_all_users()
if users:
    df = pd.DataFrame(users)
    # Format the dataframe for display
    display_df = df.copy()
    display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    display_df.rename(columns={
        'id': 'User ID',
        'email': 'Email',
        'role': 'Role',
        'last_job_role': 'Latest Job Role',
        'resumes_generated': 'Total Resumes',
        'created_at': 'Joined Date'
    }, inplace=True)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### User Activity & Resume History")
    
    selected_user_email = st.selectbox("Select User to View History", [u['email'] for u in users])
    selected_user = next(u for u in users if u['email'] == selected_user_email)
    
    from backend.database import get_user_resumes
    user_resumes = get_user_resumes(selected_user['id'])
    
    if user_resumes:
        st.write(f"Showing **{len(user_resumes)}** resumes for **{selected_user_email}**")
        
        for resume in user_resumes:
            with st.expander(f"📄 {resume['job_role']} — {resume['created_at'][:16]}"):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.caption(f"**Generated:** {resume['created_at']}")
                    st.markdown("**Job Description Snippet:**")
                    st.caption(resume['job_description'][:200] + "...")
                
                with col_actions:
                    # View Button
                    if st.button("View Content", key=f"view_{resume['id']}"):
                        st.session_state.view_resume = resume['resume_content']
                    
                    # Download DOCX
                    from utils.export import export_to_docx
                    try:
                        docx_bytes = export_to_docx(resume['resume_content'])
                        st.download_button(
                            "Download .docx", 
                            docx_bytes, 
                            file_name=f"resume_{selected_user['id']}_{resume['id']}.docx",
                            key=f"dl_{resume['id']}"
                        )
                    except Exception as e:
                        st.error("DOCX Error")

        if "view_resume" in st.session_state:
            st.markdown("---")
            st.markdown("#### Resume Content Preview")
            st.text_area("Content", st.session_state.view_resume, height=400)
            if st.button("Close Preview"):
                del st.session_state.view_resume
                st.rerun()
    else:
        st.info("This user has not generated any resumes yet.")

else:
    st.info("No users found.")
