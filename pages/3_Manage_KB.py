import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from backend.database import get_kb_entries, add_kb_entry, delete_kb_entry
from utils.styles import get_custom_css

st.set_page_config(
    page_title="Manage KB | ResumeForge AI",
    page_icon="📚",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user_id = st.session_state.user['id']

# ─── Main Content ──────────────────────────────────────────────────────────
st.markdown("# Manage Knowledge Base")
st.markdown("Add and manage your skills, experience, and projects. This data forms your private Vector DB.")
st.markdown("---")

CATEGORIES = ["projects", "experience", "skills", "education", "certifications", "personal"]

# Initialize session state for editing/adding
if "kb_action" not in st.session_state:
    st.session_state.kb_action = None  # None, 'add'

st.markdown("### 🤖 Auto-Fill from Resume (AI Assisted)")
st.markdown("Upload your resume to automatically extract and populate your Knowledge Base.")

with st.expander("Auto-Fill Options", expanded=False):
    af_resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"], key="af_pdf")
    af_resume_text = st.text_area("Or paste resume text", height=150, key="af_txt")
    
    if st.button("Parse Resume", type="primary"):
        if not af_resume_file and not af_resume_text.strip():
            st.error("Please upload a PDF or paste your resume text.")
        else:
            resume_content = ""
            if af_resume_file:
                try:
                    import pypdf
                    pdf_reader = pypdf.PdfReader(af_resume_file)
                    for page in pdf_reader.pages:
                        resume_content += page.extract_text() + "\n"
                except ImportError:
                    st.error("PDF parsing library not installed. Please paste text instead.")
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
            
            if af_resume_text.strip():
                resume_content += "\n" + af_resume_text
                
            if resume_content.strip():
                with st.spinner("Analyzing and extracting entries..."):
                    from backend.generator import parse_resume_to_kb
                    from backend.config import DEFAULT_GENERATION_MODEL
                    existing_entries = get_kb_entries(user_id)
                    parsed_data = parse_resume_to_kb(resume_content, existing_entries, DEFAULT_GENERATION_MODEL)
                    
                    if parsed_data:
                        st.session_state.pending_kb_entries = parsed_data
                        st.success(f"Extracted {len(parsed_data)} new entries!")
                    else:
                        st.warning("No new unique entries extracted.")

if "pending_kb_entries" in st.session_state and st.session_state.pending_kb_entries:
    st.markdown("#### Review Extracted Entries")
    
    with st.form("save_parsed_kb"):
        st.info("Review, edit, or uncheck the entries you don't want to save.")
        
        selected_indices = []
        for i, entry in enumerate(st.session_state.pending_kb_entries):
            st.markdown(f"**{entry.get('category', 'unknown').capitalize()}**: {entry.get('title', 'Untitled')}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.checkbox("Include", value=True, key=f"inc_{i}"):
                    selected_indices.append(i)
            with col2:
                st.session_state.pending_kb_entries[i]['content'] = st.text_area(
                    "Content", 
                    value=entry.get('content', ''), 
                    height=100, 
                    key=f"cnt_{i}"
                )
            st.markdown("---")
            
        if st.form_submit_button("Save Selected to KB", type="primary"):
            from backend.database import add_kb_entry
            
            saved_count = 0
            for i in selected_indices:
                ent = st.session_state.pending_kb_entries[i]
                add_kb_entry(user_id, ent.get("category", "personal"), ent.get("title", "Untitled"), ent.get("content", ""), "")
                saved_count += 1
            
            # Sync Admin KB to Root
            if st.session_state.user['role'] == 'admin':
                from backend.database import sync_admin_kb_to_disk
                try:
                    sync_admin_kb_to_disk(user_id)
                    st.toast("Admin KB synchronized to root directory.")
                except Exception as e:
                    st.error(f"Failed to sync Admin KB: {e}")
            
            st.session_state.pending_kb_entries = []
            if saved_count > 0:
                st.success(f"{saved_count} entries saved!")
            st.rerun()
            
    if st.button("Cancel & Clear"):
        st.session_state.pending_kb_entries = []
        st.rerun()

st.markdown("---")
st.markdown("### Manual Entry")

# Category selection MUST be outside the form to be reactive
category = st.selectbox("Category", CATEGORIES)

with st.form("add_kb_entry", clear_on_submit=True):
    if category == "projects":
        title = st.text_input("Project Name *")
        tech_stack = st.text_input("Tech Stack (comma separated)")
        github_url = st.text_input("GitHub URL")
        description = st.text_area("Description *", height=150, placeholder="Describe your project...")
    elif category == "education":
        title = st.text_input("Degree/Program *", placeholder="B.Tech in Computer Science")
        univ = st.text_input("College/University *")
        start_date = st.text_input("Start Date", placeholder="Aug 2018")
        end_date = st.text_input("End Date", placeholder="May 2022")
        location = st.text_input("Location")
        description = ""
        github_url = ""
    elif category == "experience":
        title = st.text_input("Job Title *")
        company = st.text_input("Company Name *")
        location = st.text_input("Location")
        start_date = st.text_input("Start Date", placeholder="Jan 2023")
        end_date = st.text_input("End Date", placeholder="Present")
        description = st.text_area("Responsibilities *", height=150, placeholder="What did you do?")
        github_url = ""
    elif category == "skills":
        title = st.text_input("Skill Group (e.g., Programming Languages, Frameworks) *")
        description = st.text_area("Skills (comma separated) *", height=100)
        github_url = ""
    else:
        title = st.text_input("Title *")
        github_url = st.text_input("URL (Optional)")
        description = st.text_area("Content *", height=150)
        
    submit = st.form_submit_button("Save Entry", use_container_width=True)
    
    if submit:
        if not title.strip() or (category not in ["education"] and not description.strip()):
            st.error("Please fill in all required fields marked with *.")
        else:
            # Build content string based on category
            content = ""
            if category == "projects":
                if tech_stack:
                    content += f"**Tech Stack:** {tech_stack}\n\n"
                content += description
            elif category == "education":
                content += f"**Institution:** {univ}\n"
                if location:
                    content += f"**Location:** {location}\n"
                if start_date or end_date:
                    content += f"**Duration:** {start_date} - {end_date}\n"
            elif category == "experience":
                content += f"**Job Title:** {title}\n"
                content += f"**Company:** {company}\n"
                if location:
                    content += f"**Location:** {location}\n"
                if start_date or end_date:
                    content += f"**Duration:** {start_date} - {end_date}\n\n"
                content += f"**Responsibilities:**\n{description}"
            else:
                content = description
                
            add_kb_entry(user_id, category, title, content, github_url)
            
            # Sync Admin KB to Root
            if st.session_state.user['role'] == 'admin':
                from backend.database import sync_admin_kb_to_disk
                try:
                    sync_admin_kb_to_disk(user_id)
                    st.toast("Admin KB synchronized to root directory.")
                except Exception as e:
                    st.error(f"Failed to sync Admin KB: {e}")
                    
            st.success(f"Added '{title}' to {category}!")
            st.rerun()

st.markdown("---")
st.markdown("### Your Knowledge Base")

entries = get_kb_entries(user_id)
if not entries:
    st.info("Your knowledge base is empty. Add some entries to get started!")
else:
    # Group by category
    grouped = {cat: [] for cat in CATEGORIES}
    for entry in entries:
        if entry["category"] in grouped:
            grouped[entry["category"]].append(entry)
        else:
            grouped[entry["category"]] = [entry]

    for cat in CATEGORIES:
        cat_entries = grouped.get(cat, [])
        if cat_entries:
            with st.expander(f"{cat.upper()} ({len(cat_entries)})", expanded=(cat == "projects")):
                for entry in cat_entries:
                    st.markdown(f"#### {entry['title']}")
                    if entry['github_url']:
                        st.markdown(f"**🔗 [View Project]({entry['github_url']})**")
                    st.markdown(entry['content'])
                    
                    if st.button("Delete", key=f"del_{entry['id']}", type="secondary"):
                        delete_kb_entry(entry['id'], user_id)
                        # Sync Admin KB to Root
                        if st.session_state.user['role'] == 'admin':
                            from backend.database import sync_admin_kb_to_disk
                            try:
                                # We need to remove the specific file or just rewrite all. 
                                # Since rewrite all doesn't delete, we should ideally clear the directory first.
                                # For now, rewrite all.
                                import os
                                from backend.config import KNOWLEDGE_BASE_DIR
                                import re
                                # Delete the specific file
                                safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', entry['title'])
                                filename = f"{safe_title}.md"
                                filepath = KNOWLEDGE_BASE_DIR / entry['category'] / filename
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                            except Exception as e:
                                st.error(f"Failed to delete from root KB: {e}")
                        st.rerun()
                    st.markdown("---")

st.markdown("---")
st.info("💡 **Tip**: After updating your Knowledge Base, go to **Generate Resume** and click **Rebuild Vector DB** to apply the changes.")
