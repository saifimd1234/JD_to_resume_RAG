"""
Custom Streamlit CSS styles for ResumeForge AI.
"""


def get_custom_css() -> str:
    """Return custom CSS for the Streamlit app."""
    return """
    <style>
    /* ─── Import Google Font ──────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ─── Global ──────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%);
    }

    /* ─── Sidebar ─────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    section[data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, #00d4ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 1.5rem;
        letter-spacing: -0.5px;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
    }

    /* ─── Main Content Headers ────────────────────────────── */
    .main .stMarkdown h1 {
        background: linear-gradient(135deg, #00d4ff, #7b2ff7, #ff6b9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        letter-spacing: -1px;
        margin-bottom: 0.3rem;
    }

    .main .stMarkdown h2 {
        color: #e0e0ff;
        font-weight: 700;
        font-size: 1.3rem;
        border-bottom: 2px solid rgba(123, 47, 247, 0.3);
        padding-bottom: 8px;
        margin-top: 1.5rem;
    }

    .main .stMarkdown h3 {
        color: #b0b0d0;
        font-weight: 600;
        font-size: 1.1rem;
    }

    .main .stMarkdown p {
        color: rgba(255, 255, 255, 0.8);
    }

    /* ─── Cards / Containers ──────────────────────────────── */
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }

    div[data-testid="stExpander"] summary {
        color: #b0b0d0;
        font-weight: 600;
    }

    /* ─── Text Area ───────────────────────────────────────── */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(123, 47, 247, 0.2) !important;
        border-radius: 10px !important;
        color: #e0e0ff !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .stTextArea textarea:focus {
        border-color: rgba(123, 47, 247, 0.5) !important;
        box-shadow: 0 0 20px rgba(123, 47, 247, 0.15) !important;
    }

    /* ─── Select Box ──────────────────────────────────────── */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(123, 47, 247, 0.2) !important;
        border-radius: 10px !important;
        color: #e0e0ff !important;
    }

    /* ─── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.3px;
        transition: all 0.3s ease;
        border: none;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7b2ff7 0%, #00d4ff 100%);
        color: white;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        box-shadow: 0 4px 20px rgba(123, 47, 247, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 30px rgba(123, 47, 247, 0.5);
        transform: translateY(-1px);
    }

    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.06);
        color: #b0b0d0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #e0e0ff;
    }

    /* ─── Download Button ─────────────────────────────────── */
    .stDownloadButton > button {
        background: rgba(0, 212, 255, 0.1) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        color: #00d4ff !important;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stDownloadButton > button:hover {
        background: rgba(0, 212, 255, 0.2) !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
    }

    /* ─── Metrics ─────────────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px;
    }

    div[data-testid="stMetric"] label {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.85rem;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: 700;
    }

    /* ─── Tabs ────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.5);
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(123, 47, 247, 0.2), rgba(0, 212, 255, 0.2));
        color: #e0e0ff !important;
    }

    /* ─── Spinner ─────────────────────────────────────────── */
    .stSpinner > div {
        border-color: #7b2ff7 transparent transparent transparent !important;
    }

    /* ─── Success / Info / Warning ─────────────────────────── */
    .stSuccess {
        background: rgba(0, 200, 83, 0.08) !important;
        border: 1px solid rgba(0, 200, 83, 0.2) !important;
        border-radius: 10px;
    }

    .stInfo {
        background: rgba(0, 212, 255, 0.08) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 10px;
    }

    .stWarning {
        background: rgba(255, 171, 0, 0.08) !important;
        border: 1px solid rgba(255, 171, 0, 0.2) !important;
        border-radius: 10px;
    }

    /* ─── Divider ─────────────────────────────────────────── */
    hr {
        border-color: rgba(123, 47, 247, 0.15) !important;
    }

    /* ─── File Uploader ───────────────────────────────────── */
    .stFileUploader > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 2px dashed rgba(123, 47, 247, 0.2) !important;
        border-radius: 12px !important;
    }

    /* ─── Toast ───────────────────────────────────────────── */
    div[data-testid="stToast"] {
        background: rgba(26, 26, 46, 0.95) !important;
        border: 1px solid rgba(123, 47, 247, 0.3) !important;
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }

    /* ─── Scrollbar ───────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(123, 47, 247, 0.3);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(123, 47, 247, 0.5);
    }

    /* ─── Custom Status Badge ─────────────────────────────── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .status-ready {
        background: rgba(0, 200, 83, 0.1);
        color: #00c853;
        border: 1px solid rgba(0, 200, 83, 0.2);
    }

    .status-empty {
        background: rgba(255, 171, 0, 0.1);
        color: #ffab00;
        border: 1px solid rgba(255, 171, 0, 0.2);
    }
    </style>
    """


def get_resume_preview_css() -> str:
    """CSS for the resume preview panel (light background for readability)."""
    return """
    <style>
    .resume-preview {
        background: #ffffff;
        color: #1a1a2e;
        padding: 30px 40px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-family: 'Inter', 'Calibri', sans-serif;
        font-size: 0.92rem;
        line-height: 1.6;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .resume-preview h1 {
        color: #1a1a2e;
        font-size: 1.6rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 4px;
    }

    .resume-preview h2 {
        color: #2c3e6b;
        font-size: 1.05rem;
        font-weight: 700;
        text-transform: uppercase;
        border-bottom: 2px solid #2c3e6b;
        padding-bottom: 4px;
        margin-top: 16px;
        margin-bottom: 8px;
    }

    .resume-preview h3 {
        color: #34495e;
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .resume-preview ul {
        margin: 4px 0;
        padding-left: 20px;
    }

    .resume-preview li {
        margin-bottom: 3px;
        color: #333;
    }

    .resume-preview p {
        color: #333;
        margin: 4px 0;
    }
    </style>
    """
