# frontend/theme.py
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700;9..144,800&display=swap');

/* ══════════════════════════════════════════════
   CSS VARIABLES
══════════════════════════════════════════════ */
:root {
  --bg-deep:        #020817;
  --bg-base:        #060d1a;
  --bg-card:        #0b1425;
  --bg-elevated:    #0f1c30;
  --bg-hover:       #14243d;
  --bg-glass:       rgba(11,20,37,0.7);

  --border-subtle:  rgba(255,255,255,0.05);
  --border-medium:  rgba(255,255,255,0.09);
  --border-accent:  rgba(56,189,248,0.2);
  --border-gold:    rgba(251,191,36,0.2);

  --accent-gold:    #f59e0b;
  --accent-gold-lt: #fde68a;
  --accent-cyan:    #38bdf8;
  --accent-cyan-lt: #bae6fd;
  --accent-green:   #34d399;
  --accent-green-lt:#a7f3d0;
  --accent-red:     #f87171;
  --accent-purple:  #c084fc;
  --accent-blue:    #818cf8;

  --text-primary:   #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted:     #475569;
  --text-xmuted:    #1e3a5f;

  --radius-xs:  6px;
  --radius-sm:  10px;
  --radius-md:  16px;
  --radius-lg:  22px;
  --radius-xl:  30px;

  --shadow-card:  0 1px 3px rgba(0,0,0,0.5), 0 8px 32px rgba(0,0,0,0.3);
  --shadow-hover: 0 20px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(56,189,248,0.12), 0 0 40px rgba(56,189,248,0.06);
  --shadow-glow:  0 0 40px rgba(56,189,248,0.12);
  --shadow-gold:  0 0 40px rgba(245,158,11,0.08);
}

/* ══════════════════════════════════════════════
   BASE
══════════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  background: var(--bg-deep) !important;
  color: var(--text-primary) !important;
}
h1, h2, h3, h4 {
  font-family: 'Fraunces', serif !important;
  letter-spacing: -0.02em;
  color: var(--text-primary) !important;
}

#MainMenu, footer { visibility: hidden; }

/* Hide Streamlit branding but keep the sidebar toggle visible */
header[data-testid="stHeader"] {
  background: transparent !important;
  border-bottom: none !important;
}
header[data-testid="stHeader"] > div:first-child {
  visibility: hidden;  /* hides the Streamlit logo/menu area */
}
/* But keep the collapse button visible */
[data-testid="collapsedControl"],
button[kind="header"],
[data-testid="stSidebarCollapsedControl"] {
  visibility: visible !important;
  opacity: 1 !important;
}
.block-container {
  padding-top: 1.2rem !important;
  max-width: 1340px;
}

/* Subtle grid texture on body */
body::before {
  content: '';
  position: fixed; inset: 0; z-index: -1;
  background-image:
    linear-gradient(rgba(56,189,248,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56,189,248,0.015) 1px, transparent 1px);
  background-size: 64px 64px;
  pointer-events: none;
}

/* ══════════════════════════════════════════════
   INPUTS
══════════════════════════════════════════════ */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-medium) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 0.875rem !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
input:focus, textarea:focus {
  border-color: rgba(56,189,248,0.45) !important;
  box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
  outline: none !important;
}
[data-baseweb="input"] {
  background: var(--bg-elevated) !important;
}
input::placeholder { color: var(--text-muted) !important; }

/* ══════════════════════════════════════════════
   SELECTBOX
══════════════════════════════════════════════ */
[data-baseweb="select"] > div {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-medium) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-size: 0.875rem !important;
  transition: border-color 0.2s !important;
}
[data-baseweb="select"] > div:hover {
  border-color: rgba(56,189,248,0.3) !important;
}

