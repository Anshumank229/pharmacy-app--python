# frontend/config.py
# ─────────────────────────────────────────
# Single source of truth for all constants.
#
# In production (Streamlit Cloud):
#   Set these in the Streamlit Cloud dashboard under App Settings → Secrets
#   Format (TOML):
#       API_URL       = "https://your-app.up.railway.app/api"
#       BACKEND_MEDIA = "https://your-app.up.railway.app/media"
#       ADMIN_API_KEY = "your-strong-key"
#
# In development:
#   Values fall back to localhost — no secrets.toml needed locally.
# ─────────────────────────────────────────
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(key: str, fallback: str) -> str:
    """Read from Streamlit secrets first (production), then env, then fallback."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, fallback)


API_URL         = _secret("API_URL",         "http://127.0.0.1:8000/api")
BACKEND_MEDIA   = _secret("BACKEND_MEDIA",   "http://127.0.0.1:8000/media")
ADMIN_API_KEY   = _secret("ADMIN_API_KEY",   "change-me-in-production")
ADMIN_HEADERS   = {"x-admin-key": ADMIN_API_KEY}
ADMIN_EMAIL     = _secret("ADMIN_EMAIL",     "kumaranshuman500@gmail.com")
WHATSAPP_NUMBER = _secret("WHATSAPP_NUMBER", "91XXXXXXXXXX")