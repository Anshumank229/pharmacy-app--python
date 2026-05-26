import time
import requests
import streamlit as st
from datetime import datetime
from config import ADMIN_HEADERS


def render_admin(api_url: str):
    """
    Full-page admin dashboard.
    - Guards against non-admin access
    - Shows batch expiry alerts
    - Shows today's order KPIs
    - Lists all orders with status update controls
    - Auto-refreshes every 60 seconds
    Calls st.stop() so nothing else renders behind it.
    """
    # Guard — only staff users allowed
    if not st.session_state.user or not st.session_state.user.get('is_admin'):
        st.error("Unauthorized.")
        st.stop()

    st.title("Admin control panel")

    _render_top_buttons()
    _render_batch_alerts(api_url)
    _render_order_dashboard(api_url)
    _render_footer(api_url)

    st.stop()


# ==========================================
# TOP ACTION BUTTONS
# ==========================================
def _render_top_buttons():
    btn_cols = st.columns(3)
    with btn_cols[0]:
        if st.button("📊 View analytics", use_container_width=True):
            st.session_state.show_admin     = False
            st.session_state.show_analytics = True
            st.rerun()


# ==========================================
# BATCH EXPIRY ALERTS
# ==========================================
def _render_batch_alerts(api_url: str):
    try:
        batch_resp = requests.get(f"{api_url}/admin/batches/alerts", headers=ADMIN_HEADERS, timeout=10)
        if batch_resp.status_code != 200:
            return

        alerts   = batch_resp.json()
        expired  = alerts.get('expired', [])
        expiring = alerts.get('expiring_soon', [])

        if expired:
            st.error(f"🔴 {len(expired)} expired batch(es) — remove from stock immediately!")
            for b in expired:
                st.caption(
                    f"  {b['medicine']} | Batch {b['batch']} | "
                    f"Qty: {b['quantity']} | Expired {b['days_ago']} days ago"
                )

        if expiring:
            st.warning(f"🟡 {len(expiring)} batch(es) expiring within 30 days")
            for b in expiring:
                st.caption(
                    f"  {b['medicine']} | Batch {b['batch']} | "
                    f"Qty: {b['quantity']} | {b['days_left']} days left"
                )

    except requests.exceptions.RequestException:
        pass


# ==========================================
# ORDER DASHBOARD
# ==========================================
def _render_order_dashboard(api_url: str):
    try:
        orders_resp = requests.get(f"{api_url}/admin/orders", headers=ADMIN_HEADERS, timeout=10)
        if orders_resp.status_code != 200:
            st.error("Unauthorized — check your ADMIN_API_KEY.")
            return

        all_orders = orders_resp.json()

        _render_new_order_alert(all_orders)
        _render_today_kpis(all_orders)
        _render_low_stock_warning()

        st.divider()
        st.subheader("All orders")

        for order in all_orders:
            _render_order_row(api_url, order)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")


def _render_new_order_alert(all_orders: list):
    current_pending = sum(1 for o in all_orders if o['status'] == 'PENDING')
    if current_pending > st.session_state.last_pending_count:
        new_count = current_pending - st.session_state.last_pending_count
        st.error(f"🔔 {new_count} new order(s) arrived!")
    st.session_state.last_pending_count = current_pending


def _render_today_kpis(all_orders: list):
    today_str       = datetime.now().date().isoformat()
    todays          = [o for o in all_orders if (o.get('created_at') or '').startswith(today_str)]
    pending_today   = sum(1 for o in todays if o['status'] == 'PENDING')
    shipped_today   = sum(1 for o in todays if o['status'] == 'SHIPPED')
    delivered_today = sum(1 for o in todays if o['status'] == 'DELIVERED')

    cols = st.columns(4)
    cols[0].metric("Pending today",   pending_today)
    cols[1].metric("Shipped today",   shipped_today)
    cols[2].metric("Delivered today", delivered_today)
    cols[3].metric("Total orders",    len(all_orders))


def _render_low_stock_warning():
    """Try to warn about low-stock medicines (best-effort — only works in same process)."""
    try:
        from inventory.models import Medicine as Med
        low = Med.objects.filter(stock__lte=5).values('name', 'stock')
        if low:
            names = ", ".join(f"{m['name']} ({m['stock']} left)" for m in low)
            st.warning(f"⚠️ Low stock: {names}")
    except Exception:
        pass


# ==========================================
# SINGLE ORDER ROW
# ==========================================
def _render_order_row(api_url: str, order: dict):
    with st.container():
        c1, c2 = st.columns([3, 1])

        with c1:
            st.write(
                f"**Order #{order['id']}** | {order['customer_name']} | "
                f"📞 {order.get('customer_phone', '—')} | "
                f"📮 {order.get('pincode', '—')} | "
                f"💰 ₹{order.get('total_price', 0):.2f}"
            )
            if order.get('discount_applied'):
                st.caption(f"Coupon: {order.get('coupon_code')} — {order['discount_applied']}% off")
            st.write(f"📍 {order.get('delivery_address', '—')}")

            base_url = api_url.replace('/api', '')
            if order.get('prescription_image'):
                st.markdown(
                    f"[📄 View prescription]({base_url}/api/prescriptions/{order['prescription_image']})"
                )
            st.markdown(
                f"[🧾 Download invoice]({api_url}/orders/{order['id']}/invoice"
                f"?email={order['customer_email']})"
            )

        with c2:
            st.write(f"Status: **{order['status']}**")
            statuses    = ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
            new_status  = st.selectbox(
                "Update",
                statuses,
                key=f"sel_{order['id']}",
                index=statuses.index(order['status']),
            )
            if st.button("Save", key=f"btn_{order['id']}"):
                _update_order_status(api_url, order['id'], new_status)

        st.divider()


def _update_order_status(api_url: str, order_id: int, new_status: str):
    try:
        requests.put(
            f"{api_url}/admin/orders/{order_id}",
            params={"status": new_status},
            headers=ADMIN_HEADERS,
            timeout=10,
        )
        st.rerun()
    except requests.exceptions.RequestException as e:
        st.error(f"Update failed: {e}")


# ==========================================
# FOOTER + AUTO-REFRESH
# ==========================================
def _render_footer(api_url: str):
    if st.button("Back to store"):
        st.session_state.show_admin = False
        st.rerun()

    st.caption("Auto-refreshing every 60 seconds…")
    time.sleep(60)
    st.rerun()
