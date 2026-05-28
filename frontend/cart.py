# frontend/cart.py
# ─────────────────────────────────────────
# Renders the cart summary + full checkout form in the sidebar.
# Call render() from app.py.
# ─────────────────────────────────────────
import streamlit as st
import requests
from config import API_URL


def render():
    st.sidebar.markdown(
        '<div class="sidebar-section"><span class="sidebar-label">Your cart</span></div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.sidebar.markdown(
            '<div style="color:#334155;font-size:.85rem;padding:6px 0">Cart is empty</div>',
            unsafe_allow_html=True,
        )
        return

    cart_total = sum(i["quantity"] * i["price"] for i in st.session_state.cart)

    # ── Item rows ──
    rows_html = ""
    for item in st.session_state.cart:
        rx = "&nbsp;<span style='color:#c084fc;font-size:.68rem'>Rx</span>" if item.get("requires_rx") else ""
        line = item["quantity"] * item["price"]
        rows_html += f"""
        <div class="cart-row">
            <span>{item['quantity']}× {item['name']}{rx}</span>
            <span style="color:#38bdf8;font-weight:600">₹{line:.2f}</span>
        </div>"""
    rows_html += f"""
    <div class="cart-total-row">
        <span class="cart-total-label">ORDER TOTAL</span>
        <span class="cart-total-value">₹{cart_total:.2f}</span>
    </div>"""
    st.sidebar.markdown(rows_html, unsafe_allow_html=True)

    if st.sidebar.button("🗑 Clear cart", width='stretch', key="clear_cart"):
        st.session_state.cart = []
        st.rerun()

    st.sidebar.markdown("<hr style='margin:.8rem 0'>", unsafe_allow_html=True)
    _checkout_form(cart_total)


# ── Private ───────────────────────────────────────────────────────────────────

