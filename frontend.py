# frontend.py
import os
from datetime import datetime, timedelta
import streamlit as st
import requests



API_URL = "http://127.0.0.1:8000/api"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")
ADMIN_HEADERS = {"x-admin-key": ADMIN_API_KEY}

st.set_page_config(page_title="Medicine Delivery", page_icon="💊", layout="wide")

# ==========================================
# 1. SESSION STATE
# ==========================================
if 'show_profile' not in st.session_state: st.session_state.show_profile = False
if 'show_admin' not in st.session_state: st.session_state.show_admin = False
if 'cart' not in st.session_state: st.session_state.cart = []
if 'user' not in st.session_state: st.session_state.user = None

# ==========================================
# 2. GOOGLE LOGIN URL CATCHER
# ==========================================
query_params = st.query_params
if "email" in query_params and "name" in query_params:
    st.session_state.user = {
        "name": query_params["name"],
        "email": query_params["email"],
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
# HELPER — delivery estimate label
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

    # --- SAVED DETAILS ---
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

    # --- ORDER HISTORY ---
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
                            st.write(f"💰 **Total:** ₹{order.get('total_price', 0)}")

                        # Delivery estimate for active orders
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

                        # Cancel button — only for PENDING orders
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

    import time

    st.markdown("*Auto-refreshing every 60 seconds*")
    time.sleep(60)
    st.rerun()

    try:
        orders_resp = requests.get(
            f"{API_URL}/admin/orders", headers=ADMIN_HEADERS, timeout=10
        )
        if orders_resp.status_code == 200:
            all_orders = orders_resp.json()

            # Today's summary counts
            today = datetime.now().date()
            todays = [o for o in all_orders if o.get('created_at', '').startswith(str(today))]
            pending   = sum(1 for o in todays if o['status'] == 'PENDING')
            shipped   = sum(1 for o in todays if o['status'] == 'SHIPPED')
            delivered = sum(1 for o in todays if o['status'] == 'DELIVERED')

            st.markdown(
                f"**Today:** 🕐 {pending} pending &nbsp;|&nbsp; "
                f"🚚 {shipped} shipped &nbsp;|&nbsp; ✅ {delivered} delivered"
            )

            # Low stock alert
            try:
                from inventory.models import Medicine as Med
                low = Med.objects.filter(stock__lte=5).values('name', 'stock')
                if low:
                    names = ", ".join(f"{m['name']} ({m['stock']} left)" for m in low)
                    st.warning(f"⚠️ Low stock: {names}")
            except Exception:
                pass

            st.divider()

            for order in all_orders:
                with st.container():
                    st.write(
                        f"**Order #{order['id']}** | {order['customer_name']} | "
                        f"📞 {order.get('customer_phone','—')} | "
                        f"📮 {order.get('pincode','—')} | "
                        f"💰 ₹{order.get('total_price', 0)} | "
                        f"Status: **{order['status']}**"
                    )
                    st.write(f"📍 {order.get('delivery_address', '—')}")

                    if order.get('prescription_image'):
                        st.markdown(
                            f"[📄 View Prescription](http://127.0.0.1:8000/media/prescriptions/{order['prescription_image']})"
                        )

                    new_status = st.selectbox(
                        "Update status",
                        ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED'],
                        key=f"sel_{order['id']}",
                    )
                    if st.button("Update", key=f"btn_{order['id']}"):
                        requests.put(
                            f"{API_URL}/admin/orders/{order['id']}",
                            params={"status": new_status},
                            headers=ADMIN_HEADERS,
                            timeout=10,
                        )
                        st.rerun()
                    st.divider()
        else:
            st.error("Unauthorized.")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")

    if st.button("Back to store"):
        st.session_state.show_admin = False
        st.rerun()
    st.stop()


# ==========================================
# 6. MAIN STOREFRONT
# ==========================================
st.title("💊 Your Local Pharmacy")
st.write("Order now — delivered to your door within 24 hours. Pay on delivery.")

# WhatsApp support button
st.markdown(
    "[💬 Questions? WhatsApp us](https://wa.me/91XXXXXXXXXX?text=Hi,%20I%20need%20help%20with%20my%20order)",
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
            <button style="width:100%;cursor:pointer;">Continue with Google</button>
        </a>
    """, unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.markdown("**Or use email & password**")

    email    = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Continue"):
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
                    st.session_state.user = login_resp.json()
                    st.rerun()
                else:
                    # Auto-register new users on first visit
                    default_name = email.split('@')[0].capitalize()
                    reg_resp = requests.post(
                        f"{API_URL}/register",
                        json={"name": default_name, "email": email, "password": password},
                        timeout=10,
                    )
                    if reg_resp.status_code in [200, 201]:
                        st.session_state.user = {"name": default_name, "email": email}
                        st.sidebar.success("Welcome! Your account has been created.")
                        st.rerun()
                    else:
                        st.sidebar.error("Incorrect password. Please try again.")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Connection error: {e}")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user.get('name', 'User')}**")
    if st.sidebar.button("My profile & orders"):
        st.session_state.show_profile = True
        st.rerun()
    if st.session_state.user.get('email') == "admin@pharmacy.com":
        if st.sidebar.button("Admin dashboard"):
            st.session_state.show_admin = True
            st.rerun()
    if st.sidebar.button("Logout"):
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
    total_price = sum(i['quantity'] * i['price'] for i in st.session_state.cart)
    for item in st.session_state.cart:
        rx = " *(Rx)*" if item.get('requires_rx') else ""
        st.sidebar.write(
            f"- **{item['quantity']}x** {item['name']}{rx} "
            f"(*₹{item['quantity'] * item['price']:.2f}*)"
        )
    st.sidebar.subheader(f"Total: ₹{total_price:.2f}")
    if st.sidebar.button("Empty cart"):
        st.session_state.cart = []
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Checkout")

    u = st.session_state.user or {}
    customer_name    = st.sidebar.text_input("Full name",         value=u.get('name', ''))
    customer_email   = st.sidebar.text_input("Email",             value=u.get('email', ''))
    customer_phone   = st.sidebar.text_input("Phone number",      value=u.get('phone', ''),   placeholder="98XXXXXXXX")
    customer_address = st.sidebar.text_area("Delivery address",   value=u.get('address', ''), placeholder="House no, street, landmark...")
    pincode          = st.sidebar.text_input("Pincode",           value=u.get('pincode', ''), placeholder="e.g. 141001", max_chars=10)

    # Live pincode check
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
                        st.sidebar.success(f"We deliver to {area_name}!")
                    else:
                        st.sidebar.error("Sorry, we don't deliver to this pincode yet.")
            except requests.exceptions.RequestException:
                st.sidebar.warning("Could not verify pincode. Try again.")
        else:
            st.sidebar.warning("Enter a valid 6-digit pincode.")

    needs_rx      = any(i.get('requires_rx', False) for i in st.session_state.cart)
    uploaded_file = None

    if needs_rx:
        st.sidebar.warning("A prescription is required for one or more items.")
        uploaded_file = st.sidebar.file_uploader("Upload prescription", type=['jpg', 'png', 'jpeg'])

    st.sidebar.info("🚚 Delivered within 24 hours. Pay cash on delivery.")

    confirm_disabled = not pincode_ok
    if confirm_disabled:
        st.sidebar.caption("Enter a serviceable pincode to enable checkout.")

    if st.sidebar.button("Confirm order", type="primary", disabled=confirm_disabled):
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

                payload = {
                    "customer_name":    customer_name,
                    "customer_email":   customer_email,
                    "customer_phone":   customer_phone,
                    "delivery_address": customer_address,
                    "pincode":          pincode,
                    "prescription_image": rx_filename,
                    "items": [
                        {"medicine_id": i["medicine_id"], "quantity": i["quantity"]}
                        for i in st.session_state.cart
                    ],
                }

                resp = requests.post(f"{API_URL}/orders", json=payload, timeout=10)
                if resp.status_code == 200:
                    order = resp.json()
                    st.sidebar.success(
                        f"Order #{order['id']} placed! "
                        f"Expected delivery within 24 hours. "
                        f"We'll call you on {customer_phone} before arrival."
                    )

                    # Silently save profile for next time
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
                                "name":     customer_name,
                                "phone":    customer_phone,
                                "address":  customer_address,
                                "pincode":  pincode,
                            })
                        except requests.exceptions.RequestException:
                            pass  # non-critical

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
ctrl_cols = st.columns([2, 1, 1])

with ctrl_cols[0]:
    search_query = st.text_input("Search by name or brand...", "")

category_id = None
try:
    cat_resp = requests.get(f"{API_URL}/categories", timeout=10)
    if cat_resp.status_code == 200:
        categories_data = cat_resp.json()
        cat_options = ["All categories"] + [c['name'] for c in categories_data]
        with ctrl_cols[1]:
            selected_cat = st.selectbox("Filter by category", cat_options)
        if selected_cat != "All categories":
            category_id = next(c['id'] for c in categories_data if c['name'] == selected_cat)
except requests.exceptions.RequestException as e:
    st.warning(f"Could not load categories: {e}")

with ctrl_cols[2]:
    sort_option = st.selectbox("Sort by price", ["Default", "Low to high", "High to low"])

st.divider()

try:
    params = {}
    if search_query:   params["search"]      = search_query
    if category_id:    params["category_id"] = category_id

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
            cols = st.columns(3)
            for index, med in enumerate(medicines):
                with cols[index % 3]:
                    if med.get('image'):
                        st.image(f"http://127.0.0.1:8000/media/{med['image']}", use_column_width=True)
                    else:
                        st.info("No image available")

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
                        if st.button("Add to cart", key=f"med_{med['id']}"):
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
                                    "medicine_id":  med['id'],
                                    "name":         med['name'],
                                    "quantity":     1,
                                    "price":        float(med['price']),
                                    "requires_rx":  med.get('requires_prescription', False),
                                })
                                st.success(f"Added {med['name']}!")

                    # Reviews — fetched only when expander is opened by Streamlit's lazy eval
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