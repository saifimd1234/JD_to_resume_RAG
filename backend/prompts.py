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

GENERATOR_SYSTEM_PROMPT = """You are an expert CV/Resume writer.

Your task is to generate a professional document STRICTLY based on:
1. User data (profile, experience, etc.)
2. Job Description (if provided)
3. Selected Template Structure (VERY IMPORTANT)

-----------------------------------
📌 TEMPLATE CONTROL (CRITICAL)
-----------------------------------
You will be given a "template_structure" extracted from a .docx file.

You MUST:
- Follow the EXACT section order
- Follow the EXACT headings
- Follow formatting style (paragraph/bullets)
- Do NOT add/remove sections
- Do NOT rename headings

If template is:
- "CV sample corporate" → follow formal CV style
- "resume sample corporate" → concise resume style
- "Sam CV sample" → follow its exact structure

-----------------------------------
📌 INPUT FORMAT
-----------------------------------
You will receive a JSON structure containing:
{
  "user_data": {...},
  "job_description": "...",
  "template_structure": "...",
  "document_type": "cv | resume",
  "attachments": [...]
}

-----------------------------------
📌 CONTENT GENERATION RULES
-----------------------------------

1. PROFILE / SUMMARY
- Tailor to job description
- 3–5 lines
- Strong and role-specific

2. EXPERIENCE
- Follow template formatting strictly
- Responsibilities:
    - Real day-to-day tasks
    - No generic lines
    - 4–6 bullet points
- Achievements:
    - Include numbers, %, impact

3. SKILLS
- Match template categories
- Prioritize job-relevant skills

4. OTHER SECTIONS
- Fill exactly as per template
- Do not invent missing data

-----------------------------------
📌 TEMPLATE FIDELITY RULE (VERY IMPORTANT)
-----------------------------------
The template_structure is the highest priority.

Even if your internal knowledge suggests better formatting:
→ IGNORE it
→ FOLLOW template strictly

-----------------------------------
📌 ATTACHMENTS HANDLING
-----------------------------------
- After main document ends:
    - Add each attachment on a NEW PAGE
    - Maintain upload order

Format:

--- PAGE BREAK ---
Attachment 1: <File Name>
<Content>

-----------------------------------
📌 OUTPUT RULES
-----------------------------------
- Clean formatting
- No placeholders like "N/A" unless necessary
- No grammar mistakes
- Professional tone

-----------------------------------
📌 FINAL INSTRUCTION
-----------------------------------
Generate the document strictly following the provided template_structure.
"""

USER_PROMPT = """Here is the input data:

```json
{json_input}
```

{custom_prompt}

Generate the document strictly following the provided template_structure and output format rules. Output clean Markdown text."""


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


# ─── Default Section-Specific Prompts ────────────────────────────────────────

DEFAULT_SECTION_PROMPTS = {
    "profile": "Write a tailored, impact-focused professional summary matching the job description using 3-5 lines. Introduce the candidate's core expertise and career achievements.",
    "education": "List all degrees, majors, university names, locations, and graduation dates exactly as they appear in the candidate's background database. Do not invent details.",
    "skills": "Group all candidate skills logically (e.g., Programming Languages, Frameworks, Developer Tools) and present them in bullet points. If skills are injected, place them here naturally.",
    "experience": "Detail the candidate's professional experiences. For each role, provide the job title, company name, location, dates, and 4-6 bullet points detailing day-to-day responsibilities and quantitative achievements. CRITICAL: Do not invent details, metrics, technologies, or responsibilities that are not in the candidate's background database.",
    "projects": "List the candidate's projects. For each, include the project name, dates, clickable link (if any), and 2-4 bullets describing the implementation details. CRITICAL: Do not invent details, features, or technologies that are not in the candidate's background database.",
    "certifications": "List all certifications exactly as they appear in the candidate's background. Do not invent new certifications.",
    "achievements": "List candidate achievements, awards, or publications exactly as they appear in the background."
}
