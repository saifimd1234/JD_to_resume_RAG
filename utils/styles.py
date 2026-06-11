"""
ResumeForge AI — Design System
Clean, light, modern SaaS look: soft gray canvas, white cards,
a single indigo accent, Inter typography, subtle borders and shadows.

Design tokens live in CSS custom properties (--rf-*) so every page
stays consistent and future tweaks happen in one place.
"""


def get_custom_css() -> str:
    """Return the global CSS for the app (inject on every page)."""
    return """
    <style>
    /* ─── Font ────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ─── Design Tokens ───────────────────────────────────────── */
    :root {
        --rf-bg: #F7F8FA;
        --rf-surface: #FFFFFF;
        --rf-border: #E6E8EF;
        --rf-border-strong: #D8DBE5;
        --rf-text: #1A2033;
        --rf-text-2: #555D72;
        --rf-text-3: #8B93A7;
        --rf-accent: #4F46E5;
        --rf-accent-hover: #4338CA;
        --rf-accent-soft: #EEF0FE;
        --rf-accent-border: #C9CDF8;
        --rf-green: #16A34A;
        --rf-green-soft: #EBF7EF;
        --rf-amber: #B45309;
        --rf-amber-soft: #FdF4E7;
        --rf-red: #DC2626;
        --rf-red-soft: #FDEEEE;
        --rf-radius: 12px;
        --rf-radius-sm: 8px;
        --rf-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
        --rf-shadow-md: 0 4px 12px rgba(16, 24, 40, 0.07);
    }

    html, body, [class*="css"], .stApp, button, input, textarea, select {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
    }

    .stApp {
        background: var(--rf-bg);
    }

    /* Soften the top chrome so it blends with the canvas */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Comfortable reading width with breathing room */
    .main .block-container {
        max-width: 1180px !important;
        padding-top: 2.2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 4rem !important;
    }

    /* ─── Typography ──────────────────────────────────────────── */
    .main .stMarkdown h1 {
        color: var(--rf-text);
        font-weight: 800;
        font-size: 1.9rem;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }

    .main .stMarkdown h2 {
        color: var(--rf-text);
        font-weight: 700;
        font-size: 1.25rem;
        letter-spacing: -0.02em;
        margin-top: 1.6rem;
        margin-bottom: 0.4rem;
        border: none;
    }

    .main .stMarkdown h3 {
        color: var(--rf-text);
        font-weight: 600;
        font-size: 1.05rem;
        letter-spacing: -0.01em;
    }

    .main .stMarkdown h4 {
        color: var(--rf-text-2);
        font-weight: 600;
        font-size: 0.95rem;
    }

    .main .stMarkdown p, .main .stMarkdown li {
        color: var(--rf-text-2);
        line-height: 1.65;
    }

    .main .stMarkdown a {
        color: var(--rf-accent);
        text-decoration: none;
    }

    .main .stMarkdown a:hover {
        text-decoration: underline;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--rf-text-3) !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid var(--rf-border) !important;
        margin: 1.6rem 0 !important;
    }

    /* ─── Sidebar ─────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--rf-surface);
        border-right: 1px solid var(--rf-border);
    }

    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: var(--rf-text);
        font-weight: 800;
        font-size: 1.25rem;
        letter-spacing: -0.02em;
    }

    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--rf-text);
        font-weight: 600;
        font-size: 0.95rem;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--rf-text-2);
        font-size: 0.88rem;
    }

    /* Sidebar nav links */
    [data-testid="stSidebarNav"] a {
        border-radius: var(--rf-radius-sm);
        color: var(--rf-text-2) !important;
        font-weight: 500;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: var(--rf-bg);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: var(--rf-accent-soft);
        color: var(--rf-accent) !important;
        font-weight: 600;
    }

    /* ─── Buttons ─────────────────────────────────────────────── */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: var(--rf-radius-sm);
        font-weight: 600;
        font-size: 0.92rem;
        padding: 0.5rem 1.2rem;
        transition: all 0.15s ease;
        box-shadow: var(--rf-shadow);
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: var(--rf-accent);
        color: #fff;
        border: 1px solid var(--rf-accent);
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--rf-accent-hover);
        border-color: var(--rf-accent-hover);
        box-shadow: var(--rf-shadow-md);
    }

    .stButton > button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"] {
        background: var(--rf-surface);
        color: var(--rf-text);
        border: 1px solid var(--rf-border-strong);
    }

    .stButton > button[kind="secondary"]:hover,
    .stFormSubmitButton > button[kind="secondary"]:hover {
        border-color: var(--rf-accent);
        color: var(--rf-accent);
        background: var(--rf-accent-soft);
    }

    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled {
        opacity: 0.45;
    }

    .stDownloadButton > button {
        background: var(--rf-surface) !important;
        border: 1px solid var(--rf-border-strong) !important;
        color: var(--rf-text) !important;
        border-radius: var(--rf-radius-sm);
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.15s ease;
        box-shadow: var(--rf-shadow);
    }

    .stDownloadButton > button:hover {
        border-color: var(--rf-accent) !important;
        color: var(--rf-accent) !important;
        background: var(--rf-accent-soft) !important;
    }

    /* ─── Inputs ──────────────────────────────────────────────── */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: var(--rf-surface) !important;
        border: 1px solid var(--rf-border-strong) !important;
        border-radius: var(--rf-radius-sm) !important;
        color: var(--rf-text) !important;
        font-size: 0.92rem !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: var(--rf-accent) !important;
        box-shadow: 0 0 0 3px var(--rf-accent-soft) !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--rf-text-3) !important;
    }

    .stSelectbox > div > div, .stMultiSelect > div > div {
        background: var(--rf-surface) !important;
        border: 1px solid var(--rf-border-strong) !important;
        border-radius: var(--rf-radius-sm) !important;
        color: var(--rf-text) !important;
    }

    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stNumberInput label, .stMultiSelect label, .stSlider label,
    .stRadio label, .stCheckbox label, .stFileUploader label {
        color: var(--rf-text-2) !important;
        font-weight: 500 !important;
        font-size: 0.86rem !important;
    }

    /* ─── Cards: expanders, forms, metrics ────────────────────── */
    div[data-testid="stExpander"] {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border) !important;
        border-radius: var(--rf-radius) !important;
        box-shadow: var(--rf-shadow);
        overflow: hidden;
    }

    div[data-testid="stExpander"] summary {
        color: var(--rf-text);
        font-weight: 600;
        font-size: 0.93rem;
    }

    div[data-testid="stExpander"] summary:hover {
        color: var(--rf-accent);
    }

    div[data-testid="stForm"] {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        padding: 1.4rem;
        box-shadow: var(--rf-shadow);
    }

    div[data-testid="stMetric"] {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        padding: 14px 18px;
        box-shadow: var(--rf-shadow);
    }

    div[data-testid="stMetric"] label {
        color: var(--rf-text-3) !important;
        font-size: 0.8rem;
        font-weight: 500;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--rf-text) !important;
        font-weight: 700;
        font-size: 1.5rem;
    }

    /* ─── Tabs ────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: transparent;
        border-bottom: 1px solid var(--rf-border);
        padding: 0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--rf-radius-sm) var(--rf-radius-sm) 0 0;
        color: var(--rf-text-3);
        font-weight: 600;
        font-size: 0.92rem;
        padding: 0.55rem 1.1rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--rf-text);
        background: var(--rf-bg);
    }

    .stTabs [aria-selected="true"] {
        color: var(--rf-accent) !important;
        background: transparent;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--rf-accent);
    }

    /* ─── Alerts ──────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: var(--rf-radius-sm);
        border: 1px solid var(--rf-border);
    }

    .stSuccess, div[data-baseweb="notification"][kind="positive"] {
        background: var(--rf-green-soft) !important;
        border-color: #BFE5CC !important;
        color: #14532D !important;
    }

    .stInfo {
        background: var(--rf-accent-soft) !important;
        border-color: var(--rf-accent-border) !important;
        color: #312E81 !important;
    }

    .stWarning {
        background: var(--rf-amber-soft) !important;
        border-color: #F2D9B5 !important;
        color: #78350F !important;
    }

    .stError {
        background: var(--rf-red-soft) !important;
        border-color: #F5C6C6 !important;
        color: #7F1D1D !important;
    }

    /* ─── Misc widgets ────────────────────────────────────────── */
    .stFileUploader > div {
        background: var(--rf-surface) !important;
        border: 1.5px dashed var(--rf-border-strong) !important;
        border-radius: var(--rf-radius) !important;
    }

    .stFileUploader > div:hover {
        border-color: var(--rf-accent) !important;
    }

    div[data-testid="stToast"] {
        background: var(--rf-text) !important;
        color: #fff !important;
        border-radius: var(--rf-radius-sm);
    }

    .stSpinner > div {
        border-color: var(--rf-accent) transparent transparent transparent !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        overflow: hidden;
        box-shadow: var(--rf-shadow);
    }

    div[data-testid="stChatMessage"] {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        box-shadow: var(--rf-shadow);
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--rf-border-strong); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--rf-text-3); }

    /* ─── Custom Components ───────────────────────────────────── */

    /* Status badge (sidebar system status) */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .status-badge::before {
        content: "";
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: currentColor;
    }

    .status-ready {
        background: var(--rf-green-soft);
        color: var(--rf-green);
        border: 1px solid #BFE5CC;
    }

    .status-empty {
        background: var(--rf-amber-soft);
        color: var(--rf-amber);
        border: 1px solid #F2D9B5;
    }

    /* Generic white card */
    .rf-card {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        padding: 20px 22px;
        box-shadow: var(--rf-shadow);
    }

    /* Dashboard feature card */
    .rf-feature {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        padding: 22px;
        min-height: 150px;
        box-shadow: var(--rf-shadow);
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }

    .rf-feature:hover {
        box-shadow: var(--rf-shadow-md);
        transform: translateY(-2px);
    }

    .rf-feature .rf-feature-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: var(--rf-accent-soft);
        color: var(--rf-accent);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .rf-feature .rf-feature-title {
        font-weight: 700;
        color: var(--rf-text);
        margin-bottom: 5px;
        font-size: 0.98rem;
    }

    .rf-feature .rf-feature-desc {
        color: var(--rf-text-2);
        font-size: 0.86rem;
        line-height: 1.5;
    }

    /* Big score display (gap analysis / ATS) */
    .rf-score-card {
        text-align: center;
        padding: 24px;
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        box-shadow: var(--rf-shadow);
        margin-bottom: 16px;
    }

    .rf-score-label {
        font-size: 0.85rem;
        color: var(--rf-text-3);
        font-weight: 500;
        margin-bottom: 2px;
    }

    .rf-score-value {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
    }

    /* Retrieved chunk / citation card */
    .rf-chunk {
        background: var(--rf-surface);
        border: 1px solid var(--rf-border);
        border-radius: var(--rf-radius);
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: var(--rf-shadow);
    }

    .rf-chunk-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }

    .rf-chunk-rank {
        font-weight: 700;
        color: var(--rf-text);
        font-size: 0.9rem;
    }

    .rf-chunk-body {
        color: var(--rf-text-2);
        font-size: 0.87rem;
        line-height: 1.55;
    }

    .rf-pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        background: var(--rf-bg);
        color: var(--rf-text-2);
        border: 1px solid var(--rf-border);
    }

    .rf-pill-green { background: var(--rf-green-soft); color: var(--rf-green); border-color: #BFE5CC; }
    .rf-pill-amber { background: var(--rf-amber-soft); color: var(--rf-amber); border-color: #F2D9B5; }
    .rf-pill-red   { background: var(--rf-red-soft);   color: var(--rf-red);   border-color: #F5C6C6; }
    .rf-pill-accent{ background: var(--rf-accent-soft); color: var(--rf-accent); border-color: var(--rf-accent-border); }

    /* Selectable style card (template picker) */
    .rf-style-card {
        border: 1.5px solid var(--rf-border);
        background: var(--rf-surface);
        border-radius: var(--rf-radius);
        padding: 18px 16px;
        text-align: center;
        min-height: 84px;
        box-shadow: var(--rf-shadow);
        transition: all 0.15s ease;
    }

    .rf-style-card.selected {
        border-color: var(--rf-accent);
        background: var(--rf-accent-soft);
        box-shadow: 0 0 0 3px var(--rf-accent-soft);
    }

    .rf-style-name {
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--rf-text);
    }

    .rf-style-desc {
        font-size: 0.8rem;
        color: var(--rf-text-3);
        margin-top: 5px;
    }

    /* Empty state */
    .rf-empty {
        text-align: center;
        padding: 56px 20px;
        color: var(--rf-text-3);
    }

    .rf-empty-icon { font-size: 2.4rem; margin-bottom: 10px; }
    .rf-empty-title { font-size: 1.05rem; font-weight: 600; color: var(--rf-text-2); }
    .rf-empty-sub { font-size: 0.85rem; margin-top: 6px; }

    /* Page header block */
    .rf-page-header { margin-bottom: 0.4rem; }
    .rf-page-title {
        color: var(--rf-text);
        font-weight: 800;
        font-size: 1.9rem;
        letter-spacing: -0.03em;
        margin: 0;
    }
    .rf-page-sub {
        color: var(--rf-text-2);
        font-size: 0.95rem;
        margin-top: 4px;
    }
    </style>
    """