def _checkout_form(cart_total: float):
    st.sidebar.markdown(
        '<div class="sidebar-section"><span class="sidebar-label">Checkout</span></div>',
        unsafe_allow_html=True,
    )

    u = st.session_state.user or {}
    name    = st.sidebar.text_input("Full name",       value=u.get("name",    ""), key="co_name")
    email   = st.sidebar.text_input("Email",           value=u.get("email",   ""), key="co_email")
    phone   = st.sidebar.text_input("Phone",           value=u.get("phone",   ""), placeholder="98XXXXXXXX", key="co_phone")
    address = st.sidebar.text_area("Delivery address", value=u.get("address", ""), placeholder="House no, street, landmark…", key="co_addr", height=80)
    pincode = st.sidebar.text_input("Pincode",         value=u.get("pincode", ""), placeholder="6-digit pincode", max_chars=10, key="co_pin")

    # ── Pincode check ──
    pincode_ok = False
    if pincode:
        if len(pincode) == 6 and pincode.isdigit():
            try:
                pc = requests.get(f"{API_URL}/check-pincode", params={"pincode": pincode}, timeout=5)
                if pc.ok:
                    res = pc.json()
                    if res["serviceable"]:
                        pincode_ok = True
                        st.session_state.last_area_name = res["area_name"]
                        st.sidebar.markdown(
                            f'<div style="color:#4ade80;font-size:.8rem;margin:2px 0 6px">✓ Delivering to {res["area_name"]}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.sidebar.markdown(
                            '<div style="color:#f87171;font-size:.8rem;margin:2px 0 6px">✗ Pincode not serviceable yet</div>',
                            unsafe_allow_html=True,
                        )
            except requests.exceptions.RequestException:
                st.sidebar.warning("Could not verify pincode.")
        else:
            st.sidebar.markdown(
                '<div style="color:#fbbf24;font-size:.8rem;margin:2px 0 6px">Enter a valid 6-digit pincode</div>',
                unsafe_allow_html=True,
            )

    # ── Coupon ──
    coupon          = st.sidebar.text_input("Coupon code (optional)", key="co_coupon")
    discount_pct    = 0
    if coupon:
        try:
            cr = requests.get(f"{API_URL}/coupons/validate", params={"code": coupon}, timeout=5)
            if cr.ok:
                d = cr.json()
                if d["valid"]:
                    discount_pct = d["discount"]
                    new_total    = cart_total * (1 - discount_pct / 100)
                    st.sidebar.markdown(
                        f'<div style="color:#4ade80;font-size:.8rem;margin:2px 0 6px">🎉 {discount_pct}% off → ₹{new_total:.2f}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.sidebar.markdown(
                        '<div style="color:#f87171;font-size:.8rem;margin:2px 0 6px">Invalid or expired coupon</div>',
                        unsafe_allow_html=True,
                    )
        except requests.exceptions.RequestException:
            st.sidebar.warning("Could not validate coupon.")

    # ── Prescription ──
    needs_rx      = any(i.get("requires_rx") for i in st.session_state.cart)
    uploaded_file = None
    if needs_rx:
        st.sidebar.markdown(
            '<div style="color:#c084fc;font-size:.8rem;padding:6px 0">⚕ Prescription required for one or more items</div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.sidebar.file_uploader("Upload prescription", type=["jpg", "jpeg", "png", "pdf"], key="co_rx")

    st.sidebar.markdown(
        '<div style="color:#475569;font-size:.78rem;margin:8px 0 4px">🚚 Cash on delivery · Delivered within 24 hrs</div>',
        unsafe_allow_html=True,
    )

    if not pincode_ok:
        st.sidebar.markdown(
            '<div style="color:#334155;font-size:.76rem;margin-bottom:6px">Enter a valid serviceable pincode to place order</div>',
            unsafe_allow_html=True,
        )

    if st.sidebar.button(
        "✓ Place order", type="primary",
        disabled=not pincode_ok, width='stretch', key="co_confirm",
    ):
        _place_order(name, email, phone, address, pincode, coupon, discount_pct, needs_rx, uploaded_file)


def _place_order(name, email, phone, address, pincode, coupon, discount_pct, needs_rx, uploaded_file):
    errors = []
    if not phone:   errors.append("Phone number is required.")
    if not address: errors.append("Delivery address is required.")
    if needs_rx and not uploaded_file: errors.append("Please upload a prescription.")
    for e in errors:
        st.sidebar.error(e)
    if errors:
        return

    try:
        rx_filename = None
        if uploaded_file:
            up = requests.post(
                f"{API_URL}/upload-prescription",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                timeout=15,
            )
            if up.status_code == 200:
                rx_filename = up.json()["filename"]
            else:
                st.sidebar.error("Prescription upload failed.")
                return

        resp = requests.post(
            f"{API_URL}/orders",
            json={
                "customer_name":      name,
                "customer_email":     email,
                "customer_phone":     phone,
                "delivery_address":   address,
                "pincode":            pincode,
                "prescription_image": rx_filename,
                "coupon_code":        coupon or None,
                "items": [
                    {"medicine_id": i["medicine_id"], "quantity": i["quantity"]}
                    for i in st.session_state.cart
                ],
            },
            timeout=10,
        )

        if resp.status_code == 200:
            order = resp.json()
            disc  = f" ({order['discount_applied']}% off)" if order.get("discount_applied") else ""
            st.sidebar.success(
                f"✅ Order #{order['id']} placed! ₹{order['total_price']:.2f}{disc}\n"
                f"We'll call {phone} before arrival."
            )
            # Save profile silently
            if st.session_state.user:
                try:
                    requests.put(
                        f"{API_URL}/profile",
                        json={
                            "email": email, "name": name, "phone": phone,
                            "address": address, "pincode": pincode,
                            "area_name": st.session_state.get("last_area_name", ""),
                        },
                        timeout=5,
                    )
                    st.session_state.user.update({"name": name, "phone": phone, "address": address, "pincode": pincode})
                except requests.exceptions.RequestException:
                    pass
            st.session_state.cart = []
            st.rerun()
        else:
            st.sidebar.error(resp.json().get("detail", "Order failed. Please try again."))

    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Checkout failed: {e}")
