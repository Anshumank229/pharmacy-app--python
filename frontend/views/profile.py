# frontend/views/profile.py
# ─────────────────────────────────────────
# User profile editor + full order history.
# Call render() from app.py when show_profile is True.
# ─────────────────────────────────────────
import streamlit as st
import requests
from config import API_URL
from helpers import delivery_estimate
from theme import scroll_to_top
from auth import auth_headers


_STATUS_PILL = {
    "PENDING":   "pill-pending",
    "SHIPPED":   "pill-shipped",
    "DELIVERED": "pill-delivered",
    "CANCELLED": "pill-cancelled",
}
_STATUS_EMOJI = {
    "PENDING": "🕐", "SHIPPED": "🚚", "DELIVERED": "✅", "CANCELLED": "❌",
}


def render():
    scroll_to_top()

    u = st.session_state.user or {}

    st.markdown('<div class="page-title">My Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Manage your saved details and view order history.</div>', unsafe_allow_html=True)

    # ── Saved details card ──
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("##### Delivery details")

    c1, c2 = st.columns(2)
    with c1:
        new_name    = st.text_input("Full name", value=u.get("name",    ""), key="prof_name")
        new_phone   = st.text_input("Phone",     value=u.get("phone",   ""), key="prof_phone")
    with c2:
        new_pincode = st.text_input("Pincode",   value=u.get("pincode", ""), key="prof_pin")
    new_address = st.text_area("Delivery address", value=u.get("address", ""), key="prof_addr", height=80)

    if st.button("Save details", type="primary"):
        try:
            requests.put(
                f"{API_URL}/profile",
                json={
                    "email": u["email"],
                    "name": new_name,
                    "phone": new_phone,
                    "address": new_address,
                    "pincode": new_pincode,
                    "area_name": u.get("area_name", ""),
                },
                headers=auth_headers(),
                timeout=5,
            )
            st.session_state.user.update({
                "name": new_name, "phone": new_phone,
                "address": new_address, "pincode": new_pincode,
            })
            st.session_state.pop("profile_loaded", None)
            st.success("Details saved!")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not save: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Order history ──
    st.markdown("### Order history")

    try:
        r = requests.get(f"{API_URL}/my-orders", headers=auth_headers(), timeout=10)
        orders = r.json() if r.ok else []
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load orders: {e}")
        orders = []

    if not orders:
        st.info("You haven't placed any orders yet.")
    else:
        for order in orders:
            _order_card(order, u)

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("← Back to store"):
        st.session_state.show_profile = False
        st.rerun()


# ── Private helpers ───────────────────────────────────────────────────────────

def _order_card(order: dict, u: dict):
    status     = order["status"]
    pill_class = _STATUS_PILL.get(status, "pill-pending")
    emoji      = _STATUS_EMOJI.get(status, "📦")
    date_str   = ""
    if order.get("created_at"):
        try:
            from datetime import datetime
            date_str = datetime.fromisoformat(order["created_at"]).strftime("%d %b %Y, %I:%M %p")
        except Exception:
            date_str = order["created_at"][:10]

    disc_html = ""
    if order.get("discount_applied"):
        disc_html = f'<span style="color:#4ade80;font-size:.78rem"> &nbsp;{order["discount_applied"]}% off</span>'

    st.markdown(f"""
    <div class="order-card">
        <div class="order-header">
            <div>
                <div class="order-id">Order #{order['id']} &nbsp;<span class="{pill_class}">{emoji} {status}</span></div>
                <div class="order-date">{date_str}</div>
            </div>
            <div class="order-total">₹{order.get('total_price',0):.2f}{disc_html}</div>
        </div>
        <div style="font-size:.8rem;color:#475569;margin-bottom:.5rem">
            📍 {order.get('delivery_address','—')}, {order.get('pincode','—')} &nbsp;·&nbsp;
            📞 {order.get('customer_phone','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"View items — Order #{order['id']}"):
        for item in order.get("items", []):
            st.markdown(f"""
            <div class="order-item-row">
                <span>{item['medicine']['name']} × {item['quantity']}</span>
                <span>₹{float(item['price_at_time_of_purchase']) * item['quantity']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)

        if status in ("PENDING", "SHIPPED") and order.get("created_at"):
            st.info(f"🚚 {delivery_estimate(order['created_at'])}")

        if order.get("prescription_image"):
            st.caption("📄 Prescription attached to this order.")

        # Actions row
        a1, a2 = st.columns(2)
        with a1:
            if st.button("📄 Download invoice", key=f"inv_{order['id']}"):
                try:
                    inv_r = requests.get(
                        f"{API_URL}/orders/{order['id']}/invoice",
                        headers=auth_headers(),
                        timeout=15,
                    )
                    if inv_r.ok:
                        st.download_button(
                            label="⬇️ Save PDF",
                            data=inv_r.content,
                            file_name=f"invoice_{order['id']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{order['id']}",
                        )
                    else:
                        st.error("Could not fetch invoice.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error: {e}")
        with a2:
            if status == "PENDING":
                if st.button("Cancel order", key=f"cancel_{order['id']}"):
                    try:
                        cr = requests.put(
                            f"{API_URL}/orders/{order['id']}/cancel",
                            headers=auth_headers(),  # ← token, no email param
                            timeout=10,
                        )
                        if cr.status_code == 200:
                            st.success("Order cancelled.")
                            st.rerun()
                        else:
                            st.error(cr.json().get("detail", "Could not cancel."))
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error: {e}")
