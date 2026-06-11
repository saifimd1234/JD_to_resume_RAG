"""
Resume Generator: Uses LLM + retrieved context to generate tailored resumes.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

from backend.config import DEFAULT_GENERATION_MODEL, RETRIEVAL_K, DEFAULT_EMBEDDING_MODEL
from backend.retriever import retrieve_relevant_chunks, retrieve_with_scores
from backend.prompts import STYLE_INSTRUCTIONS, GENERATOR_SYSTEM_PROMPT, USER_PROMPT

# ─── Helper Functions ───────────────────────────────────────────────────────

def _build_context(retrieved_docs: list[Document]) -> str:
    """
    Organize retrieved chunks by category for structured context.
    """
    categorized = {}
    for doc in retrieved_docs:
        doc_type = doc.metadata.get("doc_type", "other")
        if doc_type not in categorized:
            categorized[doc_type] = []
        categorized[doc_type].append(doc.page_content)

    context_parts = []
    # Order: personal → skills → experience → projects → certifications → other
    priority_order = ["personal", "skills", "experience", "projects", "certifications"]

    for category in priority_order:
        if category in categorized:
            context_parts.append(f"### {category.upper()}")
            context_parts.append("\n".join(categorized[category]))
            del categorized[category]

    # Remaining categories
    for category, contents in categorized.items():
        context_parts.append(f"### {category.upper()}")
        context_parts.append("\n".join(contents))

    return "\n\n".join(context_parts)


def _build_contact_info(contact_details: dict) -> str:
    """
    Build a clean contact info string for the LLM.
    Only include fields that have actual data.
    """
    if not contact_details:
        return "No contact information provided. Use background data if available."

    parts = []
    # Key-Value pairs that the LLM can easily parse
    mapping = {
        "Full Name": "name",
        "Email": "email",
        "Phone": "phone",
        "Location": "location",
        "LinkedIn URL": "linkedin",
        "GitHub URL": "github"
    }

    for label, key in mapping.items():
        val = contact_details.get(key, "").strip()
        if val:
            parts.append(f"{label}: {val}")

    if not parts:
        return "No contact information provided."

    return "\n".join(parts)


def _get_llm(model_name: str = DEFAULT_GENERATION_MODEL) -> ChatOpenAI:
    """Get LLM instance for the specified model."""
    return ChatOpenAI(
        model=model_name,
        temperature=0.3,
    )


# ─── Main Generation Function ──────────────────────────────────────────────

def generate_resume(
    user_id: int,
    jd_text: str,
    generation_model: str = DEFAULT_GENERATION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    style: str = "corporate",
    custom_prompt: str = "",
    retrieval_k: int = RETRIEVAL_K,
    contact_details: dict = None,
    doc_type: str = "resume",
    attachments: list = None,
) -> dict:
    """
    Generate a tailored resume from a JD using RAG.

    Args:
        user_id: The ID of the current user
        jd_text: The job description text
        generation_model: OpenAI model name for generation
        embedding_model: OpenAI model name for embeddings
        style: Resume style (minimal, corporate, modern)
        custom_prompt: Optional additional instructions
        retrieval_k: Number of chunks to retrieve
        contact_details: Dict with name, email, phone, location, linkedin, github
        doc_type: "resume" or "cv"
        attachments: List of attachments

    Returns:
        dict with keys: resume_text, retrieved_chunks, metadata
    """
    import json
    # 1. Retrieve relevant chunks from KB
    scored_results = retrieve_with_scores(
        user_id,
        jd_text,
        k=retrieval_k,
        embedding_model=embedding_model,
    )

    retrieved_docs = [doc for doc, _ in scored_results]
    scores = [score for _, score in scored_results]

    # 2. Build structured context
    context = _build_context(retrieved_docs)

    # 3. Build contact info
    contact_info = _build_contact_info(contact_details or {})

    # 4. Get style instructions
    style_instructions = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["corporate"])

    # 5. Construct messages
    from backend.prompts import GENERATOR_SYSTEM_PROMPT
    from backend.database import get_section_prompts
    
    attachments_list = [d.get("title") for d in attachments] if attachments else []
    
    json_input_dict = {
        "user_data": {
            "contact_info": contact_info,
            "background": context
        },
        "job_description": jd_text,
        "template_structure": style_instructions,
        "document_type": doc_type,
        "attachments": attachments_list
    }

    # Add safety clause to custom prompt to protect EXPERIENCE/PROJECTS from skill injection contamination
    safe_custom_prompt = custom_prompt
    if custom_prompt and "INJECT THE FOLLOWING SKILLS" in custom_prompt:
        safe_custom_prompt += (
            "\n\nCRITICAL SAFETY RULE: You are asked to inject skills. You must ONLY add these injected skills "
            "to the SKILLS and/or PROFILE sections. DO NOT modify the bullet points, descriptions, technologies, "
            "or details of the EXPERIENCE or PROJECTS sections to add these skills, unless they are already "
            "present in the candidate's background data for those sections. Maintain historical accuracy for "
            "all projects and experiences."
        )

    custom_section = ""
    if safe_custom_prompt.strip():
        custom_section = f"\n\n## ADDITIONAL INSTRUCTIONS:\n{safe_custom_prompt}"

    user_message = USER_PROMPT.format(
        json_input=json.dumps(json_input_dict, indent=2),
        custom_prompt=custom_section,
    )

    # Fetch customized section prompts
    sp = get_section_prompts(user_id)
    section_instructions = f"""
