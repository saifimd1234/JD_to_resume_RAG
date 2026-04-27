"""
Resume Generator: Uses LLM + retrieved context to generate tailored resumes.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

from backend.config import DEFAULT_GENERATION_MODEL, RETRIEVAL_K, DEFAULT_EMBEDDING_MODEL
from backend.retriever import retrieve_relevant_chunks, retrieve_with_scores
from backend.prompts import STYLE_INSTRUCTIONS, SYSTEM_PROMPT, USER_PROMPT

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

    Returns:
        dict with keys: resume_text, retrieved_chunks, metadata
    """
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
    system_message = SYSTEM_PROMPT.format(
        context=context,
        style_instructions=style_instructions,
        contact_info=contact_info,
    )

    custom_section = ""
    if custom_prompt.strip():
        custom_section = f"\n\n## ADDITIONAL INSTRUCTIONS:\n{custom_prompt}"

    user_message = USER_PROMPT.format(
        jd_text=jd_text,
        custom_prompt=custom_section,
    )

    messages = [
        SystemMessage(content=system_message),
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
