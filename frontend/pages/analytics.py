import requests
import streamlit as st
from config import ADMIN_HEADERS


def render_analytics(api_url: str):
    """
    Full-page analytics dashboard.
    Shows summary KPIs, daily revenue/orders charts,
    top medicines, pincode distribution, and status breakdown.
    Calls st.stop() so nothing else renders behind it.
    """
    st.title("Analytics")

    try:
        resp = requests.get(f"{api_url}/admin/analytics", headers=ADMIN_HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            _render_summary_kpis(data['summary'])
            st.divider()
            _render_time_series(data)
            st.divider()
            _render_tables(data)
            st.divider()
            _render_status_breakdown(data)
        else:
            st.error("Unauthorized.")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load analytics: {e}")

    _render_back_buttons()
    st.stop()


# ==========================================
# KPI ROW
# ==========================================
def _render_summary_kpis(summary: dict):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue",  f"₹{summary['total_revenue']:.0f}")
    c2.metric("Total Orders",    summary['total_orders'])
    c3.metric("Delivered",       summary['delivered'])
    c4.metric("Cancelled",       summary['cancelled'])
    c5.metric("Delivery Rate",  f"{summary['delivery_rate']}%")


# ==========================================
# CHARTS
# ==========================================
def _render_time_series(data: dict):
    if not data['daily_revenue']:
        st.info("No order data yet for the last 30 days.")
        return

    import pandas as pd

    df = pd.DataFrame(data['daily_revenue'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')

    st.subheader("Revenue — last 30 days")
    st.bar_chart(df['revenue'])

    st.subheader("Orders per day — last 30 days")
    st.line_chart(df['orders'])


# ==========================================
# TABLES
# ==========================================
def _render_tables(data: dict):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top medicines sold")
        if data['top_medicines']:
            import pandas as pd
            df = pd.DataFrame(data['top_medicines'])
            df = df.rename(columns={
                'name':    'Medicine',
                'qty_sold': 'Qty Sold',
                'revenue': 'Revenue (₹)',
            })
            df['Revenue (₹)'] = df['Revenue (₹)'].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sales data yet.")

    with col2:
        st.subheader("Orders by pincode")
        if data['by_pincode']:
            import pandas as pd
            df = pd.DataFrame(data['by_pincode'])
            df = df.rename(columns={'pincode': 'Pincode', 'orders': 'Orders'})
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No pincode data yet.")


# ==========================================
# STATUS BREAKDOWN
# ==========================================
def _render_status_breakdown(data: dict):
    st.subheader("Order status breakdown")
    if data['status_breakdown']:
        import pandas as pd
        df = pd.DataFrame(
            list(data['status_breakdown'].items()),
            columns=['Status', 'Count'],
        )
        st.bar_chart(df.set_index('Status'))


# ==========================================
# NAVIGATION
# ==========================================
def _render_back_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to admin panel", use_container_width=True):
            st.session_state.show_analytics = False
            st.session_state.show_admin     = True
            st.rerun()
    with col2:
        if st.button("← Back to store", use_container_width=True):
            st.session_state.show_analytics = False
            st.rerun()