/* ══════════════════════════════════════════════
   BUTTONS — complete overhaul
══════════════════════════════════════════════ */
.stButton button {
  border-radius: var(--radius-sm) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  padding: 0.5rem 1.1rem !important;
  transition: all 0.18s cubic-bezier(.4,0,.2,1) !important;
  border: 1px solid var(--border-medium) !important;
  background: var(--bg-elevated) !important;
  color: var(--text-secondary) !important;
  letter-spacing: 0.01em !important;
  position: relative !important;
  overflow: hidden !important;
}
.stButton button::before {
  content: '' !important;
  position: absolute !important; inset: 0 !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.03), transparent) !important;
  pointer-events: none !important;
}
.stButton button:hover {
  border-color: rgba(56,189,248,0.3) !important;
  color: var(--text-primary) !important;
  background: var(--bg-hover) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
  transform: translateY(-1px) !important;
}
.stButton button[kind="primary"] {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%) !important;
  border: 1px solid rgba(56,189,248,0.35) !important;
  color: #fff !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em !important;
  box-shadow: 0 2px 16px rgba(14,165,233,0.2), inset 0 1px 0 rgba(255,255,255,0.1) !important;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
}
.stButton button[kind="primary"]:hover {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%) !important;
  box-shadow: 0 6px 28px rgba(14,165,233,0.35), inset 0 1px 0 rgba(255,255,255,0.15) !important;
  transform: translateY(-2px) !important;
}
.stButton button:disabled {
  opacity: 0.35 !important;
  transform: none !important;
}

/* ══════════════════════════════════════════════
   DIVIDER
══════════════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--border-subtle) !important;
  margin: 1.2rem 0 !important;
}

/* ══════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-sm) !important;
  transition: border-color 0.2s !important;
}
[data-testid="stExpander"]:hover {
  border-color: var(--border-medium) !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.01em !important;
}

/* ══════════════════════════════════════════════
   METRIC CARDS
══════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.2rem 1.5rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent-cyan), transparent 70%);
  opacity: 0.7;
}
[data-testid="stMetric"]:hover {
  border-color: var(--border-accent);
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
}
[data-testid="stMetricLabel"] {
  font-size: 0.65rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Fraunces', serif !important;
  font-size: 1.8rem !important;
  color: var(--text-primary) !important;
  font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* ══════════════════════════════════════════════
   HERO BANNER — elevated
══════════════════════════════════════════════ */
.hero {
  background:
    radial-gradient(ellipse 100% 120% at 90% 30%, rgba(56,189,248,0.09) 0%, transparent 50%),
    radial-gradient(ellipse 60% 80% at 5% 90%, rgba(245,158,11,0.06) 0%, transparent 50%),
    radial-gradient(ellipse 40% 60% at 50% 0%, rgba(129,140,248,0.04) 0%, transparent 50%),
    linear-gradient(160deg, #0c1829 0%, #0f2040 50%, #070e1c 100%);
  border: 1px solid rgba(56,189,248,0.14);
  border-radius: var(--radius-xl);
  padding: 2.8rem 3.2rem;
  margin-bottom: 1.8rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(56,189,248,0.08);
}
.hero::before {
  content: '💊';
  position: absolute; top: -20px; right: 40px;
  font-size: 10rem; opacity: 0.03; line-height: 1;
  pointer-events: none; user-select: none;
}
.hero::after {
  content: '';
  position: absolute; bottom: -60px; left: 20%;
  width: 400px; height: 200px;
  background: radial-gradient(ellipse, rgba(245,158,11,0.04) 0%, transparent 60%);
  pointer-events: none;
}
.hero-eyebrow {
  font-size: 0.65rem; font-weight: 800;
  letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--accent-cyan); margin-bottom: 0.6rem;
  display: flex; align-items: center; gap: 8px;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.hero-eyebrow::after {
  content: '';
  flex: 1; max-width: 40px; height: 1px;
  background: linear-gradient(90deg, var(--accent-cyan), transparent);
  opacity: 0.5;
}
.hero-title {
  font-family: 'Fraunces', serif;
  font-size: 2.8rem; font-weight: 800;
  color: var(--text-primary); margin: 0 0 0.5rem;
  line-height: 1.1; letter-spacing: -0.03em;
}
.hero-title span {
  background: linear-gradient(135deg, var(--accent-cyan-lt) 0%, var(--accent-cyan) 60%, #0ea5e9 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  color: var(--text-secondary);
  font-size: 0.92rem; margin-bottom: 1.4rem;
  line-height: 1.7; max-width: 500px;
  font-weight: 400;
}
.hero-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 1.2rem; }
.hero-chip {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 100px; padding: 6px 16px;
  font-size: 0.75rem; color: var(--text-secondary);
  display: inline-flex; align-items: center; gap: 6px;
  font-weight: 600; letter-spacing: 0.02em;
  backdrop-filter: blur(8px);
  transition: all 0.2s;
}
.hero-chip:hover { transform: translateY(-1px); }
.hero-chip.green {
  border-color: rgba(52,211,153,0.25);
  color: var(--accent-green-lt);
  background: rgba(52,211,153,0.06);
}
.hero-chip.blue {
  border-color: rgba(56,189,248,0.25);
  color: var(--accent-cyan-lt);
  background: rgba(56,189,248,0.06);
}
.hero-chip.gold {
  border-color: rgba(245,158,11,0.25);
  color: var(--accent-gold-lt);
  background: rgba(245,158,11,0.06);
}
.wa-btn {
  display: inline-flex; align-items: center; gap: 9px;
  background: rgba(37,211,102,0.07);
  border: 1px solid rgba(37,211,102,0.25);
  border-radius: 100px; padding: 10px 24px;
  color: #6ee7b7 !important; text-decoration: none !important;
  font-size: 0.85rem; font-weight: 700;
  transition: all 0.2s ease;
  letter-spacing: 0.02em;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 12px rgba(37,211,102,0.08);
}
.wa-btn:hover {
  background: rgba(37,211,102,0.14);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(37,211,102,0.18);
}

/* ══════════════════════════════════════════════
   FILTER BAR
══════════════════════════════════════════════ */
.filter-bar {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem 1.4rem;
  margin-bottom: 1.4rem;
  backdrop-filter: blur(12px);
}
.section-label {
  font-size: 0.58rem; font-weight: 800;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--text-xmuted); margin-bottom: 0.8rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ══════════════════════════════════════════════
   MEDICINE CARD — full redesign
══════════════════════════════════════════════ */
.med-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(.4,0,.2,1);
  box-shadow: var(--shadow-card);
  margin-bottom: 1.2rem;
  position: relative;
}
.med-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(56,189,248,0.5) 50%, transparent 100%);
  opacity: 0; transition: opacity 0.3s;
  z-index: 1;
}
.med-card:hover {
  border-color: rgba(56,189,248,0.2);
  transform: translateY(-6px) scale(1.005);
  box-shadow: var(--shadow-hover);
}
.med-card:hover::before { opacity: 1; }

