# 🚀 ResumeForge AI — JD-to-Resume Generator using RAG

An AI-powered system that generates highly tailored, ATS-optimized resumes from Job Descriptions using Retrieval-Augmented Generation (RAG).

## 🏗️ Architecture

```
Job Description → Embedding → Vector Search (ChromaDB) → Relevant KB Chunks → LLM → Tailored Resume
```

**Tech Stack:**
- **RAG Pipeline**: LangChain + ChromaDB + OpenAI Embeddings
- **LLM**: OpenAI (gpt-4.1-nano / mini / full)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Export**: python-docx (DOCX) + fpdf2 (PDF)

## 📂 Project Structure

```
jd_to_resume_RAG/
├── knowledge_base/          # Your personal data (edit these!)
│   ├── skills/skills.md
│   ├── projects/projects.md
│   ├── experience/experience.md
│   ├── certifications/certifications.md
│   └── personal/personal.md
├── backend/                 # RAG pipeline + API
│   ├── config.py            # Centralized configuration
│   ├── ingest.py            # KB → chunks → embeddings
│   ├── retriever.py         # Vector similarity search
│   ├── generator.py         # LLM resume generation
│   ├── api.py               # FastAPI endpoints
│   ├── gap_analyzer.py      # JD gap analysis (Phase 2)
│   └── ats_scorer.py        # ATS scoring (Phase 2)
├── frontend/                # Streamlit UI
│   ├── app.py               # Home page
│   ├── pages/
│   │   ├── 1_Generate_Resume.py
│   │   └── 2_Evaluator.py
│   └── utils/
│       ├── export.py        # DOCX/PDF export
│       └── styles.py        # Custom CSS
├── vector_db/               # ChromaDB storage (auto-generated)
├── requirements.txt
└── .env                     # Your API keys
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key
Edit `.env` and paste your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Edit Knowledge Base
Update the markdown files in `knowledge_base/` with your real data.

### 4. Run the App
```bash
streamlit run frontend/app.py
```

### 5. Generate Your Resume
1. Click **"Run Ingestion"** on the Generate Resume page to index your KB
2. Paste a Job Description
3. Select your preferred model and style
4. Click **Generate Resume**
5. Download as DOCX, PDF, or Markdown

## ⚙️ Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Generation Model | gpt-4.1-nano | OpenAI model for resume generation |
| Embedding Model | text-embedding-3-large | Model for vector embeddings |
| Chunk Size | 500 | Characters per chunk |
| Chunk Overlap | 200 | Overlap between chunks |
| Top-K | 10 | Number of chunks retrieved |

## 🎨 Resume Styles

- **Minimal** — Clean, whitespace-heavy layout
- **Corporate** — Traditional business format
- **Modern** — Contemporary with visual hierarchy

## 📊 Features

### Phase 1 (MVP) ✅
- [x] Knowledge Base ingestion (Markdown → ChromaDB)
- [x] RAG-based resume generation
- [x] Multiple OpenAI model selection
- [x] Multiple embedding model selection
- [x] 3 resume style templates
- [x] DOCX, PDF, Markdown export
- [x] Editable resume output
- [x] Retrieved chunks viewer
- [x] RAG Evaluator page

### Phase 2 (Coming Soon)
- [ ] JD Gap Analyzer
- [ ] ATS Match Score
- [ ] Resume upload & smart merge
- [ ] Custom template upload

### Phase 3
- [ ] Multi-version resume generator
- [ ] Bullet point rewriter
- [ ] Past JD memory
- [ ] Experience prioritization

## 📝 License

MIT
