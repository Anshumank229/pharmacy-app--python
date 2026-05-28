# frontend/views/admin.py
# ─────────────────────────────────────────
# Admin order management panel.
# Call render() from app.py when show_admin is True.
# Auto-refreshes every 60 seconds.
# ─────────────────────────────────────────
import time
from datetime import datetime
import streamlit as st
import requests
from config import API_URL, ADMIN_HEADERS
from theme import scroll_to_top


_STATUSES = ["PENDING", "SHIPPED", "DELIVERED", "CANCELLED"]

_STATUS_PILL = {
    "PENDING":   "pill-pending",
    "SHIPPED":   "pill-shipped",
    "DELIVERED": "pill-delivered",
    "CANCELLED": "pill-cancelled",
}
_STATUS_EMOJI = {
    "PENDING":   "🕐",
    "SHIPPED":   "🚚",
    "DELIVERED": "✅",
    "CANCELLED": "❌",
}


def render():
    scroll_to_top()

    st.markdown('<div class="page-title">Admin Panel</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Manage orders, monitor stock, and track batches.</div>',
        unsafe_allow_html=True,
    )

    # ── Top action bar ──
    a1, a2, a3 = st.columns([1, 1, 4])
    with a1:
        if st.button("📊 Analytics", width='stretch'):
            st.session_state.show_admin     = False
            st.session_state.show_analytics = True
            st.rerun()
    with a2:
        if st.button("← Store", width='stretch'):
            st.session_state.show_admin = False
            st.rerun()

    st.divider()

    _batch_alerts()
    _orders_panel()

    st.markdown(
        '<div style="color:#334155;font-size:.75rem;text-align:center;margin-top:1rem">'
        'Auto-refreshing every 60 seconds</div>',
        unsafe_allow_html=True,
    )
    time.sleep(60)
    st.rerun()


# ── Private helpers ───────────────────────────────────────────────────────────

def _batch_alerts():
    try:
        r = requests.get(f"{API_URL}/admin/batches/alerts", headers=ADMIN_HEADERS, timeout=10)
        if not r.ok:
            return
        alerts   = r.json()
        expired  = alerts.get("expired",       [])
        expiring = alerts.get("expiring_soon",  [])

        if expired:
            st.markdown(
                f'<div class="alert-expired">🔴 <b>{len(expired)} expired batch'
                f'{"es" if len(expired) > 1 else ""}</b> — remove from stock immediately</div>',
                unsafe_allow_html=True,
            )
            for b in expired:
                st.caption(
                    f"  {b['medicine']} | Batch {b['batch']} | "
                    f"Qty {b['quantity']} | Expired {b['days_ago']}d ago"
                )

        if expiring:
            st.markdown(
                f'<div class="alert-expiring">🟡 <b>{len(expiring)} batch'
                f'{"es" if len(expiring) > 1 else ""}</b> expiring within 30 days</div>',
                unsafe_allow_html=True,
            )
            for b in expiring:
                st.caption(
                    f"  {b['medicine']} | Batch {b['batch']} | "
                    f"Qty {b['quantity']} | {b['days_left']}d left"
                )
    except requests.exceptions.RequestException:
        pass


