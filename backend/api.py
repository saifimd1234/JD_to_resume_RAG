"""
FastAPI endpoints for the JD-to-Resume RAG system.
Includes Phase 2: Gap Analysis + ATS Scoring.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import (
    DEFAULT_GENERATION_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RETRIEVAL_K,
    MAX_JD_CHARACTERS,
)
from backend.ingest import run_ingestion, check_kb_changes, get_kb_metadata
from backend.generator import generate_resume
from backend.retriever import get_chunk_count, get_all_categories
from backend.gap_analyzer import analyze_gaps
from backend.ats_scorer import calculate_ats_score

app = FastAPI(
    title="ResumeForge AI API",
    description="RAG-based resume generation with gap analysis and ATS scoring",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Models ─────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    jd_text: str = Field(..., max_length=MAX_JD_CHARACTERS)
    generation_model: str = DEFAULT_GENERATION_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    style: str = "corporate"
    custom_prompt: str = ""
    retrieval_k: int = RETRIEVAL_K
    contact_details: dict = Field(default_factory=dict)


class IngestRequest(BaseModel):
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    embedding_model: str = DEFAULT_EMBEDDING_MODEL


class GapRequest(BaseModel):
    jd_text: str = Field(..., max_length=MAX_JD_CHARACTERS)
    generation_model: str = DEFAULT_GENERATION_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL


class ATSRequest(BaseModel):
    resume_text: str
    jd_text: str = Field(..., max_length=MAX_JD_CHARACTERS)
    generation_model: str = DEFAULT_GENERATION_MODEL


# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """System health and vector DB status."""
    chunk_count = get_chunk_count()
    categories = get_all_categories()
    kb_meta = get_kb_metadata()
    kb_changes = check_kb_changes()
    return {
        "status": "healthy",
        "vector_db_ready": chunk_count > 0,
        "chunk_count": chunk_count,
        "categories": categories,
        "last_ingestion": kb_meta.get("last_ingestion"),
        "kb_has_changes": kb_changes["has_changes"],
    }


@app.post("/api/generate-resume")
def api_generate_resume(request: GenerateRequest):
    """Generate a tailored resume from a Job Description."""
    if not request.jd_text.strip():
        raise HTTPException(400, "JD text cannot be empty")
    if get_chunk_count() == 0:
        raise HTTPException(400, "Vector DB is empty. Run ingestion first.")

    try:
        return generate_resume(
            jd_text=request.jd_text,
            generation_model=request.generation_model,
            embedding_model=request.embedding_model,
            style=request.style,
            custom_prompt=request.custom_prompt,
            retrieval_k=request.retrieval_k,
            contact_details=request.contact_details,
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/ingest")
def api_ingest(request: IngestRequest):
    """Re-ingest the knowledge base."""
    try:
        return run_ingestion(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            embedding_model=request.embedding_model,
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/kb-status")
def kb_status():
    """Check knowledge base file changes."""
    return check_kb_changes()


@app.post("/api/gap-analysis")
def api_gap_analysis(request: GapRequest):
    """Analyze skill gaps between JD and KB."""
    if not request.jd_text.strip():
        raise HTTPException(400, "JD text cannot be empty")
    if get_chunk_count() == 0:
        raise HTTPException(400, "Vector DB is empty. Run ingestion first.")

    try:
        result = analyze_gaps(
            jd_text=request.jd_text,
            generation_model=request.generation_model,
            embedding_model=request.embedding_model,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/ats-score")
def api_ats_score(request: ATSRequest):
    """Calculate ATS match score for a resume against a JD."""
    if not request.resume_text.strip() or not request.jd_text.strip():
        raise HTTPException(400, "Both resume and JD text are required")

    try:
        result = calculate_ats_score(
            resume_text=request.resume_text,
            jd_text=request.jd_text,
            generation_model=request.generation_model,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
