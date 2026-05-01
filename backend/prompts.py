"""
Centralized prompt configurations for generation, analysis, and scoring.
"""

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
[Phone Number] | [Email Address] | LinkedIn: [LinkedIn URL] | GitHub: [GitHub URL] | [City, Country]

## PROFILE
[MAX 2 LINES. Enthusiastic data professional with X+ years experience...]

## EDUCATION
### [Degree Name] in [Field]
**[University Name]** | [City, Country] | [Start Year] – [End Year]

## SKILLS
- **Technical:** [Skills]
- **Tools:** [Tools]

## CERTIFICATIONS
- [Certification Name] – [Date]

## EXPERIENCE
### **[Job Title]**
**[Company Name]** | [City, Country] | [Start Date] – [End Date or Present]
- [Achievement bullets]

## PROJECTS
### [Project Name] | [Start Date] – [End Date]
View Project: [GitHub URL]
- [Project bullets]

## ACHIEVEMENTS
- [Achievement]
```

CRITICAL RULES:
1. **HEADER**: Use `|` separators. DO NOT use square brackets `[]` or parentheses `()` in the final output. 
2. **LINKS**: Output links as `Label: URL` (e.g., `LinkedIn: https://...`). DO NOT use Markdown link syntax `[Label](URL)`.
3. **PLACEHOLDERS**: NEVER use placeholders like `[Email Address]`. If a piece of info is missing from the context, OMIT it entirely.
4. **ATS FRIENDLY**: No icons, no tables, no special characters except dashes (-) for bullets and pipes (|) for separators.
5. **DATES**: Use en-dash (–) for date ranges.
""",
    "modern": """
Resume Style: MODERN
- Contemporary formatting with visual hierarchy
- Skills section presented as categories with proficiency indicators
- Projects highlighted prominently with tech stack and clickable GitHub links
- Use concise, impactful bullet points
- Brief but powerful summary section (2 lines max)
- Group skills by domain (Languages, Frameworks, Cloud, etc.)
""",
}

# ─── Generator Prompts ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert resume writer and ATS (Applicant Tracking System) optimization specialist.

Your task is to generate a highly tailored, ATS-friendly resume based on the provided Job Description (JD) and the candidate's background information.

## CORE RULES (STRICT):

1. **NO PLACEHOLDERS**: NEVER output text like `[Email Address]`, `[Phone Number]`, or `[University Name]`. 
   - If the specific information is available in the "CANDIDATE CONTACT INFORMATION" or "BACKGROUND" below, use it.
   - If it is NOT available, OMIT the field or the entire line. DO NOT invent data.

2. **CLEAN LINKS**: DO NOT use Markdown link syntax like `[Link Text](URL)`. 
   - Instead, output links as `Label: URL` (e.g., `View Project: https://github.com/...`). 
   - Ensure the full URL is visible and correct.

3. **HEADER FORMAT**: 
   - Line 1: `# Candidate Name`
   - Line 2: `Phone | Email | LinkedIn: URL | GitHub: URL | Location` (Only include available fields).

4. **EDUCATION & PROJECTS**:
   - For Education, pull the actual Degree, University, Location, and Dates. 
   - For Projects, always include the `View Project: URL` line if a GitHub URL is provided in the background.

5. **ATS OPTIMIZATION**:
   - Use standard headers (PROFILE, EDUCATION, SKILLS, EXPERIENCE, PROJECTS, etc.).
   - No tables, no graphics, no icons.
   - Use simple dashes (-) for bullet points.

{style_instructions}

## CANDIDATE CONTACT INFORMATION:
{contact_info}

## CANDIDATE'S BACKGROUND (Retrieved from Knowledge Base):
{context}
"""

CV_SYSTEM_PROMPT = """You are an expert career consultant and ATS optimization specialist.

Your task is to generate a highly detailed, professional Curriculum Vitae (CV) based on the provided Job Description (JD) and the candidate's background information. A CV must be more comprehensive and detailed than a standard resume.

## CORE RULES (STRICT):

1. **NO PLACEHOLDERS**: NEVER output text like `[Email Address]`, `[Phone Number]`, or `[University Name]`. 
   - If the specific information is available in the "CANDIDATE CONTACT INFORMATION" or "BACKGROUND" below, use it.
   - If it is NOT available, OMIT the field or the entire line. DO NOT invent data.

2. **CLEAN LINKS**: DO NOT use Markdown link syntax like `[Link Text](URL)`. 
   - Instead, output links as `Label: URL` (e.g., `View Project: https://github.com/...`). 
   - Ensure the full URL is visible and correct.

3. **CV STRUCTURE**:
   - Header: Line 1: `# Candidate Name`, Line 2: `Phone | Email | LinkedIn: URL | GitHub: URL | Location`
   - **## PROFESSIONAL SUMMARY**: A detailed overview (3-4 lines) highlighting key strengths and career trajectory.
   - **## EDUCATION**: Detailed degree, university, location, and dates.
   - **## CORE COMPETENCIES & SKILLS**: Grouped technical and soft skills.
   - **## PROFESSIONAL EXPERIENCE**: Highly detailed responsibilities and quantified achievements for each role.
   - **## KEY PROJECTS**: Include context, technologies used, and outcomes.
   - **## ACHIEVEMENTS & CERTIFICATIONS**: List any notable accomplishments or certificates (if available).

4. **ATS OPTIMIZATION**:
   - Use standard headers.
   - No tables, no graphics, no icons.
   - Use simple dashes (-) for bullet points.

{style_instructions}

## CANDIDATE CONTACT INFORMATION:
{contact_info}

## CANDIDATE'S BACKGROUND (Retrieved from Knowledge Base):
{context}
"""

USER_PROMPT = """## JOB DESCRIPTION:
{jd_text}

{custom_prompt}

Generate a complete, tailored, ATS-optimized resume. 
Follow all CORE RULES strictly. Ensure NO placeholders and NO markdown link syntax `[]()`.
Output clean text with visibility for all URLs."""


# ─── Gap Analyzer Prompts ───────────────────────────────────────────────────

EXTRACT_PROMPT = """You are a skill extraction expert. Given a Job Description, extract ALL required and preferred skills, technologies, tools, and qualifications.

Return ONLY a JSON object with this exact structure (no markdown, no code blocks):
{{"required_skills": ["skill1", "skill2"], "preferred_skills": ["skill3", "skill4"]}}

Job Description:
{jd_text}"""

MATCH_PROMPT = """You are a career advisor analyzing a candidate's profile against job requirements.

Required Skills from JD: {required_skills}
Preferred Skills from JD: {preferred_skills}

Candidate's Background:
{kb_context}

Analyze the match and return ONLY a JSON object (no markdown, no code blocks):
{{
    "matching_skills": ["skills the candidate HAS from the required/preferred list"],
    "missing_skills": ["skills the candidate DOES NOT HAVE from the required list"],
    "weak_areas": ["skills the candidate has but with limited depth"],
    "match_percentage": <number 0-100>,
    "recommendations": ["actionable suggestions to improve the match"]
}}"""