-----------------------------------
📌 SECTION-SPECIFIC INSTRUCTIONS (CRITICAL)
-----------------------------------
For each section of the document, you MUST follow these specific customization rules:

- PROFILE / SUMMARY:
{sp.get('profile', '')}

- EDUCATION:
{sp.get('education', '')}

- SKILLS:
{sp.get('skills', '')}

- CERTIFICATIONS:
{sp.get('certifications', '')}

- EXPERIENCE:
{sp.get('experience', '')}

- PROJECTS:
{sp.get('projects', '')}

- ACHIEVEMENTS:
{sp.get('achievements', '')}
"""

    system_prompt_content = GENERATOR_SYSTEM_PROMPT + "\n" + section_instructions
    if doc_type != "cv":
        import re
        system_prompt_content = re.sub(r"-{30,}\n📌 ATTACHMENTS HANDLING.*?(?=-{30,}\n📌)", "", system_prompt_content, flags=re.DOTALL)

    messages = [
        SystemMessage(content=system_prompt_content),
        HumanMessage(content=user_message),
    ]

    # 6. Generate resume
    llm = _get_llm(generation_model)
    response = llm.invoke(messages)

    # 7. Build response
    chunk_details = []
    for i, (doc, score) in enumerate(scored_results):
        chunk_details.append({
            "rank": i + 1,
            "doc_type": doc.metadata.get("doc_type", "unknown"),
            "score": round(score, 4),
            "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "full_content": doc.page_content,
        })

    return {
        "resume_text": response.content,
        "retrieved_chunks": chunk_details,
        "metadata": {
            "generation_model": generation_model,
            "embedding_model": embedding_model,
            "style": style,
            "chunks_retrieved": len(retrieved_docs),
            "retrieval_k": retrieval_k,
        },
    }

def generate_job_description(
    job_role: str,
    generation_model: str = DEFAULT_GENERATION_MODEL
) -> str:
    """
    Generate a relevant job description based on a target job role.
    """
    llm = _get_llm(generation_model)
    system_prompt = (
        "You are an expert technical recruiter and hiring manager. "
        "Your task is to write a comprehensive, ATS-friendly Job Description for the given job role. "
        "Include a brief summary, key responsibilities, required skills (both technical and soft skills), "
        "and qualifications. Format the output in clean Markdown. "
        "ALWAYS display the FULL job description. NEVER truncate the output or use placeholders like 'character limit reached'."
    )
    user_prompt = f"Generate a detailed Job Description for the role: {job_role}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    response = llm.invoke(messages)
    return response.content

def parse_resume_to_kb(
    resume_text: str,
    existing_kb: list,
    generation_model: str = DEFAULT_GENERATION_MODEL
) -> list[dict]:
    """
    Parse a resume text into structured Knowledge Base entries, avoiding duplicates with existing KB.
    Returns a list of dicts: [{"category": "...", "title": "...", "content": "..."}]
    """
    import json
    llm = _get_llm(generation_model)
    
    existing_kb_text = ""
    if existing_kb:
        existing_kb_text = "EXISTING KNOWLEDGE BASE ENTRIES (DO NOT DUPLICATE THESE):\n"
        for entry in existing_kb:
            existing_kb_text += f"- Category: {entry['category']} | Title: {entry['title']}\n"
    
    system_prompt = (
        "You are an AI assistant that extracts structured information from a resume. "
        "Extract the individual experiences, projects, skills, education, and certifications. "
        "For each item, provide a 'category' (must be one of: 'projects', 'experience', 'skills', 'education', 'certifications', 'personal'), "
        "a 'title' (e.g., the job title, project name, or skill group), and 'content' (the detailed description in markdown format). "
        "IMPORTANT: You MUST NOT extract items that are already in the existing knowledge base. "
        "If a project or experience is clearly a duplicate of an existing entry, ignore it or consolidate new details. "
        "Return the result ONLY as a valid JSON array of objects, with keys 'category', 'title', and 'content'. "
        "Do not include markdown code blocks around the JSON."
    )
    
    user_prompt = f"{existing_kb_text}\n\nRESUME TEXT:\n{resume_text}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # Clean up possible markdown wrappers
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return []

def refine_resume(
    current_resume_text: str,
    refinement_prompt: str,
    jd_text: str = None,
    generation_model: str = DEFAULT_GENERATION_MODEL
) -> str:
    """
    Refine the current resume using AI based on user refinement instructions.
    """
    llm = _get_llm(generation_model)
    
    system_prompt = (
        "You are an expert resume writer. "
        "Your task is to refine and update the candidate's current resume based on their specific refinement request. "
        "You must preserve the original formatting, headings, structure, and style of the resume. "
        "Apply only the requested changes, edits, or additions. Keep unchanged sections exactly as they are. "
        "Return the updated resume in clean Markdown format."
    )
    
    user_prompt = f"""
CURRENT RESUME:
```markdown
{current_resume_text}
```

REFINEMENT REQUEST:
{refinement_prompt}
"""
    if jd_text:
        user_prompt += f"\n\nTARGET JOB DESCRIPTION (for reference/tailoring):\n{jd_text}"
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    response = llm.invoke(messages)
    return response.content

