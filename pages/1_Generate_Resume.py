"""
Generate Resume Page — Vertically stacked layout
Contact Info → JD Input → Config → Style → Generate → Output
"""

import sys
import os
import base64
from pathlib import Path

# Add root to path (one level up from pages/)
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import markdown

from utils.styles import get_custom_css, get_resume_preview_css
from utils.export import export_to_docx, export_to_pdf
import backend.config as cfg
from backend.retriever import get_chunk_count_for_user
from backend.ingest import run_ingestion, check_kb_changes, get_kb_metadata
from backend.generator import generate_resume
from backend.gap_analyzer import analyze_gaps
from backend.ats_scorer import calculate_ats_score


# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Generate Resume | ResumeForge AI",
    page_icon="📄",
    layout="wide",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)
st.markdown(get_resume_preview_css(), unsafe_allow_html=True)

# ─── Auth Check ─────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in from the main page first.")
    st.stop()

user_id = st.session_state.user['id']
user_profile = st.session_state.user

# Initialize session state for contact info from user profile if not set
if "c_name" not in st.session_state: st.session_state.c_name = user_profile.get("full_name") or ""
if "c_email" not in st.session_state: st.session_state.c_email = user_profile.get("email") or ""
if "c_phone" not in st.session_state: st.session_state.c_phone = user_profile.get("phone") or ""
if "c_loc" not in st.session_state: st.session_state.c_loc = user_profile.get("location") or ""
if "c_li" not in st.session_state: st.session_state.c_li = user_profile.get("linkedin") or ""
if "c_gh" not in st.session_state: st.session_state.c_gh = user_profile.get("github") or ""

# ─── Session State ──────────────────────────────────────────────────────────
for key in ["generated_resume", "retrieved_chunks", "generation_metadata",
            "gap_analysis", "ats_score", "jd_for_analysis"]:
    if key not in st.session_state:
        st.session_state[key] = None

if "is_locked" not in st.session_state:
    st.session_state.is_locked = False

if "jd_input_text" not in st.session_state:
    st.session_state.jd_input_text = ""

is_locked = st.session_state.is_locked
lock_help = "This feature is locked. Please contact admin or upgrade your plan to unlock." if is_locked else None


# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("# Generate Resume")
st.markdown("Paste a Job Description and generate a tailored, ATS-optimized resume.")
if is_locked:
    st.warning("🔒 **Features Locked:** You have already generated a resume. Please contact admin or upgrade your plan to unlock and make further edits.")
st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Knowledge Base & Ingestion
# ═══════════════════════════════════════════════════════════════════════════

user_id = st.session_state.user['id']
chunk_count = get_chunk_count_for_user(user_id)

with st.expander("Knowledge Base & Ingestion", expanded=(chunk_count == 0)):
    # Show KB status
    kb_changes = check_kb_changes(user_id)
    kb_meta = get_kb_metadata(user_id)

    status_col, info_col = st.columns([1, 2])

    with status_col:
        if chunk_count > 0:
            st.success(f"Vector DB Ready — {chunk_count} chunks")
            if kb_meta.get("last_ingestion"):
                st.caption(f"Last indexed: {kb_meta['last_ingestion'][:19]}")
        else:
            st.warning("Vector DB is empty")

    with info_col:
        if kb_changes["has_changes"]:
            change_parts = []
            if kb_changes["new_files"]:
                change_parts.append(f"**{len(kb_changes['new_files'])} new**")
            if kb_changes["modified_files"]:
                change_parts.append(f"**{len(kb_changes['modified_files'])} modified**")
            if kb_changes["deleted_files"]:
                change_parts.append(f"**{len(kb_changes['deleted_files'])} deleted**")
            st.info(f"Knowledge Base changes detected: {', '.join(change_parts)} files. Rebuild recommended.")
        elif chunk_count > 0:
            st.caption(f"{kb_changes['total_files']} files — no changes since last ingestion.")

    # Ingestion controls
    ing_col1, ing_col2, ing_col3 = st.columns(3)
    with ing_col1:
        ing_embedding = st.selectbox("Embedding Model", list(cfg.EMBEDDING_MODELS.keys()), key="ing_emb", disabled=is_locked, help=lock_help)
    with ing_col2:
        ing_chunk_size = st.number_input("Chunk Size", 100, 2000, cfg.CHUNK_SIZE, 50, key="ing_cs", disabled=is_locked, help=lock_help)
    with ing_col3:
        ing_chunk_overlap = st.number_input("Chunk Overlap", 0, 500, cfg.CHUNK_OVERLAP, 50, key="ing_co", disabled=is_locked, help=lock_help)

    if st.button("Rebuild Vector DB", type="primary", key="ingest_btn", disabled=is_locked, help=lock_help):
        with st.spinner("Indexing knowledge base..."):
            try:
                stats = run_ingestion(user_id, ing_chunk_size, ing_chunk_overlap, cfg.EMBEDDING_MODELS[ing_embedding])
                st.success(f"Done! {stats['documents_loaded']} docs → {stats['chunks_created']} chunks → {stats['vectors_stored']} vectors")
                st.rerun()
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Contact Information
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## Contact Information")
st.caption("Appears at the top of your resume header.")

