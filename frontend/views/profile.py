import requests
import streamlit as st
from helpers import delivery_estimate, reorder


def render_profile(api_url: str):
    """
    Full-page profile view.
    Shows editable delivery details and complete order history.
    Calls st.stop() so nothing else renders behind it.
    """
    if not st.session_state.user:
        st.stop()

    st.title("Your Profile & Orders")

    _render_profile_form(api_url)

    st.divider()

    _render_order_history(api_url)

    st.divider()
    if st.button("Back to store"):
        st.session_state.show_profile = False
        st.rerun()

    st.stop()


# ==========================================
# PROFILE FORM
# ==========================================
def _render_profile_form(api_url: str):
    st.subheader("Saved delivery details")
    u = st.session_state.user or {}

    new_name    = st.text_input("Name",    value=u.get('name', ''))
    new_phone   = st.text_input("Phone",   value=u.get('phone', ''))
    new_address = st.text_area("Address",  value=u.get('address', ''))
    new_pincode = st.text_input("Pincode", value=u.get('pincode', ''))

    if st.button("Save details"):
        try:
            requests.put(
                f"{api_url}/profile",
                json={
                    "email":     u['email'],
                    "name":      new_name,
                    "phone":     new_phone,
                    "address":   new_address,
                    "pincode":   new_pincode,
                    "area_name": u.get('area_name', ''),
                },
                timeout=5,
            )
            st.session_state.user.update({
                "name":    new_name,
                "phone":   new_phone,
                "address": new_address,
                "pincode": new_pincode,
            })
            if 'profile_loaded' in st.session_state:
                del st.session_state.profile_loaded
            st.success("Details saved!")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not save: {e}")


# ==========================================
# ORDER HISTORY
# ==========================================
def _render_order_history(api_url: str):
    st.subheader("Your order history")
    u = st.session_state.user or {}

    try:
        orders_resp = requests.get(
            f"{api_url}/my-orders",
            params={"email": u['email']},
            timeout=10,
        )
        if orders_resp.status_code != 200:
            st.error("Could not load orders.")
            return

        orders = orders_resp.json()
        if not orders:
            st.info("You haven't placed any orders yet.")
            return

        for order in orders:
            _render_order_card(api_url, order, u)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not load orders: {e}")


STATUS_EMOJI = {
    'PENDING':   '🕐',
    'SHIPPED':   '🚚',
    'DELIVERED': '✅',
    'CANCELLED': '❌',
}


def _render_order_card(api_url: str, order: dict, u: dict):
    status       = order['status']
    status_emoji = STATUS_EMOJI.get(status, '📦')

    with st.expander(f"Order #{order['id']} — {status_emoji} {status}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📍 **Address:** {order.get('delivery_address', '—')}")
            st.write(f"📮 **Pincode:** {order.get('pincode', '—')}")
        with col2:
            st.write(f"📞 **Phone:** {order.get('customer_phone', '—')}")
            total    = order.get('total_price', 0)
            discount = order.get('discount_applied', 0)
            if discount:
                st.write(f"💰 **Total:** ₹{total:.2f} *(saved {discount}%)*")
            else:
                st.write(f"💰 **Total:** ₹{total:.2f}")

        if status in ('PENDING', 'SHIPPED') and order.get('created_at'):
            st.info(f"🚚 {delivery_estimate(order['created_at'])}")

        if order.get('prescription_image'):
            st.info("📄 Prescription attached to this order.")

        st.write("**Items ordered:**")
        for item in order['items']:
            st.write(
                f"- {item['medicine']['name']} × {item['quantity']} "
                f"(₹{item['price_at_time_of_purchase']} each)"
            )

        action_cols = st.columns(3)

        with action_cols[0]:
            invoice_url = f"{api_url}/orders/{order['id']}/invoice?email={u['email']}"
            st.markdown(f"[📄 Invoice PDF]({invoice_url})")

        with action_cols[1]:
            if st.button(
                "🔄 Reorder",
                key=f"reorder_{order['id']}",
                use_container_width=True,
                help="Add all items from this order to your cart",
            ):
                with st.spinner("Checking stock and adding to cart…"):
                    added, skipped = reorder(order, api_url)
                if added:
                    st.success(f"Added to cart: {', '.join(added)}")
                if skipped:
                    st.warning(f"Skipped (unavailable): {', '.join(skipped)}")
                if added:
                    st.info("👈 Review your cart in the sidebar and checkout when ready.")

        with action_cols[2]:
            if status == 'PENDING':
                if st.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    _cancel_order(api_url, order['id'], u['email'])


def _cancel_order(api_url: str, order_id: int, email: str):
    try:
        r = requests.put(
            f"{api_url}/orders/{order_id}/cancel",
            params={"email": email},
            timeout=10,
        )
        if r.status_code == 200:
            st.success("Order cancelled.")
            st.rerun()
        else:
            st.error(r.json().get('detail', 'Could not cancel.'))
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
