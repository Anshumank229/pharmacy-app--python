import requests
import streamlit as st


def resolve_google_token(api_url: str):
    query_params = st.query_params
    if "token" not in query_params or st.session_state.user:
        return
    token = query_params["token"]
    try:
        resp = requests.get(f"{api_url}/resolve-token", params={"token": token}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            try:
                role_resp = requests.get(f"{api_url}/me", params={"email": data["email"]}, timeout=5)
                is_admin = role_resp.json().get("is_admin", False) if role_resp.ok else False
            except requests.exceptions.RequestException:
                is_admin = False
            st.session_state.user = {"name": data["name"], "email": data["email"], "is_admin": is_admin}
        else:
            st.warning("Your login link has expired. Please log in again.")
    except requests.exceptions.RequestException:
        st.warning("Could not verify login. Please try again.")
    st.query_params.clear()


def load_profile_once(api_url: str):
    if not st.session_state.user or 'profile_loaded' in st.session_state:
        return
    try:
        r = requests.get(f"{api_url}/profile", params={"email": st.session_state.user['email']}, timeout=5)
        if r.status_code == 200:
            p = r.json()
            st.session_state.user.update({
                'phone': p.get('phone', ''), 'address': p.get('address', ''),
                'pincode': p.get('pincode', ''), 'area_name': p.get('area_name', ''),
            })
    except requests.exceptions.RequestException:
        pass
    st.session_state.profile_loaded = True


def render_auth_sidebar(api_url: str):
    # Section label
    st.sidebar.markdown(
        '<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.75rem;">'
        'Account</p>',
        unsafe_allow_html=True,
    )

    if not st.session_state.user:
        _render_logged_out(api_url)
    else:
        _render_logged_in()


def _render_logged_out(api_url: str):
    backend_base = api_url.replace('/api', '')

    # Google button
    st.sidebar.markdown(f"""
    <a href="{backend_base}/login/google-oauth2/" target="_self" style="text-decoration:none;">
        <div style="
            display:flex;align-items:center;justify-content:center;gap:0.5rem;
            background:rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.12);
            border-radius:8px;padding:0.6rem 1rem;
            font-size:0.875rem;font-weight:500;color:#f0f4ff;
            transition:background 0.2s;cursor:pointer;margin-bottom:1rem;">
            <svg width="16" height="16" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
        </div>
    </a>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        '<p style="text-align:center;font-size:0.75rem;color:var(--text-muted);margin:0.5rem 0;">or</p>',
        unsafe_allow_html=True,
    )

    email    = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")

    tab_login, tab_register = st.sidebar.tabs(["Log in", "Sign up"])

    with tab_login:
        if st.button("Log in", use_container_width=True, key="btn_login"):
            _handle_login(api_url, email, password)

    with tab_register:
        if st.button("Create account", use_container_width=True, key="btn_register"):
            _handle_register(api_url, email, password)


def _handle_login(api_url, email, password):
    if not email or not password:
        st.sidebar.warning("Please enter both fields.")
        return
    try:
        resp = requests.post(f"{api_url}/login", json={"email": email, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.user = {
                "name": data.get("name", ""), "email": data.get("email", ""),
                "is_admin": data.get("is_admin", False),
            }
            st.rerun()
        elif resp.status_code == 429:
            st.sidebar.error("Too many attempts. Wait a minute.")
        else:
            st.sidebar.error("Incorrect email or password.")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Connection error: {e}")


def _handle_register(api_url, email, password):
    if not email or not password:
        st.sidebar.warning("Please enter both fields.")
        return
    if len(password) < 8:
        st.sidebar.warning("Password must be at least 8 characters.")
        return
    default_name = email.split('@')[0].capitalize()
    try:
        resp = requests.post(f"{api_url}/register",
                             json={"name": default_name, "email": email, "password": password}, timeout=10)
        if resp.status_code in [200, 201]:
            st.session_state.user = {"name": default_name, "email": email, "is_admin": False}
            st.sidebar.success("Welcome aboard!")
            st.rerun()
        elif resp.status_code == 400:
            st.sidebar.error("Email already registered. Try logging in.")
        else:
            st.sidebar.error("Registration failed. Please try again.")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Connection error: {e}")


def _render_logged_in():
    u = st.session_state.user
    # User badge
    st.sidebar.markdown(f"""
    <div style="
        background:rgba(59,130,246,0.08);
        border:1px solid rgba(59,130,246,0.15);
        border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.75rem;">
        <p style="margin:0;font-size:0.75rem;color:var(--text-muted);">Signed in as</p>
        <p style="margin:0;font-weight:600;font-size:0.9rem;color:var(--text-primary);">{u.get('name','User')}</p>
        <p style="margin:0;font-size:0.75rem;color:var(--text-secondary);">{u.get('email','')}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("My profile & orders", use_container_width=True):
        st.session_state.show_profile = True
        st.rerun()

    if u.get('is_admin'):
        if st.sidebar.button("Admin dashboard", use_container_width=True):
            st.session_state.show_admin = True
            st.rerun()

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        if 'profile_loaded' in st.session_state:
            del st.session_state.profile_loaded
        st.rerun()
