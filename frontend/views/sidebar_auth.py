# frontend/views/sidebar_auth.py
import streamlit as st
import requests
from config import API_URL, ADMIN_EMAIL


def render():
    # Brand header
    st.sidebar.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">💊 MediCare</div>
            <div class="sidebar-brand-sub">Local Pharmacy — Est. 2024</div>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        '<div class="sidebar-section"><span class="sidebar-label">Account</span></div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.user:
        _login_panel()
    else:
        _user_card()


def _login_panel():
    st.sidebar.markdown("""
        <div style="background:rgba(56,189,248,0.04);border:1px solid rgba(56,189,248,0.1);
                    border-radius:12px;padding:10px 13px;margin-bottom:12px;
                    font-size:.8rem;color:#475569;line-height:1.6;">
            Sign in to track orders &amp; checkout faster
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("""
        <a href="http://127.0.0.1:8000/login/google-oauth2/" target="_self"
           style="text-decoration:none;display:block;margin-bottom:12px">
            <div style="width:100%;padding:10px 0;cursor:pointer;border-radius:10px;
                        border:1px solid rgba(255,255,255,0.09);text-align:center;
                        background:rgba(255,255,255,0.03);color:#cbd5e1;font-size:.84rem;
                        font-weight:600;transition:all .2s;letter-spacing:.01em;">
                🔵 &nbsp; Continue with Google
            </div>
        </a>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        '<div style="text-align:center;color:#1e3a5f;font-size:.72rem;margin:2px 0 10px;'
        'display:flex;align-items:center;gap:8px;">'
        '<span style="flex:1;height:1px;background:rgba(255,255,255,0.05)"></span>'
        '<span>or email</span>'
        '<span style="flex:1;height:1px;background:rgba(255,255,255,0.05)"></span>'
        '</div>',
        unsafe_allow_html=True,
    )

    email    = st.sidebar.text_input("Email",    placeholder="you@example.com", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", placeholder="••••••••", key="auth_pass")

    if st.sidebar.button("Continue →", width='stretch', key="auth_go"):
        if not email or not password:
            st.sidebar.warning("Enter email and password.")
        else:
            _do_login(email, password)


def _do_login(email: str, password: str):
    try:
        r = requests.post(
            f"{API_URL}/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            d = r.json()
            st.session_state.user = {
                "name":     d.get("name",     ""),
                "email":    d.get("email",    ""),
                "is_admin": d.get("is_admin", False),
            }
            st.session_state.access_token = d.get("access_token")  # ← ADD THIS LINE
            st.rerun()
        elif r.status_code == 429:
            st.sidebar.error("Too many attempts — wait a minute.")
        else:
            default_name = email.split("@")[0].capitalize()
            reg = requests.post(
                f"{API_URL}/register",
                json={"name": default_name, "email": email, "password": password},
                timeout=10,
            )
            if reg.status_code in (200, 201):
                # Auto-login after register to get the token
                login_r = requests.post(
                    f"{API_URL}/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                if login_r.ok:
                    ld = login_r.json()
                    st.session_state.access_token = ld.get("access_token")  # ← ADD
                st.session_state.user = {"name": default_name, "email": email, "is_admin": False}
                st.sidebar.success("Account created — welcome!")
                st.rerun()
            else:
                st.sidebar.error("Incorrect password. Try again.")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Connection error: {e}")


def _user_card():
    u     = st.session_state.user
    name  = u.get("name",  "User")
    email = u.get("email", "")
    initials = "".join(w[0].upper() for w in name.split()[:2]) or "U"

    st.sidebar.markdown(f"""
        <div class="user-card">
            <div style="display:flex;align-items:center;gap:10px">
                <div style="width:34px;height:34px;border-radius:50%;
                     background:linear-gradient(135deg,#0ea5e9,#0284c7);
                     display:flex;align-items:center;justify-content:center;
                     font-weight:800;font-size:.85rem;color:#fff;flex-shrink:0">
                    {initials}
                </div>
                <div>
                    <div class="user-card-label">Signed in</div>
                    <div class="user-card-name">{name}</div>
                    <div class="user-card-email">{email}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("My profile & orders", width='stretch', key="go_profile"):
        st.session_state.show_profile = True
        st.rerun()

    if email == ADMIN_EMAIL and u.get("is_admin"):
        if st.sidebar.button("Admin dashboard", width='stretch', key="go_admin"):
            st.session_state.show_admin = True
            st.rerun()

    if st.sidebar.button("Logout", width='stretch', key="auth_logout"):
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.pop("profile_loaded", None)
        st.rerun()
