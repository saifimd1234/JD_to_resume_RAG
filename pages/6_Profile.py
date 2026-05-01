import sys
from pathlib import Path
import streamlit as st

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import update_user_profile
from utils.styles import get_custom_css

st.set_page_config(
    page_title="My Profile | ResumeForge AI",
    page_icon="👤",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user = st.session_state.user
user_id = user['id']

# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# My Profile")
st.markdown("Update your default personal details for resumes and CVs.")
st.markdown("---")

with st.form("profile_form"):
    st.markdown("### Contact Information")
    
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name", value=user.get("full_name") or "", placeholder="Mohammad Saifi")
        email = st.text_input("Email", value=user.get("email") or "", disabled=True, help="Email cannot be changed.")
        phone = st.text_input("Phone Number", value=user.get("phone") or "", placeholder="+91 7209538634")
    
    with col2:
        location = st.text_input("Location", value=user.get("location") or "", placeholder="Jamshedpur, JH")
        linkedin = st.text_input("LinkedIn URL", value=user.get("linkedin") or "", placeholder="linkedin.com/in/yourprofile")
        github = st.text_input("GitHub URL", value=user.get("github") or "", placeholder="github.com/yourusername")
        
    submit = st.form_submit_button("Update Profile")
    
    if submit:
        profile_data = {
            "full_name": full_name,
            "phone": phone,
            "location": location,
            "linkedin": linkedin,
            "github": github
        }
        update_user_profile(user_id, profile_data)
        
        # Update session state
        st.session_state.user.update(profile_data)
        st.success("Profile updated successfully!")
        st.rerun()

st.info("These details will be used as the default values in the 'Contact Information' section of the Generate Resume page.")