.med-img-wrap {
  width: 100%; height: 185px; overflow: hidden;
  background: linear-gradient(145deg, #0d1e3a, #060d1c);
  display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
}
.med-img-wrap::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(to bottom, transparent 60%, rgba(11,20,37,0.8) 100%);
  pointer-events: none;
}
.med-img-wrap img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s ease; }
.med-card:hover .med-img-wrap img { transform: scale(1.04); }
.med-img-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.med-img-placeholder-icon { font-size: 2.5rem; opacity: 0.12; }
.med-img-placeholder-text {
  color: var(--text-xmuted); font-size: 0.65rem;
  letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700;
}

.med-body { padding: 1.1rem 1.2rem 0.5rem; }
.med-brand {
  font-size: 0.62rem; color: var(--accent-cyan);
  text-transform: uppercase; letter-spacing: 0.16em;
  margin-bottom: 5px; font-weight: 800;
}
.med-name {
  font-family: 'Fraunces', serif;
  font-size: 1.08rem; font-weight: 700;
  color: var(--text-primary); margin-bottom: 2px;
  line-height: 1.25;
}
.med-desc-short {
  font-size: 0.73rem; color: var(--text-muted);
  line-height: 1.5; margin-bottom: 10px;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.med-price-row {
  display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px;
}
.med-price {
  font-family: 'Fraunces', serif;
  font-size: 1.55rem; font-weight: 700;
  color: var(--accent-gold);
  letter-spacing: -0.02em;
}
.med-price-unit {
  font-size: 0.68rem; color: var(--text-muted); font-weight: 500;
}
.med-badges { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }

.med-footer {
  padding: 0 1.2rem 1.1rem;
  display: flex; flex-direction: column; gap: 7px;
}

/* ══════════════════════════════════════════════
   BADGE SYSTEM — refined
══════════════════════════════════════════════ */
.badge-instock {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(52,211,153,0.08); color: var(--accent-green-lt);
  border: 1px solid rgba(52,211,153,0.22);
  border-radius: 100px; padding: 3px 11px;
  font-size: 0.64rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
}
.badge-instock::before { content: '●'; color: var(--accent-green); font-size: 0.5rem; }

.badge-low {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(245,158,11,0.08); color: #fde68a;
  border: 1px solid rgba(245,158,11,0.22);
  border-radius: 100px; padding: 3px 11px;
  font-size: 0.64rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em;
}
.badge-low::before { content: '●'; color: var(--accent-gold); font-size: 0.5rem; }

.badge-out {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(248,113,113,0.08); color: #fca5a5;
  border: 1px solid rgba(248,113,113,0.18);
  border-radius: 100px; padding: 3px 11px;
  font-size: 0.64rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em;
}
.badge-out::before { content: '●'; color: var(--accent-red); font-size: 0.5rem; }

.badge-rx {
  display: inline-flex; align-items: center; gap: 4px;
  background: rgba(192,132,252,0.08); color: var(--accent-purple);
  border: 1px solid rgba(192,132,252,0.22);
  border-radius: 100px; padding: 3px 11px;
  font-size: 0.64rem; font-weight: 700;
  letter-spacing: 0.04em;
}

/* ══════════════════════════════════════════════
   MEDICINE DETAIL PAGE
══════════════════════════════════════════════ */
.detail-hero {
  background:
    radial-gradient(ellipse 70% 100% at 95% 50%, rgba(56,189,248,0.07) 0%, transparent 55%),
    radial-gradient(ellipse 40% 60% at 0% 100%, rgba(245,158,11,0.04) 0%, transparent 50%),
    linear-gradient(150deg, #0c1829 0%, #101e36 60%, #070d1a 100%);
  border: 1px solid rgba(56,189,248,0.12);
  border-radius: var(--radius-xl); padding: 2.4rem 2.8rem; margin-bottom: 1.8rem;
  position: relative; overflow: hidden;
  box-shadow: 0 4px 40px rgba(0,0,0,0.4);
}
.detail-hero::before {
  content: '';
  position: absolute; top: -100px; right: -100px;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(56,189,248,0.06) 0%, transparent 60%);
  pointer-events: none;
}
.detail-brand {
  font-size: 0.65rem; color: var(--accent-cyan);
  text-transform: uppercase; letter-spacing: 0.18em;
  margin-bottom: 6px; font-weight: 800;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.detail-title {
  font-family: 'Fraunces', serif;
  font-size: 2.2rem; font-weight: 800;
  color: var(--text-primary); margin-bottom: 4px; line-height: 1.15;
}
.detail-price {
  font-family: 'Fraunces', serif;
  font-size: 2.4rem; font-weight: 700;
  color: var(--accent-gold); margin: 0.7rem 0 1rem;
  letter-spacing: -0.025em;
}
.info-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs); padding: 6px 14px;
  font-size: 0.8rem; color: var(--text-secondary);
  margin: 3px 5px 3px 0;
  transition: border-color 0.2s;
}
.info-pill:hover { border-color: var(--border-medium); }
.info-pill b { color: var(--text-muted); font-weight: 600; font-size: 0.7rem; }
.detail-desc {
  background: rgba(6,13,26,0.6);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.2rem 1.4rem;
  color: var(--text-secondary); font-size: 0.88rem; line-height: 1.75;
  margin-top: 1rem;
}

