# frontend/auth.py
# ─────────────────────────────────────────
# Three responsibilities:
#   1. init_session_state()  – safe defaults on every cold start
#   2. handle_google_redirect() – catch ?email=&name= after OAuth
#   3. load_profile_once()   – merge saved address/phone into user dict
# ─────────────────────────────────────────
import streamlit as st
import requests
from config import API_URL


def init_session_state():
    defaults = {
        "show_profile":         False,
        "show_admin":           False,
        "show_analytics":       False,
        "show_medicine_detail": False,
        "selected_medicine_id": None,
        "cart":                 [],
        "user":                 None,
        "last_area_name":       "",
        "last_pending_count":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def handle_google_redirect():
    qp = st.query_params
    if "email" not in qp or "name" not in qp:
        return
    email, name = qp["email"], qp["name"]
    try:
        r = requests.get(f"{API_URL}/me", params={"email": email}, timeout=5)
        is_admin = r.json().get("is_admin", False) if r.ok else False
    except requests.exceptions.RequestException:
        is_admin = False

    st.session_state.user = {"name": name, "email": email, "is_admin": is_admin}
    # FIX: clear params first, then rerun so the logged-in sidebar renders
    st.query_params.clear()
    st.rerun()


def load_profile_once():
    if not st.session_state.user or "profile_loaded" in st.session_state:
        return
    try:
        r = requests.get(
            f"{API_URL}/profile",
            params={"email": st.session_state.user["email"]},
            timeout=5,
        )
        if r.status_code == 200:
            p = r.json()
            st.session_state.user.update({
                "phone":     p.get("phone",     ""),
                "address":   p.get("address",   ""),
                "pincode":   p.get("pincode",   ""),
                "area_name": p.get("area_name", ""),
            })
    except requests.exceptions.RequestException:
        pass
    st.session_state.profile_loaded = True