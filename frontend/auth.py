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
        "cart":                 [],   # list of dicts: {id, name, price, quantity, requires_rx}
        "user":                 None,
        "last_area_name":       "",
        "last_pending_count":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def handle_google_redirect():
    """
    Called after Google OAuth redirect.
    Exchanges the signed ?token= param via the backend — never trusts
    raw email/name from the URL, preventing spoofed logins.
    """
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

    # Fetch admin status from backend
    try:
        me = requests.get(f"{API_URL}/me", params={"email": email}, timeout=5)
        is_admin = me.json().get("is_admin", False) if me.ok else False
    except requests.exceptions.RequestException:
        is_admin = False

    st.session_state.user = {"name": name, "email": email, "is_admin": is_admin}


def load_profile_once():
    """
    Fetches saved delivery details once per session and merges them into
    session_state.user so checkout fields are pre-filled.

    Uses finally to guarantee profile_loaded is always set — even on network
    failure — so a flaky backend doesn't cause infinite retries on every rerun.
    """
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
        # 404 = new user with no saved profile, that's fine

    except requests.exceptions.RequestException:
        st.toast(
            "⚠️ Could not load saved profile — fill in your details manually.",
            icon="⚠️",
        )

    finally:
        st.session_state.profile_loaded = True