def get_resume_preview_css() -> str:
    """CSS for the resume preview panel (paper-like document view)."""
    return """
    <style>
    .main .stMarkdown .resume-preview {
        background: #ffffff !important;
        color: #1A2033 !important;
        padding: 36px 44px !important;
        border-radius: 12px !important;
        border: 1px solid #E6E8EF !important;
        font-family: 'Inter', 'Calibri', sans-serif !important;
        font-size: 0.92rem !important;
        line-height: 1.6 !important;
        max-height: 600px !important;
        overflow-y: auto !important;
        box-shadow: 0 4px 12px rgba(16, 24, 40, 0.07) !important;
    }

    .main .stMarkdown .resume-preview h1 {
        color: #1A2033 !important;
        background: none !important;
        -webkit-text-fill-color: #1A2033 !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        text-align: center !important;
        margin-bottom: 4px !important;
        letter-spacing: normal !important;
    }

    .main .stMarkdown .resume-preview h2 {
        color: #2c3e6b !important;
        background: none !important;
        -webkit-text-fill-color: #2c3e6b !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        border-bottom: 2px solid #2c3e6b !important;
        padding-bottom: 4px !important;
        margin-top: 16px !important;
        margin-bottom: 8px !important;
        letter-spacing: normal !important;
    }

    .main .stMarkdown .resume-preview h3 {
        color: #34495e !important;
        background: none !important;
        -webkit-text-fill-color: #34495e !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        margin-top: 10px !important;
        margin-bottom: 4px !important;
        letter-spacing: normal !important;
    }

    .main .stMarkdown .resume-preview ul {
        margin: 4px 0 !important;
        padding-left: 20px !important;
    }

    .main .stMarkdown .resume-preview li {
        margin-bottom: 3px !important;
        color: #333333 !important;
        list-style-type: disc !important;
    }

    .main .stMarkdown .resume-preview p {
        color: #333333 !important;
        margin: 4px 0 !important;
    }
    </style>
    """
