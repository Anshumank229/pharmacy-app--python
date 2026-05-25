# frontend.py
from dotenv import load_dotenv
load_dotenv()

import os
import time
from datetime import datetime, timedelta
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")
ADMIN_HEADERS = {"x-admin-key": ADMIN_API_KEY}
ADMIN_EMAIL = "kumaranshuman500@gmail.com"
WHATSAPP_NUMBER = "91XXXXXXXXXX"  # Replace with your actual number (country code + number, no +)

st.set_page_config(page_title="Medicine Delivery", page_icon="💊", layout="wide")

# Mobile-friendly CSS
st.markdown("""
<style>
  @media (max-width: 768px) {
    [data-testid="stSidebar"] { min-width: 100% !important; }
    .stButton button { width: 100%; }
  }
  .stButton button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. SESSION STATE
# ==========================================
defaults = {
    'show_profile': False,
    'show_admin': False,
    'cart': [],
    'user': None,
    'last_area_name': '',
    'last_pending_count': 0,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ==========================================
# 2. GOOGLE LOGIN URL CATCHER
# ==========================================
query_params = st.query_params
if "email" in query_params and "name" in query_params:
    email_from_google = query_params["email"]
    name_from_google = query_params["name"]
    # Check role from backend — don't trust frontend-only email matching
    try:
        role_resp = requests.get(f"{API_URL}/me", params={"email": email_from_google}, timeout=5)
        is_admin = role_resp.json().get("is_admin", False) if role_resp.ok else False
    except requests.exceptions.RequestException:
        is_admin = False
    st.session_state.user = {
        "name": name_from_google,
        "email": email_from_google,
        "is_admin": is_admin,
    }
    st.query_params.clear()


# ==========================================
# 3. LOAD PROFILE ONCE AFTER LOGIN
# ==========================================
if st.session_state.user and 'profile_loaded' not in st.session_state:
    try:
        prof_resp = requests.get(
            f"{API_URL}/profile",
            params={"email": st.session_state.user['email']},
            timeout=5,
        )
        if prof_resp.status_code == 200:
            prof = prof_resp.json()
            st.session_state.user['phone']     = prof.get('phone', '')
            st.session_state.user['address']   = prof.get('address', '')
            st.session_state.user['pincode']   = prof.get('pincode', '')
            st.session_state.user['area_name'] = prof.get('area_name', '')
    except requests.exceptions.RequestException:
        pass
    st.session_state.profile_loaded = True


# ==========================================
# HELPER — delivery estimate
# ==========================================
def delivery_estimate(created_at_str: str) -> str:
    try:
        created = datetime.fromisoformat(created_at_str)
        eta = created + timedelta(hours=24)
        now = datetime.now(tz=created.tzinfo)
        if eta > now:
            hrs = int((eta - now).total_seconds() // 3600)
            return f"Expected within ~{hrs} hrs"
        return "Expected: any moment now"
    except Exception:
        return "Expected within 24 hrs"


# ==========================================
# 4. PROFILE PAGE
# ==========================================
if st.session_state.show_profile and st.session_state.user:
    st.title("Your Profile & Orders")

    st.subheader("Saved delivery details")
    u = st.session_state.user or {}
    new_name    = st.text_input("Name",    value=u.get('name', ''))
    new_phone   = st.text_input("Phone",   value=u.get('phone', ''))
    new_address = st.text_area("Address",  value=u.get('address', ''))
    new_pincode = st.text_input("Pincode", value=u.get('pincode', ''))

    if st.button("Save details"):
        try:
            requests.put(
                f"{API_URL}/profile",
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
                "name": new_name, "phone": new_phone,
                "address": new_address, "pincode": new_pincode,
            })
            if 'profile_loaded' in st.session_state:
                del st.session_state.profile_loaded
            st.success("Details saved!")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not save: {e}")

    st.divider()

    st.subheader("Your order history")
    try:
        orders_resp = requests.get(
            f"{API_URL}/my-orders",
            params={"email": u['email']},
            timeout=10,
        )
        if orders_resp.status_code == 200:
            orders = orders_resp.json()
            if not orders:
                st.info("You haven't placed any orders yet.")
            else:
                for order in orders:
                    status = order['status']
                    status_emoji = {
                        'PENDING': '🕐', 'SHIPPED': '🚚',
                        'DELIVERED': '✅', 'CANCELLED': '❌'
                    }.get(status, '📦')

                    label = f"Order #{order['id']} — {status_emoji} {status}"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"📍 **Address:** {order.get('delivery_address', '—')}")
                            st.write(f"📮 **Pincode:** {order.get('pincode', '—')}")
                        with col2:
                            st.write(f"📞 **Phone:** {order.get('customer_phone', '—')}")
                            total = order.get('total_price', 0)
                            discount = order.get('discount_applied', 0)
                            if discount:
                                st.write(f"💰 **Total:** ₹{total:.2f} *(saved {discount}%)*")
                            else:
                                st.write(f"💰 **Total:** ₹{total:.2f}")

                        if status in ('PENDING', 'SHIPPED') and order.get('created_at'):
                            st.info(f"🚚 {delivery_estimate(order['created_at'])}")

                        if order.get('prescription_image'):
                            st.info("📄 Prescription attached.")

                        st.write("**Items ordered:**")
                        for item in order['items']:
                            st.write(
                                f"- {item['medicine']['name']} × {item['quantity']} "
                                f"(₹{item['price_at_time_of_purchase']} each)"
                            )

                        if status == 'PENDING':
                            if st.button("Cancel order", key=f"cancel_{order['id']}"):
                                try:
                                    r = requests.put(
                                        f"{API_URL}/orders/{order['id']}/cancel",
                                        params={"email": u['email']},
                                        timeout=10,
                                    )
                                    if r.status_code == 200:
                                        st.success("Order cancelled.")
                                        st.rerun()
                                    else:
                                        st.error(r.json().get('detail', 'Could not cancel.'))
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Error: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load orders: {e}")

    st.divider()
    if st.button("Back to store"):
        st.session_state.show_profile = False
        st.rerun()
    st.stop()


# ==========================================
# 5. ADMIN DASHBOARD
# ==========================================
if st.session_state.get('show_admin'):
    st.title("Admin control panel")

    try:
        orders_resp = requests.get(
            f"{API_URL}/admin/orders", headers=ADMIN_HEADERS, timeout=10
        )
        if orders_resp.status_code == 200:
            all_orders = orders_resp.json()

            # New order alert — compare pending count with last refresh
            current_pending = sum(1 for o in all_orders if o['status'] == 'PENDING')
            if current_pending > st.session_state.last_pending_count:
                new_count = current_pending - st.session_state.last_pending_count
                st.error(f"🔔 {new_count} new order(s) arrived!")
            st.session_state.last_pending_count = current_pending

            # Today's summary
            today_str = datetime.now().date().isoformat()
            todays = [o for o in all_orders if (o.get('created_at') or '').startswith(today_str)]
            pending_today   = sum(1 for o in todays if o['status'] == 'PENDING')
            shipped_today   = sum(1 for o in todays if o['status'] == 'SHIPPED')
            delivered_today = sum(1 for o in todays if o['status'] == 'DELIVERED')

            cols = st.columns(4)
            cols[0].metric("Pending today",   pending_today)
            cols[1].metric("Shipped today",   shipped_today)
            cols[2].metric("Delivered today", delivered_today)
            cols[3].metric("Total orders",    len(all_orders))

            # Low stock alert
            try:
                low = Medicine.objects.filter(stock__lte=5).values('name', 'stock')
                if low:
                    names = ", ".join(f"{m['name']} ({m['stock']} left)" for m in low)
                    st.warning(f"⚠️ Low stock: {names}")
            except Exception:
                pass

            st.divider()
            st.subheader("All orders")

            for order in all_orders:
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
                        if order.get('prescription_image'):
                            st.markdown(
                                f"[📄 View prescription](http://127.0.0.1:8000/api/prescriptions/{order['prescription_image']})",
                            )
                    with c2:
                        st.write(f"Status: **{order['status']}**")
                        new_status = st.selectbox(
                            "Update",
                            ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED'],
                            key=f"sel_{order['id']}",
                            index=['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED'].index(order['status']),
                        )
                        if st.button("Save", key=f"btn_{order['id']}"):
                            try:
                                requests.put(
                                    f"{API_URL}/admin/orders/{order['id']}",
                                    params={"status": new_status},
                                    headers=ADMIN_HEADERS,
                                    timeout=10,
                                )
                                st.rerun()
                            except requests.exceptions.RequestException as e:
                                st.error(f"Update failed: {e}")
                    st.divider()

        else:
            st.error("Unauthorized — check your ADMIN_API_KEY.")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")

    if st.button("Back to store"):
        st.session_state.show_admin = False
        st.rerun()

    # Auto-refresh AFTER content is rendered — was incorrectly placed before content
    st.caption("Auto-refreshing every 60 seconds…")
    time.sleep(60)
    st.rerun()

    st.stop()


# ==========================================
# 6. MAIN STOREFRONT
# ==========================================
st.title("💊 Your Local Pharmacy")
st.write("Order now — delivered to your door within 24 hours. Pay on delivery.")
st.markdown(
    f"[💬 WhatsApp support](https://wa.me/{WHATSAPP_NUMBER}?text=Hi,%20I%20need%20help%20with%20my%20order)",
    unsafe_allow_html=False,
)
st.divider()


# ==========================================
# 7. SIDEBAR — AUTH
# ==========================================
st.sidebar.header("Your account")

if not st.session_state.user:
    st.sidebar.markdown("""
        <a href="http://127.0.0.1:8000/login/google-oauth2/" target="_blank">
            <button style="width:100%;padding:8px;cursor:pointer;border-radius:8px;border:1px solid #ccc;">
                Continue with Google
            </button>
        </a>
    """, unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.markdown("**Or use email & password**")

    email    = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Continue", use_container_width=True):
        if not email or not password:
            st.sidebar.warning("Please enter both email and password.")
        else:
            try:
                login_resp = requests.post(
                    f"{API_URL}/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                if login_resp.status_code == 200:
                    data = login_resp.json()
                    st.session_state.user = {
                        "name": data.get("name", ""),
                        "email": data.get("email", ""),
                        "is_admin": data.get("is_admin", False),
                    }
                    st.rerun()
                elif login_resp.status_code == 429:
                    st.sidebar.error("Too many login attempts. Please wait a minute.")
                else:
                    # Auto-register on first visit
                    default_name = email.split('@')[0].capitalize()
                    reg_resp = requests.post(
                        f"{API_URL}/register",
                        json={"name": default_name, "email": email, "password": password},
                        timeout=10,
                    )
                    if reg_resp.status_code in [200, 201]:
                        st.session_state.user = {
                            "name": default_name,
                            "email": email,
                            "is_admin": False,
                        }
                        st.sidebar.success("Welcome! Your account has been created.")
                        st.rerun()
                    else:
                        st.sidebar.error("Incorrect password. Please try again.")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Connection error: {e}")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user.get('name', 'User')}**")
    if st.sidebar.button("My profile & orders", use_container_width=True):
        st.session_state.show_profile = True
        st.rerun()
    # Admin button shown only if backend confirmed is_admin — not just by email string
    if st.session_state.user.get('email') == ADMIN_EMAIL and st.session_state.user.get('is_admin'):
        if st.sidebar.button("Admin dashboard", use_container_width=True):
            st.session_state.show_admin = True
            st.rerun()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        if 'profile_loaded' in st.session_state:
            del st.session_state.profile_loaded
        st.rerun()


# ==========================================
# 8. SIDEBAR — CART & CHECKOUT
# ==========================================
st.sidebar.divider()
st.sidebar.header("Your cart")

if not st.session_state.cart:
    st.sidebar.write("Your cart is empty.")
else:
    cart_total = sum(i['quantity'] * i['price'] for i in st.session_state.cart)
    for item in st.session_state.cart:
        rx = " *(Rx)*" if item.get('requires_rx') else ""
        st.sidebar.write(
            f"- **{item['quantity']}x** {item['name']}{rx} "
            f"(*₹{item['quantity'] * item['price']:.2f}*)"
        )
    st.sidebar.subheader(f"Total: ₹{cart_total:.2f}")
    if st.sidebar.button("Empty cart", use_container_width=True):
        st.session_state.cart = []
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Checkout")

    u = st.session_state.user or {}
    customer_name    = st.sidebar.text_input("Full name",        value=u.get('name', ''))
    customer_email   = st.sidebar.text_input("Email",            value=u.get('email', ''))
    customer_phone   = st.sidebar.text_input("Phone number",     value=u.get('phone', ''),   placeholder="98XXXXXXXX")
    customer_address = st.sidebar.text_area("Delivery address",  value=u.get('address', ''), placeholder="House no, street, landmark...")
    pincode          = st.sidebar.text_input("Pincode",          value=u.get('pincode', ''), placeholder="e.g. 800001", max_chars=10)

    # Live pincode validation
    pincode_ok = False
    area_name  = None

    if pincode:
        if len(pincode) == 6 and pincode.isdigit():
            try:
                pc = requests.get(f"{API_URL}/check-pincode", params={"pincode": pincode}, timeout=5)
                if pc.status_code == 200:
                    res = pc.json()
                    if res["serviceable"]:
                        pincode_ok = True
                        area_name  = res["area_name"]
                        st.session_state.last_area_name = area_name
                        st.sidebar.success(f"✅ We deliver to {area_name}!")
                    else:
                        st.sidebar.error("Sorry, we don't deliver to this pincode yet.")
            except requests.exceptions.RequestException:
                st.sidebar.warning("Could not verify pincode. Try again.")
        else:
            st.sidebar.warning("Enter a valid 6-digit pincode.")

    # Coupon code
    coupon_code = st.sidebar.text_input("Coupon code (optional)")
    discount_percent = 0
    if coupon_code:
        try:
            cr = requests.get(f"{API_URL}/coupons/validate", params={"code": coupon_code}, timeout=5)
            if cr.ok:
                cr_data = cr.json()
                if cr_data["valid"]:
                    discount_percent = cr_data["discount"]
                    discounted_total = cart_total * (1 - discount_percent / 100)
                    st.sidebar.success(f"🎉 {discount_percent}% off! New total: ₹{discounted_total:.2f}")
                else:
                    st.sidebar.error("Invalid or expired coupon.")
        except requests.exceptions.RequestException:
            st.sidebar.warning("Could not validate coupon. Try again.")

    # Prescription upload if needed
    needs_rx      = any(i.get('requires_rx', False) for i in st.session_state.cart)
    uploaded_file = None
    if needs_rx:
        st.sidebar.warning("⚕️ A prescription is required for one or more items.")
        uploaded_file = st.sidebar.file_uploader("Upload prescription", type=['jpg', 'png', 'jpeg', 'pdf'])

    st.sidebar.info("🚚 Delivered within 24 hours. Pay cash on delivery.")

    if not pincode_ok:
        st.sidebar.caption("Enter a serviceable pincode to enable checkout.")

    if st.sidebar.button("Confirm order", type="primary", disabled=not pincode_ok, use_container_width=True):
        if not customer_phone:
            st.sidebar.error("Phone number is required.")
        elif not customer_address:
            st.sidebar.error("Delivery address is required.")
        elif needs_rx and uploaded_file is None:
            st.sidebar.error("Please upload a prescription.")
        else:
            try:
                rx_filename = None
                if uploaded_file is not None:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    up = requests.post(f"{API_URL}/upload-prescription", files=files, timeout=15)
                    if up.status_code == 200:
                        rx_filename = up.json()["filename"]
                    else:
                        st.sidebar.error("Prescription upload failed. Please try again.")
                        st.stop()

                payload = {
                    "customer_name":    customer_name,
                    "customer_email":   customer_email,
                    "customer_phone":   customer_phone,
                    "delivery_address": customer_address,
                    "pincode":          pincode,
                    "prescription_image": rx_filename,
                    "coupon_code":      coupon_code if coupon_code else None,
                    "items": [
                        {"medicine_id": i["medicine_id"], "quantity": i["quantity"]}
                        for i in st.session_state.cart
                    ],
                }

                resp = requests.post(f"{API_URL}/orders", json=payload, timeout=10)
                if resp.status_code == 200:
                    order = resp.json()
                    msg = (
                        f"✅ Order #{order['id']} placed! "
                        f"Total: ₹{order['total_price']:.2f}"
                    )
                    if order.get('discount_applied'):
                        msg += f" ({order['discount_applied']}% coupon applied)"
                    msg += f". Expected within 24 hours. We'll call {customer_phone} before arrival."
                    st.sidebar.success(msg)

                    # Save profile silently for next time
                    if st.session_state.user:
                        try:
                            requests.put(
                                f"{API_URL}/profile",
                                json={
                                    "email":     customer_email,
                                    "name":      customer_name,
                                    "phone":     customer_phone,
                                    "address":   customer_address,
                                    "pincode":   pincode,
                                    "area_name": st.session_state.get('last_area_name', ''),
                                },
                                timeout=5,
                            )
                            st.session_state.user.update({
                                "name":    customer_name,
                                "phone":   customer_phone,
                                "address": customer_address,
                                "pincode": pincode,
                            })
                        except requests.exceptions.RequestException:
                            pass

                    st.session_state.cart = []
                    st.rerun()
                else:
                    st.sidebar.error(resp.json().get('detail', 'Order failed. Please try again.'))
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Checkout failed: {e}")


# ==========================================
# 9. MEDICINE SEARCH, FILTER & DISPLAY
# ==========================================
st.subheader("Available medicines")
ctrl_cols = st.columns([2, 1, 1, 1])

with ctrl_cols[0]:
    search_query = st.text_input("Search by name or brand…", "")

category_id = None
try:
    cat_resp = requests.get(f"{API_URL}/categories", timeout=10)
    if cat_resp.status_code == 200:
        categories_data = cat_resp.json()
        cat_options = ["All categories"] + [c['name'] for c in categories_data]
        with ctrl_cols[1]:
            selected_cat = st.selectbox("Category", cat_options)
        if selected_cat != "All categories":
            category_id = next(c['id'] for c in categories_data if c['name'] == selected_cat)
except requests.exceptions.RequestException as e:
    st.warning(f"Could not load categories: {e}")

with ctrl_cols[2]:
    sort_option = st.selectbox("Sort by price", ["Default", "Low to high", "High to low"])

with ctrl_cols[3]:
    col_count = st.selectbox("Layout", ["2 columns", "3 columns"], index=0)

st.divider()

try:
    params = {}
    if search_query: params["search"]      = search_query
    if category_id:  params["category_id"] = category_id

    resp = requests.get(f"{API_URL}/medicines", params=params, timeout=10)
    if resp.status_code == 200:
        medicines = resp.json()

        if sort_option == "Low to high":
            medicines = sorted(medicines, key=lambda x: float(x['price']))
        elif sort_option == "High to low":
            medicines = sorted(medicines, key=lambda x: float(x['price']), reverse=True)

        if not medicines:
            st.info("No medicines found.")
        else:
            num_cols = 2 if col_count == "2 columns" else 3
            cols = st.columns(num_cols)
            for index, med in enumerate(medicines):
                with cols[index % num_cols]:
                    if med.get('image'):
                        st.image(
                            f"http://127.0.0.1:8000/media/{med['image']}",
                            use_container_width=True,   # fixed: use_column_width is deprecated
                        )
                    else:
                        st.info("No image")

                    if med.get('requires_prescription'):
                        st.markdown("⚕️ **Prescription required**")

                    st.markdown(f"### {med['name']}")
                    st.write(f"**Price:** ₹{med['price']}")

                    stock = med.get('stock', 0)
                    if stock == 0:
                        st.error("Out of stock")
                        st.button("Add to cart", key=f"med_{med['id']}", disabled=True)
                    else:
                        if stock <= 5:
                            st.warning(f"Only {stock} left!")
                        if st.button("Add to cart", key=f"med_{med['id']}", use_container_width=True):
                            item_found = False
                            for cart_item in st.session_state.cart:
                                if cart_item["medicine_id"] == med['id']:
                                    if cart_item["quantity"] < stock:
                                        cart_item["quantity"] += 1
                                        st.success(f"Added another {med['name']}!")
                                    else:
                                        st.error(f"Only {stock} in stock!")
                                    item_found = True
                                    break
                            if not item_found:
                                st.session_state.cart.append({
                                    "medicine_id": med['id'],
                                    "name":        med['name'],
                                    "quantity":    1,
                                    "price":       float(med['price']),
                                    "requires_rx": med.get('requires_prescription', False),
                                })
                                st.success(f"Added {med['name']}!")

                    with st.expander("Reviews & ratings"):
                        try:
                            rev_resp = requests.get(
                                f"{API_URL}/medicines/{med['id']}/reviews", timeout=10
                            )
                            if rev_resp.status_code == 200:
                                reviews = rev_resp.json()
                                if not reviews:
                                    st.write("No reviews yet. Be the first!")
                                else:
                                    for r in reviews:
                                        st.markdown(f"**{r['customer_name']}** {'⭐' * r['rating']}")
                                        if r['comment']:
                                            st.write(f"*{r['comment']}*")
                                        st.divider()
                        except requests.exceptions.RequestException:
                            st.warning("Could not load reviews.")

                        if st.session_state.user:
                            with st.form(key=f"review_form_{med['id']}"):
                                rating  = st.slider("Rating", 1, 5, 5)
                                comment = st.text_area("Your experience (optional)")
                                if st.form_submit_button("Submit review"):
                                    try:
                                        requests.post(
                                            f"{API_URL}/medicines/{med['id']}/reviews",
                                            json={
                                                "customer_name": st.session_state.user.get('name', 'User'),
                                                "rating":  rating,
                                                "comment": comment,
                                            },
                                            timeout=10,
                                        )
                                        st.success("Review submitted!")
                                        st.rerun()
                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Could not submit review: {e}")
                        else:
                            st.info("Log in to leave a review.")

except requests.exceptions.RequestException as e:
    st.error(f"Could not reach backend: {e}")