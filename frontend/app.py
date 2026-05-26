"""
app.py — Entry point for the Medicine Delivery storefront.
Run with: streamlit run app.py
"""

import streamlit as st

from config import SESSION_DEFAULTS, API_URL, WHATSAPP_NUMBER
from theme import inject_theme
from auth import resolve_google_token, load_profile_once, render_auth_sidebar
from cart import render_cart_sidebar
from views.medicine_detail import render_medicine_detail
from views.profile import render_profile
from views.analytics import render_analytics
from views.admin import render_admin
from views.store import render_store


# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="MediCare — Local Pharmacy",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()


# ── Session state ─────────────────────────────────────────────
for key, val in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Auth ──────────────────────────────────────────────────────
resolve_google_token(API_URL)
load_profile_once(API_URL)


# ── Page routing ──────────────────────────────────────────────
if st.session_state.show_medicine_detail and st.session_state.selected_medicine_id:
    render_medicine_detail(API_URL)

if st.session_state.show_profile and st.session_state.user:
    render_profile(API_URL)

if st.session_state.show_analytics:
    render_analytics(API_URL)

if st.session_state.show_admin:
    render_admin(API_URL)


# ── Sidebar ───────────────────────────────────────────────────
render_auth_sidebar(API_URL)
render_cart_sidebar(API_URL, WHATSAPP_NUMBER)


# ── Hero ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <p class="hero-title">💊 Your Local Pharmacy</p>
    <p class="hero-subtitle">
        Medicines delivered to your door within 24 hours.<br>
        No advance payment — pay cash on delivery.
    </p>
    <a class="hero-pill" href="https://wa.me/{WHATSAPP_NUMBER}?text=Hi,%20I%20need%20help%20with%20my%20order"
       target="_blank">
        💬 WhatsApp Support
    </a>
    <span class="badge badge-green">✓ Free Delivery</span>
    &nbsp;
    <span class="badge badge-blue">⚡ Same Day Dispatch</span>
</div>
""", unsafe_allow_html=True)


# ── Store ─────────────────────────────────────────────────────
render_store(API_URL)
