"""
Resume Generator: Uses LLM + retrieved context to generate tailored resumes.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

from backend.config import DEFAULT_GENERATION_MODEL, RETRIEVAL_K, DEFAULT_EMBEDDING_MODEL
from backend.retriever import retrieve_relevant_chunks, retrieve_with_scores


# ─── Resume Style Templates ────────────────────────────────────────────────

STYLE_INSTRUCTIONS = {
    "minimal": """
Resume Style: MINIMAL
- Clean, whitespace-heavy layout
- No decorative elements or icons
- Section headers in bold, simple horizontal rules
- Focus on content clarity and readability
- Use simple bullet points (-)
- Keep formatting sparse and readable
""",
    "corporate": """
Resume Style: CORPORATE / ATS-OPTIMIZED

You MUST follow this EXACT resume structure and format:

```
# [Full Name]
[City, Country] | [Email Address] | [Phone Number] | [LinkedIn Profile] | [GitHub Profile]

## PROFILE
[MAX 2 LINES. Enthusiastic data professional with X+ years experience... Google certified...]

## EDUCATION
### [University Name] — [City, Country]
**[Degree Name]** | [Start Year] - [End Year]
- [Notable achievements, top X%, relevant coursework]

## SKILLS
- **Technical:** [Comma-separated list of technical skills relevant to JD]
- **Tools:** [Comma-separated list of tools, platforms, cloud services]

## CERTIFICATIONS
- [Certification Name] - [Date] ([link if available])

## EXPERIENCE
### [Company Name] — [City, Country]
**[Job Title]** | [Start Date] - [End Date or Present]
- [Action verb] + [what you did] + [impact/result with numbers]
- [Max 5-7 bullet points per role]

## PROJECTS
### [Project Name] | [Start Date] - [End Date]
- [What and how you solved]
- [Tools/methods/frameworks used]
- [Result/Impact with numbers]
- [Max 3 points per project]

## ACHIEVEMENTS
- [Achievement] - [Organization/Context]
- [Max 3 points]
```

CRITICAL RULES:
- Header: Name as # Header, then contact line exactly as shown with | separators.
- PROFILE: MUST BE MAX 2 LINES.
- Use `##` for section headers (PROFILE, EDUCATION, SKILLS, CERTIFICATIONS, EXPERIENCE, PROJECTS, ACHIEVEMENTS).
- Use `###` for sub-items (University, Company, Project).
- Use `**bold**` for job titles, degrees, and dates.
- Use `-` for ALL bullet points.
- NO horizontal rules, NO special characters like bullets (•). Use simple dash (-).
""",
    "modern": """
Resume Style: MODERN
- Contemporary formatting with visual hierarchy
- Skills section presented as categories with proficiency indicators
- Projects highlighted prominently with tech stack
- Use concise, impactful bullet points
- Brief but powerful summary section (2 lines max)
- Group skills by domain (Languages, Frameworks, Cloud, etc.)
""",
}


# ─── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert resume writer and ATS (Applicant Tracking System) optimization specialist.

Your task is to generate a highly tailored, ATS-friendly resume based on the provided Job Description (JD) and the candidate's background information retrieved from their knowledge base.

## CANDIDATE CONTACT INFORMATION (USE EXACTLY AS PROVIDED):
{contact_info}

## CORE RULES:

1. **Header**: The resume MUST start with the candidate's full name as `# Name`, followed by their contact details on the next line separated by ` | `. Use EXACTLY the contact info provided above.

2. **ATS Optimization**:
   - Mirror exact keywords and phrases from the JD naturally
   - Use standard section headings (PROFILE, EDUCATION, SKILLS, CERTIFICATIONS, EXPERIENCE, PROJECTS, ACHIEVEMENTS)
   - Avoid tables, graphics, or special characters
   - Use consistent formatting throughout
   - NO emojis, NO icons, NO special unicode characters

3. **Bullet Points**:
   - Start every bullet with a strong action verb (Developed, Implemented, Optimized, Designed, Led, Built, Automated, etc.)
   - Include quantified achievements (numbers, percentages, scale)
   - Follow the pattern: [Action Verb] + [What you did] + [Impact/Result with numbers]
   - Rewrite raw experience into JD-specific, impactful bullets

4. **Prioritization**:
   - Reorder skills, experience, and projects based on JD relevance
   - If JD emphasizes Data Engineering → lead with Spark/Kafka/Pipeline work
   - If JD emphasizes Data Science → lead with ML/Analytics/Modeling work
   - If JD emphasizes Analysis → lead with SQL/Excel/Dashboard work
   - Suppress irrelevant details to keep resume concise (1-2 pages)

5. **Formatting**:
   - Use Markdown formatting ONLY
   - `#` for candidate name ONLY
   - `##` for section headers (PROFILE, SKILLS, EXPERIENCE, etc.)
   - `###` for subsections (company names, project names, university)
   - `-` for bullet points
   - `**bold**` for job titles, degrees, and date ranges
   - NO tables, NO horizontal rules, NO code blocks

6. **Content Integrity**:
   - Use ONLY the candidate's actual background — NEVER fabricate experience, skills, or achievements
   - You may rephrase and strengthen existing content, but not invent new content

{style_instructions}

## CANDIDATE'S BACKGROUND (Retrieved from Knowledge Base):
{context}
"""


USER_PROMPT = """## JOB DESCRIPTION:
{jd_text}

{custom_prompt}

Generate a complete, tailored, ATS-optimized resume for this job description.
Use ONLY the candidate's actual background information provided above — do NOT fabricate any experience, skills, or achievements.
Use the candidate's EXACT contact information from the system prompt header.
Output the resume in clean Markdown format."""


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
    Build the contact info string from user-provided details.
    """
    name = contact_details.get("name", "").strip()
    email = contact_details.get("email", "").strip()
    phone = contact_details.get("phone", "").strip()
    location = contact_details.get("location", "").strip()
    linkedin = contact_details.get("linkedin", "").strip()
    github = contact_details.get("github", "").strip()

    parts = []
    if name:
        parts.append(f"Full Name: {name}")
    if email:
        parts.append(f"Email: {email}")
    if phone:
        parts.append(f"Phone: {phone}")
    if location:
        parts.append(f"Location: {location}")
    if linkedin:
        parts.append(f"LinkedIn: {linkedin}")
    if github:
        parts.append(f"GitHub: {github}")

    if not parts:
        return "No contact information provided. Use details from the knowledge base."

    return "\n".join(parts)


def _get_llm(model_name: str = DEFAULT_GENERATION_MODEL) -> ChatOpenAI:
    """Get LLM instance for the specified model."""
    return ChatOpenAI(
        model=model_name,
        temperature=0.3,
    )


# ─── Main Generation Function ──────────────────────────────────────────────

def generate_resume(
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
