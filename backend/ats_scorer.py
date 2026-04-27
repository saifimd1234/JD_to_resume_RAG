"""
ATS Scorer: Score a generated resume against the JD for ATS compatibility.
Uses keyword matching + LLM evaluation for comprehensive scoring.
"""

import re
from collections import Counter
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.config import DEFAULT_GENERATION_MODEL


class ATSScore(BaseModel):
    """ATS scoring breakdown."""
    overall_score: float = Field(default=0.0, description="Overall ATS match (0-100)")
    skills_match: float = Field(default=0.0, description="Skills keyword match %")
    keyword_density: float = Field(default=0.0, description="JD keyword density in resume %")
    formatting_score: float = Field(default=0.0, description="ATS-friendly formatting score")
    experience_relevance: float = Field(default=0.0, description="Experience relevance score")
    suggestions: list[str] = Field(default_factory=list)


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text (lowercase, deduplicated)."""
    # Common stop words to exclude
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "need", "must",
        "we", "you", "they", "he", "she", "it", "i", "me", "my", "your",
        "our", "their", "this", "that", "these", "those", "as", "if", "not",
        "no", "so", "up", "out", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "same", "than",
        "too", "very", "just", "also", "more", "most", "other", "some",
        "such", "only", "own", "all", "each", "every", "both", "few",
        "many", "much", "any", "who", "whom", "which", "what", "where",
        "when", "how", "why", "able", "work", "working", "experience",
        "including", "using", "etc", "role", "team", "strong", "good",
    }

    words = re.findall(r'\b[a-zA-Z][a-zA-Z+#.]{1,}\b', text.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def _check_formatting(resume_text: str) -> tuple[float, list[str]]:
    """Check resume for ATS-friendly formatting. Returns score and issues."""
    score = 100.0
    issues = []

    # Check for special characters that ATS can't parse
    special_chars = ['•', '►', '◆', '★', '→', '⇒', '●', '○']
    for char in special_chars:
        if char in resume_text:
            score -= 5
            issues.append(f"Contains special character '{char}' — use simple dashes instead")

    # Check for proper section headers
    expected_sections = ["profile", "skills", "experience", "education", "projects"]
    resume_lower = resume_text.lower()
    for section in expected_sections:
        if section not in resume_lower:
            score -= 5
            issues.append(f"Missing standard section: {section.upper()}")

    # Check for quantified achievements
    numbers = re.findall(r'\d+[%+]?', resume_text)
    if len(numbers) < 3:
        score -= 10
        issues.append("Few quantified achievements — add more numbers and percentages")

    # Check for action verbs at bullet start
    bullets = [line.strip() for line in resume_text.split('\n') if line.strip().startswith('- ')]
    weak_starts = 0
    for bullet in bullets:
        content = bullet[2:].strip()
        if content and content[0].islower():
            weak_starts += 1
    if weak_starts > 2:
        score -= 5
        issues.append(f"{weak_starts} bullets don't start with strong action verbs")

    return max(0.0, min(100.0, score)), issues


def calculate_ats_score(
    resume_text: str,
    jd_text: str,
    generation_model: str = DEFAULT_GENERATION_MODEL,
) -> ATSScore:
    """
    Calculate ATS match score between resume and JD.

    Combines:
    1. Keyword matching (exact and fuzzy)
    2. Formatting checks
    3. LLM-based experience relevance scoring
    """
    # 1. Keyword matching
    jd_keywords = _extract_keywords(jd_text)
    resume_keywords = _extract_keywords(resume_text)

    jd_keyword_set = set(jd_keywords)
    resume_keyword_set = set(resume_keywords)

    if jd_keyword_set:
        matched = jd_keyword_set.intersection(resume_keyword_set)
        skills_match = (len(matched) / len(jd_keyword_set)) * 100
    else:
        skills_match = 0.0

    # 2. Keyword density
    jd_freq = Counter(jd_keywords)
    top_jd_keywords = [kw for kw, _ in jd_freq.most_common(20)]
    resume_lower = resume_text.lower()
    found_top = sum(1 for kw in top_jd_keywords if kw in resume_lower)
    keyword_density = (found_top / max(len(top_jd_keywords), 1)) * 100

    # 3. Formatting
    formatting_score, formatting_issues = _check_formatting(resume_text)

    # 4. LLM experience relevance
    try:
        llm = ChatOpenAI(model=generation_model, temperature=0)
        relevance_prompt = f"""Rate how relevant this resume is to the job description on a scale of 0-100.
Consider: role alignment, skill match, experience level, and industry fit.
Return ONLY a number (0-100), nothing else.

JOB DESCRIPTION:
{jd_text[:2000]}

RESUME:
{resume_text[:3000]}"""

        response = llm.invoke([HumanMessage(content=relevance_prompt)])
        experience_relevance = float(re.findall(r'\d+\.?\d*', response.content)[0])
        experience_relevance = min(100.0, max(0.0, experience_relevance))
    except Exception:
        experience_relevance = 50.0

    # 5. Overall score (weighted average)
    overall = (
        skills_match * 0.30
        + keyword_density * 0.25
        + formatting_score * 0.15
        + experience_relevance * 0.30
    )

    # Build suggestions
    suggestions = list(formatting_issues)
    if skills_match < 70:
        missing = jd_keyword_set - resume_keyword_set
        top_missing = list(missing)[:5]
        suggestions.append(f"Missing JD keywords: {', '.join(top_missing)}")
    if keyword_density < 60:
        suggestions.append("Increase keyword density — mirror more JD phrases naturally")
    if experience_relevance < 60:
        suggestions.append("Strengthen experience alignment — highlight JD-relevant responsibilities")

    return ATSScore(
        overall_score=round(overall, 1),
        skills_match=round(skills_match, 1),
        keyword_density=round(keyword_density, 1),
        formatting_score=round(formatting_score, 1),
        experience_relevance=round(experience_relevance, 1),
        suggestions=suggestions,
    )
