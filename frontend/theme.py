"""
theme.py — Professional design system for Medicine Delivery app.
Inject once in app.py via: from theme import inject_theme; inject_theme()
"""

import streamlit as st


def inject_theme():
    st.markdown("""
    <style>
    /* ============================================================
       FONTS
    ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap');

    /* ============================================================
       CSS VARIABLES — single source of truth
    ============================================================ */
    :root {
        --bg:           #0a0f1e;
        --bg-card:      #111827;
        --bg-card-hover:#151f30;
        --bg-sidebar:   #0d1424;
        --border:       rgba(255,255,255,0.07);
        --border-focus: rgba(99,179,237,0.5);

        --accent:       #3b82f6;
        --accent-light: #60a5fa;
        --accent-glow:  rgba(59,130,246,0.15);
        --green:        #10b981;
        --green-bg:     rgba(16,185,129,0.1);
        --red:          #ef4444;
        --red-bg:       rgba(239,68,68,0.1);
        --amber:        #f59e0b;
        --amber-bg:     rgba(245,158,11,0.1);

        --text-primary:   #f0f4ff;
        --text-secondary: #8b9cc8;
        --text-muted:     #4a5578;

        --radius:    12px;
        --radius-lg: 18px;
        --radius-sm: 8px;
        --shadow:    0 4px 24px rgba(0,0,0,0.4);
        --shadow-lg: 0 8px 40px rgba(0,0,0,0.6);

        --font-body:    'DM Sans', sans-serif;
        --font-mono:    'DM Mono', monospace;
        --font-display: 'Fraunces', serif;
    }

    /* ============================================================
       GLOBAL RESET & BASE
    ============================================================ */
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }

    /* Remove Streamlit's default padding top */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1200px !important;
    }

    /* Hide Streamlit branding & menu */
    #MainMenu, footer, header { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* ============================================================
       SIDEBAR
    ============================================================ */
    [data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem !important;
    }

    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-family: var(--font-body) !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        margin-bottom: 0.75rem !important;
        padding-top: 0.5rem !important;
    }

    /* ============================================================
       TYPOGRAPHY
    ============================================================ */
    h1 {
        font-family: var(--font-display) !important;
        font-size: 2.8rem !important;
        font-weight: 300 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em !important;
        line-height: 1.15 !important;
    }

    h2 {
        font-family: var(--font-body) !important;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    h3 {
        font-family: var(--font-body) !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    p, .stMarkdown p {
        color: var(--text-secondary) !important;
        line-height: 1.7 !important;
        font-size: 0.95rem !important;
    }

    /* ============================================================
       BUTTONS
    ============================================================ */
    .stButton > button {
        font-family: var(--font-body) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid var(--border) !important;
        background: rgba(255,255,255,0.04) !important;
        color: var(--text-primary) !important;
        width: 100% !important;
    }

    .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.15) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid*="primary"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #fff !important;
        box-shadow: 0 0 20px var(--accent-glow) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--accent-light) !important;
        border-color: var(--accent-light) !important;
        box-shadow: 0 0 30px rgba(59,130,246,0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Disabled button */
    .stButton > button:disabled {
        opacity: 0.3 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }

    /* ============================================================
       INPUTS & TEXTAREAS
    ============================================================ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
        font-size: 0.9rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
        outline: none !important;
    }

    /* Input labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stFileUploader label,
    .stSlider label {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        margin-bottom: 0.3rem !important;
    }

    /* ============================================================
       SELECTBOX
    ============================================================ */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ============================================================
       METRICS
    ============================================================ */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.25rem 1.5rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
    }

    [data-testid="stMetricValue"] {
        font-family: var(--font-display) !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    /* ============================================================
       EXPANDERS
    ============================================================ */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        transition: background 0.2s !important;
    }

    .streamlit-expanderHeader:hover {
        background: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
        padding: 1rem !important;
    }

    /* ============================================================
       ALERTS & MESSAGES
    ============================================================ */
    .stSuccess {
        background: var(--green-bg) !important;
        border: 1px solid rgba(16,185,129,0.25) !important;
        border-radius: var(--radius-sm) !important;
        color: #6ee7b7 !important;
    }

    .stError, .stException {
        background: var(--red-bg) !important;
        border: 1px solid rgba(239,68,68,0.25) !important;
        border-radius: var(--radius-sm) !important;
        color: #fca5a5 !important;
    }

    .stWarning {
        background: var(--amber-bg) !important;
        border: 1px solid rgba(245,158,11,0.25) !important;
        border-radius: var(--radius-sm) !important;
        color: #fcd34d !important;
    }

    .stInfo {
        background: var(--accent-glow) !important;
        border: 1px solid rgba(59,130,246,0.25) !important;
        border-radius: var(--radius-sm) !important;
        color: #93c5fd !important;
    }

    /* ============================================================
       DATAFRAME / TABLES
    ============================================================ */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }

    .dvn-scroller { background: var(--bg-card) !important; }

    /* ============================================================
       TABS
    ============================================================ */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        color: var(--text-muted) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.2rem !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--accent-light) !important;
        border-bottom-color: var(--accent) !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem !important;
    }

    /* ============================================================
       DIVIDER
    ============================================================ */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ============================================================
       FILE UPLOADER
    ============================================================ */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 0.75rem !important;
        transition: border-color 0.2s !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
    }

    /* ============================================================
       SLIDER
    ============================================================ */
    [data-testid="stSlider"] > div > div > div {
        background: var(--accent) !important;
    }

    /* ============================================================
       MEDICINE CARDS (custom classes injected via st.markdown)
    ============================================================ */
    .med-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.25rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        height: 100%;
    }

    .med-card:hover {
        .med-card:hover {
    transform: translateY(-8px);

    box-shadow:
    0 20px 50px rgba(0,0,0,.55);

    border-color:
    rgba(59,130,246,.4);
}
    }

    .med-card-name {
        font-family: var(--font-body);
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0.5rem 0 0.25rem;
    }

    .med-card-price {
        font-family: var(--font-mono);
        font-size: 1.2rem;
        font-weight: 500;
        color: var(--accent-light);
    }

    .badge {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
    }

    .badge-green  { background: var(--green-bg);  color: #6ee7b7; border: 1px solid rgba(16,185,129,0.25); }
    .badge-red    { background: var(--red-bg);    color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
    .badge-amber  { background: var(--amber-bg);  color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); }
    .badge-blue   { background: var(--accent-glow); color: #93c5fd; border: 1px solid rgba(59,130,246,0.25); }
    .badge-rx     { background: rgba(167,139,250,0.1); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.25); }

    /* ============================================================
       HERO SECTION
    ============================================================ */
    .hero {
        background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(16,185,129,0.05) 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%);
        pointer-events: none;
    }

    .hero-title {
        font-family: var(--font-display) !important;
        font-size: 2.6rem !important;
        font-weight: 300 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
        margin: 0 0 0.5rem !important;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin: 0 0 1.5rem !important;
    }

    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(16,185,129,0.1);
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 500;
        color: #6ee7b7;
        text-decoration: none;
        margin-right: 0.5rem;
        transition: background 0.2s;
    }

    .hero-pill:hover { background: rgba(16,185,129,0.18); }

    /* ============================================================
       SECTION HEADERS
    ============================================================ */
    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 1rem;
    }

    /* ============================================================
       CART ITEM ROW
    ============================================================ */
    .cart-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0;
        border-bottom: 1px solid var(--border);
        font-size: 0.875rem;
    }

    .cart-name { color: var(--text-primary); font-weight: 500; }
    .cart-price { color: var(--accent-light); font-family: var(--font-mono); font-size: 0.85rem; }

    /* ============================================================
       ORDER STATUS CHIPS
    ============================================================ */
    .status-chip {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .status-PENDING   { background: var(--amber-bg);  color: #fcd34d; }
    .status-SHIPPED   { background: var(--accent-glow); color: #93c5fd; }
    .status-DELIVERED { background: var(--green-bg);  color: #6ee7b7; }
    .status-CANCELLED { background: var(--red-bg);    color: #fca5a5; }

    /* ============================================================
       SCROLLBAR
    ============================================================ */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

    /* ============================================================
       RESPONSIVE
    ============================================================ */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { min-width: 100% !important; }
        .hero { padding: 1.5rem !important; }
        .hero-title { font-size: 1.8rem !important; }
        h1 { font-size: 2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)