c1, c2, c3 = st.columns(3)
with c1:
    contact_name = st.text_input("Full Name *", value=st.session_state.c_name, placeholder="Mohammad Saifi", key="c_name_input")
with c2:
    contact_email = st.text_input("Email *", value=st.session_state.c_email, placeholder="saifimd1234@gmail.com", key="c_email_input")
with c3:
    contact_phone = st.text_input("Phone", value=st.session_state.c_phone, placeholder="+91 7209538634", key="c_phone_input")

c4, c5, c6 = st.columns(3)
with c4:
    contact_location = st.text_input("Location", value=st.session_state.c_loc, placeholder="Jamshedpur, JH", key="c_loc_input")
with c5:
    contact_linkedin = st.text_input("LinkedIn", value=st.session_state.c_li, placeholder="linkedin.com/in/yourprofile", key="c_li_input")
with c6:
    contact_github = st.text_input("GitHub", value=st.session_state.c_gh, placeholder="github.com/yourusername", key="c_gh_input")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Job Information
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## Job Information")

job_role = st.text_input("Target Job Role *", placeholder="e.g., Senior Data Engineer", key="job_role_input")

if st.button("Auto-Generate Job Description", disabled=not job_role.strip()):
    with st.spinner("Generating relevant job description..."):
        from backend.generator import generate_job_description
        gen_m = st.session_state.get("gen_m", list(cfg.GENERATION_MODELS.keys())[0])
        try:
            st.session_state.jd_input_text = generate_job_description(job_role, cfg.GENERATION_MODELS[gen_m])
            st.rerun()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.info("Tip: If you are seeing an APIConnectionError, please check your internet connection or VPN. If you are in a region where OpenAI is restricted, you may need a proxy.")

jd_text_widget = st.text_area(
    "Paste Job Description *",
    value=st.session_state.jd_input_text,
    height=250,
    placeholder="Paste the full job description including requirements, responsibilities, qualifications...",
    key="jd_input_widget"
)

# Update session state with the actual value from the widget
st.session_state.jd_input_text = jd_text_widget
jd_text = jd_text_widget

char_count = len(jd_text) if jd_text else 0
color = "#16A34A" if char_count < cfg.MAX_JD_CHARACTERS * 0.9 else "#DC2626"
st.markdown(
    f"<div style='text-align:right; color:{color}; font-size:0.8rem; margin-top:-10px;'>"
    f"{char_count:,} / {cfg.MAX_JD_CHARACTERS:,} characters</div>",
    unsafe_allow_html=True,
)

st.markdown("---")


st.markdown("## Document Type & Attachments")

doc_type_option = st.radio("Select Output Format", ["Resume", "CV"], horizontal=True, key="doc_type_radio")
st.session_state.doc_type = doc_type_option.lower()