/* ══════════════════════════════════════════════
   REVIEW CARD
══════════════════════════════════════════════ */
.review-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.1rem 1.3rem; margin-bottom: 0.7rem;
  transition: border-color 0.2s, transform 0.2s;
}
.review-card:hover { border-color: var(--border-medium); transform: translateX(2px); }
.review-author {
  font-weight: 700; color: var(--text-primary); font-size: 0.9rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.review-stars { font-size: 0.8rem; margin: 3px 0 6px; letter-spacing: 2px; }
.review-text { color: var(--text-secondary); font-size: 0.84rem; line-height: 1.65; }
.review-avg {
  font-family: 'Fraunces', serif;
  font-size: 1.8rem; font-weight: 700; color: var(--text-primary);
}
.review-avg-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

/* ══════════════════════════════════════════════
   ORDER CARD (profile page)
══════════════════════════════════════════════ */
.order-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.2rem 1.5rem; margin-bottom: 0.8rem;
  transition: all 0.22s;
  position: relative; overflow: hidden;
}
.order-card::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--accent-cyan), rgba(56,189,248,0.2));
  border-radius: 0;
}
.order-card:hover { border-color: var(--border-accent); transform: translateX(3px); box-shadow: var(--shadow-hover); }
.order-header {
  display: flex; justify-content: space-between;
  align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;
}
.order-id { font-weight: 700; color: var(--text-primary); font-size: 0.95rem; }
.order-date { font-size: 0.7rem; color: var(--text-muted); margin-top: 2px; }
.order-total {
  font-family: 'Fraunces', serif;
  font-size: 1.1rem; font-weight: 700; color: var(--accent-gold);
}
.pill-pending {
  background: rgba(245,158,11,0.09); color: #fde68a;
  border: 1px solid rgba(245,158,11,0.25); border-radius: 100px;
  padding: 3px 13px; font-size: 0.67rem; font-weight: 700;
}
.pill-shipped {
  background: rgba(56,189,248,0.09); color: var(--accent-cyan-lt);
  border: 1px solid rgba(56,189,248,0.25); border-radius: 100px;
  padding: 3px 13px; font-size: 0.67rem; font-weight: 700;
}
.pill-delivered {
  background: rgba(52,211,153,0.09); color: var(--accent-green-lt);
  border: 1px solid rgba(52,211,153,0.25); border-radius: 100px;
  padding: 3px 13px; font-size: 0.67rem; font-weight: 700;
}
.pill-cancelled {
  background: rgba(248,113,113,0.09); color: #fca5a5;
  border: 1px solid rgba(248,113,113,0.25); border-radius: 100px;
  padding: 3px 13px; font-size: 0.67rem; font-weight: 700;
}
.order-item-row {
  font-size: 0.82rem; color: var(--text-secondary);
  padding: 5px 0; border-bottom: 1px solid var(--border-subtle);
  display: flex; justify-content: space-between;
}

