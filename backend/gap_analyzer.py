"""
Gap Analyzer: Compare JD requirements against KB to identify skill gaps.
Uses LLM to extract skills from JD and match against KB content.
"""

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.config import DEFAULT_GENERATION_MODEL, DEFAULT_EMBEDDING_MODEL
from backend.retriever import retrieve_relevant_chunks


class GapAnalysis(BaseModel):
    """Result of JD vs KB gap analysis."""
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)
    match_percentage: float = Field(default=0.0)
    recommendations: list[str] = Field(default_factory=list)


from backend.prompts import EXTRACT_PROMPT, MATCH_PROMPT


def analyze_gaps(
    user_id: int,
    jd_text: str,
    generation_model: str = DEFAULT_GENERATION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> GapAnalysis:
    """
    Compare JD requirements against KB content.
    1. Extract skills from JD using LLM
    2. Retrieve relevant KB chunks
    3. Match and identify gaps using LLM
    """
    import json

    llm = ChatOpenAI(model=generation_model, temperature=0)

    # Step 1: Extract skills from JD
    extract_response = llm.invoke([
        HumanMessage(content=EXTRACT_PROMPT.format(jd_text=jd_text))
    ])

    try:
        # Clean response — strip markdown code blocks if present
        raw = extract_response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        skills_data = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        skills_data = {"required_skills": [], "preferred_skills": []}

    required = skills_data.get("required_skills", [])
    preferred = skills_data.get("preferred_skills", [])

    # Step 2: Retrieve KB context
    chunks = retrieve_relevant_chunks(user_id, jd_text, k=15, embedding_model=embedding_model)
    kb_context = "\n\n".join(doc.page_content for doc in chunks)

    # Step 3: Match skills
    match_response = llm.invoke([
        HumanMessage(content=MATCH_PROMPT.format(
            required_skills=", ".join(required),
            preferred_skills=", ".join(preferred),
            kb_context=kb_context,
        ))
    ])

    try:
        raw = match_response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        match_data = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        match_data = {
            "matching_skills": [],
            "missing_skills": required,
            "weak_areas": [],
            "match_percentage": 0.0,
            "recommendations": ["Could not analyze. Try a different model."],
        }

    return GapAnalysis(
        matching_skills=match_data.get("matching_skills", []),
        missing_skills=match_data.get("missing_skills", []),
        weak_areas=match_data.get("weak_areas", []),
        match_percentage=match_data.get("match_percentage", 0.0),
        recommendations=match_data.get("recommendations", []),
    )
