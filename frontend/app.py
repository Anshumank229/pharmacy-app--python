# frontend/app.py
# ─────────────────────────────────────────
# Entry point — run with:  streamlit run app.py
#
# This file is intentionally thin.
# All logic lives in views/ and helpers.
# ─────────────────────────────────────────
import streamlit as st

# ── Must be first Streamlit call ──────────
st.set_page_config(
    page_title="MediCare — Local Pharmacy",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── App modules ───────────────────────────
import auth
import cart
import theme
from views import sidebar_auth
from views import store
from views import medicine_detail
from views import profile
from views import analytics
from views import admin


def main():
    # 1. Session state defaults
    auth.init_session_state()

    # 2. Catch Google OAuth redirect (?email=&name=)
    auth.handle_google_redirect()

    # 3. Load saved profile once per session
    auth.load_profile_once()

    # 4. Inject global CSS
    theme.inject_css()

    # 5. Sidebar — always visible
    sidebar_auth.render()
    cart.render()

    # 6. Page routing — first match wins, each view calls st.stop()
    if st.session_state.show_medicine_detail and st.session_state.selected_medicine_id:
        medicine_detail.render()
        st.stop()

    if st.session_state.show_profile and st.session_state.user:
        profile.render()
        st.stop()

    if st.session_state.show_analytics:
        analytics.render()
        st.stop()

    if st.session_state.show_admin:
        admin.render()
        st.stop()

    # 7. Default — storefront
    store.render()


if __name__ == "__main__":
    main()