/* ══════════════════════════════════════════════
   SIDEBAR — premium
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: #03070f !important;
  border-right: 1px solid rgba(56,189,248,0.07) !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 0.8rem !important; }

/* Animated gradient line on sidebar edge */
[data-testid="stSidebar"]::before {
  content: '';
  position: fixed; top: 0; left: 0; bottom: 0; width: 1px;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(56,189,248,0.4) 30%,
    rgba(245,158,11,0.3) 70%,
    transparent 100%
  );
  opacity: 0.5;
  pointer-events: none;
  z-index: 100;
}

.sidebar-section { margin-top: 1.1rem; margin-bottom: 0.4rem; }
.sidebar-label {
  font-size: 0.55rem; font-weight: 800; letter-spacing: 0.22em;
  text-transform: uppercase; color: rgba(56,189,248,0.4);
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* App brand in sidebar */
.sidebar-brand {
  padding: 0.6rem 0 0.4rem;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 0.8rem;
}
.sidebar-brand-name {
  font-family: 'Fraunces', serif;
  font-size: 1.3rem; font-weight: 800;
  background: linear-gradient(135deg, var(--accent-cyan-lt), var(--accent-cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; line-height: 1.1;
}
.sidebar-brand-sub {
  font-size: 0.62rem; color: var(--text-muted);
  font-weight: 500; letter-spacing: 0.04em; margin-top: 2px;
}

.user-card {
  background: linear-gradient(135deg, rgba(56,189,248,0.06), rgba(56,189,248,0.02));
  border: 1px solid rgba(56,189,248,0.15);
  border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 10px;
  position: relative; overflow: hidden;
}
.user-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56,189,248,0.5), transparent);
}
.user-card-label {
  font-size: 0.55rem; color: var(--accent-cyan);
  font-weight: 800; text-transform: uppercase; letter-spacing: 0.14em;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.user-card-name {
  font-weight: 700; color: var(--text-primary);
  font-size: 0.92rem; margin-top: 3px;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.user-card-email { font-size: 0.7rem; color: var(--text-muted); margin-top: 2px; }

.cart-row {
  display: flex; justify-content: space-between;
  padding: 6px 0; border-bottom: 1px solid var(--border-subtle);
  font-size: 0.79rem; color: var(--text-secondary);
  gap: 8px;
}
.cart-row span:first-child {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cart-total-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 10px; padding-top: 8px;
  border-top: 1px solid var(--border-medium);
}
.cart-total-label {
  font-size: 0.62rem; color: var(--text-muted);
  font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
}
.cart-total-value {
  font-family: 'Fraunces', serif;
  font-size: 1.15rem; font-weight: 700; color: var(--accent-gold);
}

/* ══════════════════════════════════════════════
   ADMIN PANEL
══════════════════════════════════════════════ */
.admin-order-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.1rem 1.3rem; margin-bottom: 0.9rem;
  transition: all 0.2s;
}
.admin-order-card:hover { border-color: var(--border-medium); transform: translateY(-1px); }
.admin-order-id { font-weight: 700; color: var(--text-primary); font-size: 0.92rem; }
.admin-order-meta { font-size: 0.79rem; color: var(--text-muted); margin-top: 4px; }
.alert-expired {
  background: rgba(248,113,113,0.06);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: var(--radius-xs); padding: 0.75rem 1rem; margin-bottom: 0.5rem;
  font-size: 0.85rem;
}
.alert-expiring {
  background: rgba(245,158,11,0.05);
  border: 1px solid rgba(245,158,11,0.18);
  border-radius: var(--radius-xs); padding: 0.75rem 1rem; margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

/* ══════════════════════════════════════════════
   PROFILE PAGE
══════════════════════════════════════════════ */
.profile-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1.6rem 1.8rem; margin-bottom: 1.4rem;
}
.page-title {
  font-family: 'Fraunces', serif;
  font-size: 2rem; font-weight: 800;
  color: var(--text-primary); margin-bottom: 0.2rem;
}
.page-sub { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.4rem; }

/* ══════════════════════════════════════════════
   RESULT COUNT PILL
══════════════════════════════════════════════ */
.result-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 100px; padding: 4px 14px;
  font-size: 0.72rem; color: var(--text-muted); font-weight: 600;
  letter-spacing: 0.04em;
  margin-bottom: 1rem;
}
.result-pill span { color: var(--accent-cyan); font-weight: 700; }

/* ══════════════════════════════════════════════
   SUGGESTION DROPDOWN
══════════════════════════════════════════════ */
.sugg-box {
  background: var(--bg-elevated);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-top: -6px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(56,189,248,0.05);
  backdrop-filter: blur(12px);
}

/* ══════════════════════════════════════════════
   TOAST
══════════════════════════════════════════════ */
[data-testid="stToast"] {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-accent) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 0.85rem !important;
  box-shadow: var(--shadow-hover) !important;
}

/* ══════════════════════════════════════════════
   SCROLLBAR
══════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb {
  background: rgba(56,189,248,0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(56,189,248,0.3); }

/* ══════════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════════ */
@media (max-width: 768px) {
  .hero-title  { font-size: 1.8rem; }
  .detail-title { font-size: 1.6rem; }
  .hero { padding: 1.8rem 1.6rem; }
}
</style>
"""

_SCROLL_JS = """
<script>
window.scrollTo(0, 0);
const main = window.parent.document.querySelector('.main');
if (main) main.scrollTop = 0;
</script>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def scroll_to_top():
    st.markdown(_SCROLL_JS, unsafe_allow_html=True)