if st.session_state.doc_type == "cv":
    st.markdown("#### Attachments")
    from backend.database import get_user_documents
    user_docs = get_user_documents(user_id)
    
    if user_docs:
        doc_options = {f"{d['title']} ({d['file_type'].split('/')[-1].upper()})": d for d in user_docs}
        selected_doc_names = st.multiselect("Select documents to attach to your CV (Order is preserved)", list(doc_options.keys()))
        
        if selected_doc_names:
            current_selected_ids = [doc['id'] for doc in st.session_state.get('ordered_attachments', [])]
            new_selected_ids = [doc_options[name]['id'] for name in selected_doc_names]
            
            if set(current_selected_ids) != set(new_selected_ids):
                new_ordered = [doc for doc in st.session_state.get('ordered_attachments', []) if doc['id'] in new_selected_ids]
                for name in selected_doc_names:
                    doc = doc_options[name]
                    if doc['id'] not in current_selected_ids:
                        new_ordered.append(doc)
                st.session_state.ordered_attachments = new_ordered
            elif 'ordered_attachments' not in st.session_state:
                st.session_state.ordered_attachments = [doc_options[name] for name in selected_doc_names]
            
            st.markdown("#### Ordered Attachments")
            st.caption("Use arrows to reorder before generation.")
            for i, doc in enumerate(st.session_state.ordered_attachments):
                col1, col2, col3, col4 = st.columns([0.1, 0.7, 0.1, 0.1])
                col1.write(f"{i+1}.")
                col2.write(f"**{doc['title']}**")
                
                if col3.button("↑", key=f"up_{doc['id']}", disabled=(i == 0)):
                    st.session_state.ordered_attachments[i-1], st.session_state.ordered_attachments[i] = st.session_state.ordered_attachments[i], st.session_state.ordered_attachments[i-1]
                    st.rerun()
                if col4.button("↓", key=f"down_{doc['id']}", disabled=(i == len(st.session_state.ordered_attachments)-1)):
                    st.session_state.ordered_attachments[i+1], st.session_state.ordered_attachments[i] = st.session_state.ordered_attachments[i], st.session_state.ordered_attachments[i+1]
                    st.rerun()
            
            st.session_state.selected_attachments = st.session_state.ordered_attachments
        else:
            st.session_state.selected_attachments = []
            st.session_state.ordered_attachments = []
            st.warning("Some documents are missing. Would you like to upload now?")
    else:
        st.session_state.selected_attachments = []
        st.session_state.ordered_attachments = []
        st.warning("You have no uploaded documents. Would you like to upload one now?")
        
    if not user_docs or not selected_doc_names:
        with st.expander("Upload Document Now"):
            inline_doc_title = st.text_input("Document Title *", key="inline_doc_title")
            inline_uploaded_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "jpeg"], key="inline_doc_upload")
            if st.button("Upload & Refresh"):
                if inline_doc_title and inline_uploaded_file:
                    from backend.database import add_user_document
                    import re, time
                    safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', inline_uploaded_file.name)
                    unique_filename = f"{int(time.time())}_{safe_filename}"
                    file_path = Path(__file__).parent.parent / "data" / "user_docs" / str(user_id) / unique_filename
                    import os
                    os.makedirs(file_path.parent, exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(inline_uploaded_file.getbuffer())
                    add_user_document(user_id, inline_doc_title.strip(), str(file_path), inline_uploaded_file.type)
                    st.success("Uploaded!")
                    st.rerun()

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Configuration
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## Configuration")

cfg1, cfg2, cfg3, cfg4 = st.columns(4)
with cfg1:
    gen_model_label = st.selectbox("Generation Model", list(cfg.GENERATION_MODELS.keys()), key="gen_m", disabled=is_locked, help=lock_help)
with cfg2:
    emb_model_label = st.selectbox("Embedding Model", list(cfg.EMBEDDING_MODELS.keys()), key="emb_m", disabled=is_locked, help=lock_help)
with cfg3:
    retrieval_k = st.slider("Top-K Retrieval", 3, 25, 10, key="top_k", disabled=is_locked, help=lock_help)
with cfg4:
    pass  # Reserved

# Custom prompt
with st.expander("Custom Prompt (Optional)"):
    custom_prompt = st.text_area(
        "Additional instructions",
        height=80,
        placeholder="E.g., 'Focus on leadership' or 'Highlight cloud certifications'...",
        key="custom_prompt",
        disabled=is_locked,
        help=lock_help
    )

# Resume upload
with st.expander("Upload Existing Resume (Optional)"):
    uploaded_resume = st.file_uploader("Upload PDF or paste text below", type=["pdf"], key="resume_up", disabled=is_locked, help=lock_help)
    resume_paste = st.text_area("Or paste resume text", height=100, key="resume_paste", placeholder="Paste your current resume text here...", disabled=is_locked, help=lock_help)
    if uploaded_resume:
        st.info("Resume uploaded — will be used as reference for generation.")

# Centralized section prompts configuration
with st.expander("Customize Section Prompts (Optional)"):
    from backend.database import get_section_prompts, update_section_prompt
    st.markdown("Edit the prompt instructions for each section of your resume to customize how the LLM generates them:")
    
    custom_sp = get_section_prompts(user_id)
    
    for section_key, default_text in custom_sp.items():
        edited_prompt = st.text_area(
            f"{section_key.upper()} Prompt",
            value=default_text,
            height=85,
            key=f"sp_editor_{section_key}",
            disabled=is_locked,
            help=lock_help
        )
        if edited_prompt != default_text:
            update_section_prompt(user_id, section_key, edited_prompt)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Resume Style Selection
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("## Style Selection")

style_cols = st.columns(3, gap="large")

if st.session_state.doc_type == "cv":
    style_options = ["Minimal", "Corporate"]
else:
    style_options = list(cfg.RESUME_TEMPLATES.keys())

# Initialize style in session state
if "selected_style" not in st.session_state or st.session_state.selected_style not in style_options:
    st.session_state.selected_style = "Corporate"

for i, style_name in enumerate(style_options):
    with style_cols[i]:
        is_selected = st.session_state.selected_style == style_name
        card_class = "rf-style-card selected" if is_selected else "rf-style-card"

        st.markdown(
            f"<div class='{card_class}'>"
            f"<div class='rf-style-name'>{style_name}</div>"
            f"<div class='rf-style-desc'>"
            f"{'Clean & simple' if style_name == 'Minimal' else 'Traditional ATS-ready' if style_name == 'Corporate' else 'Contemporary look'}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if st.button(f"Select {style_name}", key=f"style_{style_name}", use_container_width=True, disabled=is_locked, help=lock_help):
            st.session_state.selected_style = style_name
            st.rerun()

# Show PDF preview if available
selected_style = st.session_state.selected_style
preview_file = cfg.TEMPLATE_PREVIEWS.get(selected_style)
if preview_file:
    pdf_path = cfg.PUBLIC_DIR / preview_file
    if pdf_path.exists():
        with st.expander(f"Preview: {selected_style} Template", expanded=False):
            with open(pdf_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{pdf_data}" '
                f'width="100%" height="500px" style="border:1px solid #E6E8EF; border-radius:8px;"></iframe>',
                unsafe_allow_html=True,
            )

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Generate Button
# ═══════════════════════════════════════════════════════════════════════════

generate_disabled = (
    not jd_text or not jd_text.strip()
    or not job_role or not job_role.strip()
    or chunk_count == 0
    or not contact_name or not contact_name.strip()
)

if chunk_count == 0:
    st.caption("Run ingestion first to enable generation.")
if not job_role or not job_role.strip():
    st.caption("Target Job Role is required.")
if not contact_name or not contact_name.strip():
    st.caption("Full Name is required.")

col_gen, col_gap = st.columns(2, gap="large")

with col_gen:
    if st.button(
        "Generate Resume" if st.session_state.doc_type == "resume" else "Generate CV",
        type="primary",
        disabled=generate_disabled,
        use_container_width=True,
        key="generate_btn",
    ):
        contact_details = {
            "name": st.session_state.get("c_name_input"),
            "email": st.session_state.get("c_email_input"),
            "phone": st.session_state.get("c_phone_input"),
            "location": st.session_state.get("c_loc_input"),
            "linkedin": st.session_state.get("c_li_input"),
            "github": st.session_state.get("c_gh_input"),
        }
        st.session_state.generate_trigger = "normal"
        st.rerun()

# ─── Handle Generate Triggers ────────────────────────────────────────────────
if st.session_state.get("generate_trigger"):
    trigger_type = st.session_state.generate_trigger
    st.session_state.generate_trigger = None # reset
    
    contact_details = {
        "name": contact_name, "email": contact_email,
        "phone": contact_phone, "location": contact_location,
        "linkedin": contact_linkedin, "github": contact_github,
    }
    
    final_custom_prompt = custom_prompt if "custom_prompt" in dir() and custom_prompt else ""
    if resume_paste and resume_paste.strip():
        final_custom_prompt += f"\n\nUSER'S EXISTING RESUME (Use as structural reference and style guide):\n{resume_paste}"
        
    missing_skills_injected = []
    if trigger_type == "inject_skills":
        missing_skills_injected = st.session_state.get("missing_skills_to_inject", [])
        if missing_skills_injected:
            final_custom_prompt += f"\n\nCRITICAL: INJECT THE FOLLOWING SKILLS NATURALLY INTO THE RESUME (EVEN IF THEY ARE NOT IN THE KB): {', '.join(missing_skills_injected)}"
            # Save injected skills for display later
            st.session_state.last_injected_skills = missing_skills_injected
    else:
        st.session_state.last_injected_skills = []

    with st.spinner("Generating your tailored resume..."):
        try:
            # Check limits before generation
            from backend.database import check_resume_limit, increment_resume_count
            can_generate, limit_msg = check_resume_limit(user_id)
            if not can_generate:
                st.error(limit_msg)
                st.stop()
                
            result = generate_resume(
                user_id=user_id,
                jd_text=jd_text,
                generation_model=cfg.GENERATION_MODELS[gen_model_label],
                embedding_model=cfg.EMBEDDING_MODELS[emb_model_label],
                style=cfg.RESUME_TEMPLATES.get(selected_style, selected_style),
                custom_prompt=final_custom_prompt,
                retrieval_k=retrieval_k,
                contact_details=contact_details,
                doc_type=st.session_state.doc_type,
                attachments=st.session_state.get("selected_attachments", []) if st.session_state.doc_type == "cv" else []
            )
            
            increment_resume_count(user_id)
            
            # Save generated resume to DB for tracking
            from backend.database import save_generated_resume
            save_generated_resume(user_id, job_role, jd_text, result["resume_text"])
            
            st.session_state.generated_resume = result["resume_text"]
            st.session_state.retrieved_chunks = result["retrieved_chunks"]
            st.session_state.generation_metadata = result["metadata"]
            st.session_state.jd_for_analysis = jd_text
            st.session_state.is_locked = True
            st.rerun()
        except Exception as e:
            st.error(f"Generation failed: {e}")

with col_gap:
    if st.button(
        "Analyze JD Gaps",
        disabled=generate_disabled,
        use_container_width=True,
        key="gap_btn",
    ):
        with st.spinner("Analyzing skill gaps..."):
            try:
                gap = analyze_gaps(user_id, jd_text, cfg.GENERATION_MODELS[gen_model_label], cfg.EMBEDDING_MODELS[emb_model_label])
                st.session_state.gap_analysis = gap
                st.rerun()
            except Exception as e:
                st.error(f"Gap analysis failed: {e}")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: Gap Analysis Results
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.gap_analysis:
    gap = st.session_state.gap_analysis

    st.markdown("## JD Gap Analysis")

    # Score metric
    score_color = "#16A34A" if gap.match_percentage >= 70 else "#B45309" if gap.match_percentage >= 40 else "#DC2626"
    st.markdown(
        f"<div class='rf-score-card'>"
        f"<div class='rf-score-label'>Overall Match</div>"
        f"<div class='rf-score-value' style='color:{score_color};'>{gap.match_percentage:.0f}%</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### Matching Skills")
    if gap.matching_skills:
        pills = "".join(f"<span class='rf-pill rf-pill-green' style='margin:0 6px 8px 0;'>{skill}</span>" for skill in gap.matching_skills)
        st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)
    else:
        st.caption("None found")

    st.markdown("#### Missing Skills")
    if gap.missing_skills:
        pills = "".join(f"<span class='rf-pill rf-pill-red' style='margin:0 6px 8px 0;'>{skill}</span>" for skill in gap.missing_skills)
        st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)
    else:
        st.caption("No gaps!")

    st.markdown("#### Recommendations")
    if gap.recommendations:
        for rec in gap.recommendations:
            st.info(rec)
    else:
        st.caption("No recommendations")
        
    # Extra Generate options after Gap Analysis
    st.markdown("### Generate Options based on Gap Analysis")
    g_btn1, g_btn2 = st.columns(2)
    
    with g_btn1:
        if st.button("Generate (Current KB)", use_container_width=True, type="primary"):
            st.session_state.generate_trigger = "normal"
            st.rerun()
            
    with g_btn2:
        if gap.missing_skills:
            if st.button("Generate (Inject Missing Skills)", use_container_width=True):
                st.session_state.generate_trigger = "inject_skills"
                st.session_state.missing_skills_to_inject = gap.missing_skills
                st.rerun()
        else:
            st.button("Generate (Inject Missing Skills)", use_container_width=True, disabled=True)

    st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: Generated Resume Output
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.generated_resume:
    resume_text = st.session_state.generated_resume

    if st.session_state.doc_type == "cv":
        st.markdown("## Generated CV")
    else:
        st.markdown("## Generated Resume")

    # ─── Flow Options: Continue or Generate New ──────────────────────────────
    st.markdown("### Actions & Refinements")
    
    col_flow_new, col_flow_refine = st.columns(2)
    
    with col_flow_new:
        st.markdown("**Start Over**")
        st.caption("Clears all history, job role, job description, and generated resume to start a completely new generation.")
        if st.button("Generate Completely New Resume", use_container_width=True, type="secondary", key="flow_gen_new"):
            # Clean history and inputs
            for key in ["generated_resume", "retrieved_chunks", "generation_metadata",
                        "gap_analysis", "ats_score", "jd_for_analysis", "last_injected_skills"]:
                st.session_state[key] = None
            st.session_state.is_locked = False
            
            # Reset widgets in session state
            st.session_state.job_role_input = ""
            st.session_state.jd_input_widget = ""
            st.session_state.jd_input_text = ""
            st.session_state.custom_prompt = ""
            st.session_state.resume_paste = ""
            st.session_state.resume_up = None
            if "selected_attachments" in st.session_state:
                st.session_state.selected_attachments = []
            if "ordered_attachments" in st.session_state:
                st.session_state.ordered_attachments = []
                
            st.rerun()
            
    with col_flow_refine:
        st.markdown("**Refine with AI (Continue)**")
        st.caption("Keep current inputs and instruct the AI to make specific adjustments or corrections to the generated resume.")
        
        with st.form("refine_form", clear_on_submit=True):
            refine_prompt = st.text_area(
                "Describe the adjustments you want:",
                placeholder="E.g., 'Make the summary section sound more formal' or 'Add SQL and Python to the skills section'...",
                height=70,
                key="flow_refine_input"
            )
            submit_refine = st.form_submit_button("Apply Refinements", use_container_width=True)
            
            if submit_refine:
                if not refine_prompt.strip():
                    st.error("Please specify what adjustments you want.")
                else:
                    with st.spinner("Applying refinements..."):
                        from backend.generator import refine_resume
                        try:
                            gen_m = st.session_state.get("gen_m", list(cfg.GENERATION_MODELS.keys())[0])
                            model = cfg.GENERATION_MODELS[gen_m]
                            
                            updated_resume = refine_resume(
                                current_resume_text=resume_text,
                                refinement_prompt=refine_prompt,
                                jd_text=st.session_state.jd_for_analysis,
                                generation_model=model
                            )
                            st.session_state.generated_resume = updated_resume
                            st.toast("Resume refined successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Refinement failed: {e}")

    st.markdown("---")

    # Enhanced Generation Feedback
    if st.session_state.get("last_injected_skills"):
        st.markdown("### Enhanced Generation Feedback")
        info_col, rec_col = st.columns(2)
        with info_col:
            st.success("**Newly Added Skills (Injected):**")
            pills = "".join(f"<span class='rf-pill rf-pill-accent' style='margin:0 6px 8px 0;'>{skill}</span>" for skill in st.session_state.last_injected_skills)
            st.markdown(f"<div style='line-height:2.2;'>{pills}</div>", unsafe_allow_html=True)
        with rec_col:
            if st.session_state.gap_analysis and st.session_state.gap_analysis.recommendations:
                st.warning("**What You Should Learn:**")
                for rec in st.session_state.gap_analysis.recommendations:
                    st.markdown(f"- {rec}")

    # Preview / Edit tabs
    preview_tab, edit_tab = st.tabs(["Preview", "Edit"])

    with preview_tab:
        resume_html = markdown.markdown(resume_text, extensions=["extra"])
        st.markdown(
            f'<div class="resume-preview">{resume_html}</div>',
            unsafe_allow_html=True,
        )

    with edit_tab:
        edited_resume = st.text_area(
            "Edit your resume (Markdown)",
            value=resume_text,
            height=500,
            key="resume_editor",
        )
        if edited_resume != resume_text:
            st.session_state.generated_resume = edited_resume
            resume_text = edited_resume

    # Export buttons
    st.markdown("### Export")
    dl1, dl2, dl3, dl4 = st.columns(4)

    with dl1:
        try:
            attachments = st.session_state.get("selected_attachments", []) if st.session_state.doc_type == "cv" else []
            docx_bytes = export_to_docx(resume_text, attachments)
            st.download_button("DOCX", docx_bytes, "document.docx",
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             use_container_width=True, key="dl_docx")
        except Exception as e:
            st.error(f"DOCX error: {e}")

    with dl2:
        try:
            attachments = st.session_state.get("selected_attachments", []) if st.session_state.doc_type == "cv" else []
            pdf_bytes = export_to_pdf(resume_text, attachments)
            st.download_button("PDF", pdf_bytes, "document.pdf",
                             "application/pdf", use_container_width=True, key="dl_pdf")
        except Exception as e:
            st.error(f"PDF error: {e}")

    with dl3:
        st.download_button("Markdown", resume_text, "document.md",
                         "text/markdown", use_container_width=True, key="dl_md")

    with dl4:
        # ATS Score button
        if st.button("ATS Score", use_container_width=True, key="ats_btn"):
            jd_for_score = st.session_state.jd_for_analysis or jd_text
            if jd_for_score:
                with st.spinner("Calculating ATS score..."):
                    try:
                        ats = calculate_ats_score(resume_text, jd_for_score, cfg.GENERATION_MODELS[gen_model_label])
                        st.session_state.ats_score = ats
                        st.rerun()
                    except Exception as e:
                        st.error(f"ATS scoring error: {e}")

    # ATS Score display
    if st.session_state.ats_score:
        ats = st.session_state.ats_score
        st.markdown("---")
        st.markdown("### ATS Match Score")

        ats_color = "#16A34A" if ats.overall_score >= 70 else "#B45309" if ats.overall_score >= 50 else "#DC2626"
        st.markdown(
            f"<div class='rf-score-card'>"
            f"<div class='rf-score-label'>Overall ATS Score</div>"
            f"<div class='rf-score-value' style='color:{ats_color};'>{ats.overall_score:.0f}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Skills Match", f"{ats.skills_match:.0f}%")
        a2.metric("Keyword Density", f"{ats.keyword_density:.0f}%")
        a3.metric("Formatting", f"{ats.formatting_score:.0f}%")
        a4.metric("Experience Fit", f"{ats.experience_relevance:.0f}%")

        if ats.suggestions:
            with st.expander("Improvement Suggestions"):
                for suggestion in ats.suggestions:
                    st.markdown(f"- {suggestion}")
        meta = st.session_state.generation_metadata
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Model", meta.get("generation_model", "N/A"))
        m2.metric("Chunks Used", meta.get("chunks_retrieved", 0))
        m3.metric("Style", meta.get("style", "N/A").capitalize())

    # Retrieved chunks
    if st.session_state.retrieved_chunks:
        with st.expander(f"Retrieved Chunks ({len(st.session_state.retrieved_chunks)})"):
            for chunk in st.session_state.retrieved_chunks:
                pill_class = "rf-pill-green" if chunk["score"] > 0.5 else "rf-pill-amber" if chunk["score"] > 0.3 else "rf-pill-red"
                st.markdown(
                    f"<div class='rf-chunk'>"
                    f"<div class='rf-chunk-head'>"
                    f"<span class='rf-chunk-rank'>#{chunk['rank']}</span>"
                    f"<span class='rf-pill'>{chunk['doc_type']}</span>"
                    f"<span class='rf-pill {pill_class}'>Score: {chunk['score']}</span>"
                    f"</div>"
                    f"<div class='rf-chunk-body'>{chunk['preview']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
