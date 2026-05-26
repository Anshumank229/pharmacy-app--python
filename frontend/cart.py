import requests
import streamlit as st


def render_cart_sidebar(api_url: str, whatsapp_number: str):
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.75rem;">'
        'Your Cart</p>',
        unsafe_allow_html=True,
    )

    if not st.session_state.cart:
        st.sidebar.markdown(
            '<p style="color:var(--text-muted);font-size:0.85rem;'
            'text-align:center;padding:1rem 0;">Cart is empty</p>',
            unsafe_allow_html=True,
        )
        return

    _render_cart_items()
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    _render_checkout_form(api_url)


def _render_cart_items():
    cart_total = sum(i['quantity'] * i['price'] for i in st.session_state.cart)

    for item in st.session_state.cart:
        rx = " <span style='font-size:0.7rem;color:#c4b5fd;'>Rx</span>" if item.get('requires_rx') else ""
        st.sidebar.markdown(
            f'<div class="cart-row">'
            f'<span class="cart-name">{item["quantity"]}× {item["name"]}{rx}</span>'
            f'<span class="cart-price">₹{item["quantity"] * item["price"]:.2f}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.75rem 0 0.5rem;font-weight:700;">'
        f'<span style="color:var(--text-primary);">Total</span>'
        f'<span style="color:var(--accent-light);font-family:var(--font-mono);font-size:1.05rem;">'
        f'₹{cart_total:.2f}</span></div>',
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Clear cart", use_container_width=True):
        st.session_state.cart = []
        st.rerun()


def _render_checkout_form(api_url: str):
    st.sidebar.markdown(
        '<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--text-muted);margin-bottom:0.75rem;">'
        'Checkout</p>',
        unsafe_allow_html=True,
    )

    u = st.session_state.user or {}
    customer_name    = st.sidebar.text_input("Full name",       value=u.get('name', ''))
    customer_email   = st.sidebar.text_input("Email",           value=u.get('email', ''))
    customer_phone   = st.sidebar.text_input("Phone",           value=u.get('phone', ''), placeholder="98XXXXXXXX")
    customer_address = st.sidebar.text_area("Delivery address", value=u.get('address', ''),
                                             placeholder="House no, street, landmark...")
    pincode          = st.sidebar.text_input("Pincode",         value=u.get('pincode', ''),
                                              placeholder="6-digit pincode", max_chars=10)

    pincode_ok, area_name = _validate_pincode(api_url, pincode)
    coupon_code, discount_percent = _validate_coupon(api_url)
    uploaded_file = _handle_prescription_upload()

    st.sidebar.markdown(
        '<div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.15);'
        'border-radius:8px;padding:0.6rem 0.9rem;font-size:0.8rem;color:#6ee7b7;margin:0.75rem 0;">'
        '🚚 Delivered in 24 hrs &nbsp;·&nbsp; Cash on delivery</div>',
        unsafe_allow_html=True,
    )

    if not pincode_ok:
        st.sidebar.markdown(
            '<p style="font-size:0.75rem;color:var(--text-muted);text-align:center;">'
            'Enter a serviceable pincode to unlock checkout</p>',
            unsafe_allow_html=True,
        )

    if st.sidebar.button("Confirm order", type="primary", disabled=not pincode_ok, use_container_width=True):
        _submit_order(api_url, customer_name, customer_email, customer_phone,
                      customer_address, pincode, coupon_code, discount_percent,
                      uploaded_file, area_name)


def _validate_pincode(api_url, pincode):
    if not pincode:
        return False, None
    if not (len(pincode) == 6 and pincode.isdigit()):
        st.sidebar.warning("Enter a valid 6-digit pincode.")
        return False, None
    try:
        pc = requests.get(f"{api_url}/check-pincode", params={"pincode": pincode}, timeout=5)
        if pc.status_code == 200:
            res = pc.json()
            if res["serviceable"]:
                area_name = res["area_name"]
                st.session_state.last_area_name = area_name
                st.sidebar.success(f"✅ We deliver to {area_name}!")
                return True, area_name
            else:
                st.sidebar.error("Sorry, we don't deliver to this pincode yet.")
    except requests.exceptions.RequestException:
        st.sidebar.warning("Could not verify pincode. Try again.")
    return False, None


def _validate_coupon(api_url):
    coupon_code      = st.sidebar.text_input("Coupon code (optional)", max_chars=20)
    discount_percent = 0
    if not coupon_code:
        return coupon_code, discount_percent
    cart_total = sum(i['quantity'] * i['price'] for i in st.session_state.cart)
    try:
        cr = requests.get(f"{api_url}/coupons/validate", params={"code": coupon_code}, timeout=5)
        if cr.ok:
            cr_data = cr.json()
            if cr_data["valid"]:
                discount_percent = cr_data["discount"]
                discounted_total = cart_total * (1 - discount_percent / 100)
                st.sidebar.success(f"🎉 {discount_percent}% off — new total: ₹{discounted_total:.2f}")
            else:
                st.sidebar.error("Invalid or expired coupon.")
    except requests.exceptions.RequestException:
        st.sidebar.warning("Could not validate coupon.")
    return coupon_code, discount_percent


def _handle_prescription_upload():
    needs_rx = any(i.get('requires_rx', False) for i in st.session_state.cart)
    if not needs_rx:
        return None
    st.sidebar.warning("⚕️ Prescription required for one or more items.")
    return st.sidebar.file_uploader("Upload prescription", type=['jpg', 'png', 'jpeg', 'pdf'])


def _submit_order(api_url, customer_name, customer_email, customer_phone,
                  customer_address, pincode, coupon_code, discount_percent,
                  uploaded_file, area_name):
    needs_rx = any(i.get('requires_rx', False) for i in st.session_state.cart)
    if not customer_name:   st.sidebar.error("Full name is required."); return
    if not customer_email:  st.sidebar.error("Email is required."); return
    if not customer_phone:  st.sidebar.error("Phone number is required."); return
    if not customer_address: st.sidebar.error("Delivery address is required."); return
    if needs_rx and uploaded_file is None: st.sidebar.error("Please upload a prescription."); return

    try:
        rx_filename = None
        if uploaded_file is not None:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            up = requests.post(f"{api_url}/upload-prescription", files=files, timeout=15)
            if up.status_code == 200:
                rx_filename = up.json()["filename"]
            else:
                st.sidebar.error("Prescription upload failed.")
                return

        payload = {
            "customer_name": customer_name, "customer_email": customer_email,
            "customer_phone": customer_phone, "delivery_address": customer_address,
            "pincode": pincode, "prescription_image": rx_filename,
            "coupon_code": coupon_code if coupon_code else None,
            "items": [{"medicine_id": i["medicine_id"], "quantity": i["quantity"]}
                      for i in st.session_state.cart],
        }

        resp = requests.post(f"{api_url}/orders", json=payload, timeout=10)
        if resp.status_code == 200:
            order = resp.json()
            msg = f"Order #{order['id']} confirmed! Total ₹{order['total_price']:.2f}"
            if order.get('discount_applied'):
                msg += f" ({order['discount_applied']}% off)"
            st.sidebar.success(f"✅ {msg}")
            _save_profile(api_url, customer_email, customer_name, customer_phone, customer_address, pincode)
            st.session_state.cart = []
            st.rerun()
        elif resp.status_code == 429:
            st.sidebar.error("Too many orders. Please wait a moment.")
        else:
            st.sidebar.error(resp.json().get('detail', 'Order failed. Please try again.'))
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Checkout failed: {e}")


def _save_profile(api_url, email, name, phone, address, pincode):
    if not st.session_state.user:
        return
    try:
        requests.put(f"{api_url}/profile", json={
            "email": email, "name": name, "phone": phone,
            "address": address, "pincode": pincode,
            "area_name": st.session_state.get('last_area_name', ''),
        }, timeout=5)
        st.session_state.user.update({"name": name, "phone": phone, "address": address, "pincode": pincode})
    except requests.exceptions.RequestException:
        pass
