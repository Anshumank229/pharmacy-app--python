# frontend/auth.py
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
        "access_token":         None,   # ← NEW
        "last_area_name":       "",
        "last_pending_count":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def auth_headers() -> dict:
    """Call this on every protected API request."""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def handle_google_redirect():
    qp = st.query_params
    if "token" not in qp:
        return

    token = qp["token"]
    st.query_params.clear()

    try:
        r = requests.get(f"{API_URL}/resolve-token", params={"token": token}, timeout=5)
        if not r.ok:
            st.error("Login failed or link expired. Please try again.")
            return
        data  = r.json()
        email = data.get("email", "")
        name  = data.get("name", "")
    except requests.exceptions.RequestException:
        st.warning("Could not verify login — check your connection and try again.")
        return

    # Google OAuth: get JWT token from backend using the resolved email
    try:
        login_r = requests.post(
            f"{API_URL}/login-google",   # you'll add this endpoint, OR reuse /login with a flag
            json={"email": email},
            timeout=5,
        )
        if login_r.ok:
            d = login_r.json()
            st.session_state.access_token = d.get("access_token")
            is_admin = d.get("is_admin", False)
        else:
            # fallback: no token, limited access
            is_admin = False
    except requests.exceptions.RequestException:
        is_admin = False

    st.session_state.user = {"name": name, "email": email, "is_admin": is_admin}


def load_profile_once():
    if not st.session_state.user or "profile_loaded" in st.session_state:
        return

    try:
        r = requests.get(
            f"{API_URL}/profile",
            headers=auth_headers(),   # ← TOKEN, not email param
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
        elif r.status_code == 401:
            # Token expired — force re-login
            st.session_state.user = None
            st.session_state.access_token = None
            st.rerun()

    except requests.exceptions.RequestException:
        st.toast("⚠️ Could not load saved profile — fill in your details manually.", icon="⚠️")

    finally:
        st.session_state.profile_loaded = True