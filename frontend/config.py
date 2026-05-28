# frontend/config.py
# ─────────────────────────────────────────
# Single source of truth for all constants.
# Change values here; every other file imports from here.
# ─────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv()

API_URL         = "http://127.0.0.1:8000/api"
BACKEND_MEDIA   = "http://127.0.0.1:8000/media"
ADMIN_API_KEY   = os.getenv("ADMIN_API_KEY", "change-me-in-production")
ADMIN_HEADERS   = {"x-admin-key": ADMIN_API_KEY}
ADMIN_EMAIL     = "kumaranshuman500@gmail.com"   # ← owner email for admin button
WHATSAPP_NUMBER = "91XXXXXXXXXX"                  # ← replace with real number
