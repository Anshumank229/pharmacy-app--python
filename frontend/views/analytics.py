# frontend/views/analytics.py
# ─────────────────────────────────────────
# Admin analytics dashboard.
# Call render() from app.py when show_analytics is True.
# ─────────────────────────────────────────
import streamlit as st
import requests
from config import API_URL, ADMIN_HEADERS
from theme import scroll_to_top


def render():
    scroll_to_top()
    st.markdown('<div class="page-title">Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Sales performance over the last 30 days.</div>', unsafe_allow_html=True)

    try:
        resp = requests.get(f"{API_URL}/admin/analytics", headers=ADMIN_HEADERS, timeout=15)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load analytics: {e}")
        _back_btn()
        return

    if resp.status_code != 200:
        st.error("Unauthorized — check your ADMIN_API_KEY.")
        _back_btn()
        return

    data    = resp.json()
    summary = data["summary"]

    # ── Summary metrics ──
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue",       f"₹{summary['total_revenue']:.0f}")
    c2.metric("Total orders",  summary["total_orders"])
    c3.metric("Delivered",     summary["delivered"])
    c4.metric("Cancelled",     summary["cancelled"])
    c5.metric("Delivery rate", f"{summary['delivery_rate']}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Revenue chart ──
    if data["daily_revenue"]:
        import pandas as pd
        df = pd.DataFrame(data["daily_revenue"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        st.markdown("#### Revenue — last 30 days")
        st.bar_chart(df["revenue"], width='stretch')

        st.markdown("#### Orders per day")
        st.line_chart(df["orders"], width='stretch')
    else:
        st.info("No order data yet for the last 30 days.")

    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Top medicines sold")
        if data["top_medicines"]:
            import pandas as pd
            df_m = pd.DataFrame(data["top_medicines"])
            df_m = df_m.rename(columns={"name": "Medicine", "qty_sold": "Qty", "revenue": "Revenue (₹)"})
            df_m["Revenue (₹)"] = df_m["Revenue (₹)"].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(df_m, width='stretch', hide_index=True)
        else:
            st.info("No sales data yet.")

    with col2:
        st.markdown("#### Orders by pincode")
        if data["by_pincode"]:
            import pandas as pd
            df_p = pd.DataFrame(data["by_pincode"])
            df_p = df_p.rename(columns={"pincode": "Pincode", "orders": "Orders"})
            st.dataframe(df_p, width='stretch', hide_index=True)
        else:
            st.info("No pincode data yet.")

    if data.get("status_breakdown"):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Order status breakdown")
        import pandas as pd
        df_s = pd.DataFrame(list(data["status_breakdown"].items()), columns=["Status", "Count"])
        st.bar_chart(df_s.set_index("Status"), width='stretch')

    st.markdown("<hr>", unsafe_allow_html=True)
    _back_btn()


def _back_btn():
    if st.button("← Back to admin"):
        st.session_state.show_analytics = False
        st.session_state.show_admin     = True
        st.rerun()