def _orders_panel():
    try:
        r = requests.get(f"{API_URL}/admin/orders", headers=ADMIN_HEADERS, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")
        return

    if r.status_code != 200:
        st.error("Unauthorized — check your ADMIN_API_KEY.")
        return

    orders = r.json()

    # ── New order alert ──
    current_pending = sum(1 for o in orders if o["status"] == "PENDING")
    if current_pending > st.session_state.last_pending_count:
        diff = current_pending - st.session_state.last_pending_count
        st.toast(f"🔔 {diff} new order{'s' if diff > 1 else ''} arrived!", icon="🔔")
    st.session_state.last_pending_count = current_pending

    # ── Low stock alert ──
    try:
        from inventory.models import Medicine as Med
        low = Med.objects.filter(stock__lte=5).values("name", "stock")
        if low:
            names = ", ".join(f"{m['name']} ({m['stock']} left)" for m in low)
            st.warning(f"⚠️ Low stock: {names}")
    except Exception:
        pass

    # ── Today's summary metrics ──
    today = datetime.now().date().isoformat()
    todays = [o for o in orders if (o.get("created_at") or "").startswith(today)]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pending today",   sum(1 for o in todays if o["status"] == "PENDING"))
    m2.metric("Shipped today",   sum(1 for o in todays if o["status"] == "SHIPPED"))
    m3.metric("Delivered today", sum(1 for o in todays if o["status"] == "DELIVERED"))
    m4.metric("Total orders",    len(orders))

    st.divider()
    st.markdown("#### All orders")

    if not orders:
        st.info("No orders yet.")
        return

    for order in orders:
        _order_row(order)


def _order_row(order: dict):
    status = order["status"]

    # FIX: extract all values BEFORE building HTML so formatting errors
    # never cause the raw HTML to render as escaped text
    order_id     = order.get("id", "—")
    name         = order.get("customer_name", "—")
    phone        = order.get("customer_phone", "—")
    pincode      = order.get("pincode", "—")
    address      = order.get("delivery_address", "—")
    discount     = order.get("discount_applied", 0)
    coupon       = order.get("coupon_code", "")
    email        = order.get("customer_email", "")
    rx_image     = order.get("prescription_image", "")

    # Safe float conversion — JSON may return string or None
    try:
        total = float(order.get("total_price", 0) or 0)
    except (ValueError, TypeError):
        total = 0.0

    pill_class = _STATUS_PILL.get(status, "pill-pending")
    emoji      = _STATUS_EMOJI.get(status, "📦")

    discount_html = (
        f'&nbsp;·&nbsp; 🎟 <b>{coupon}</b> ({discount}% off)'
        if discount else ""
    )

    # Build HTML with all values pre-formatted — no f-string formatting inside HTML
    total_str = f"₹{total:.2f}"

    with st.container():
        # Card header — pure HTML, no Python formatting inside the string
        st.markdown(f"""
<div class="admin-order-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
    <div style="flex:1;min-width:0">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <span class="admin-order-id">Order #{order_id}</span>
        <span class="{pill_class}">{emoji} {status}</span>
      </div>
      <div class="admin-order-meta">
        👤 {name} &nbsp;·&nbsp; 📞 {phone} &nbsp;·&nbsp; 📮 {pincode}
        &nbsp;·&nbsp; 💰 {total_str}{discount_html}
      </div>
      <div class="admin-order-meta" style="margin-top:4px">
        📍 {address}
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        # Links + status control — using native Streamlit below the card
        link_col, ctrl_col = st.columns([3, 1])

        with link_col:
            links = []
            if rx_image:
                links.append(
                    f"[📄 View prescription](http://127.0.0.1:8000/api/prescriptions/{rx_image})"
                )
            links.append(
                f"[🧾 Download invoice]({API_URL}/orders/{order_id}/invoice?email={email})"
            )
            st.markdown("  &nbsp;&nbsp;  ".join(links))

            # Order items summary
            items = order.get("items", [])
            if items:
                items_text = " · ".join(
                    f"{i['medicine']['name']} ×{i['quantity']}"
                    for i in items
                )
                st.caption(f"📦 {items_text}")

        with ctrl_col:
            new_status = st.selectbox(
                "Status",
                _STATUSES,
                index=_STATUSES.index(status),
                key=f"sel_{order_id}",
                label_visibility="collapsed",
            )
            if st.button("Save", key=f"save_{order_id}", type="primary", width='stretch'):
                try:
                    requests.put(
                        f"{API_URL}/admin/orders/{order_id}",
                        params={"status": new_status},
                        headers=ADMIN_HEADERS,
                        timeout=10,
                    )
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Update failed: {e}")

        st.markdown("<hr style='margin:.6rem 0'>", unsafe_allow_html=True)