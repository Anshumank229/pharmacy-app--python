# frontend.py
import os
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api"

# Define the secret header for Admin actions
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")
ADMIN_HEADERS = {"x-admin-key": ADMIN_API_KEY}

st.set_page_config(page_title="Medicine Delivery", page_icon="💊", layout="wide")

# ==========================================
# 1. INITIALIZE SESSION STATE
# ==========================================
if 'show_profile' not in st.session_state: st.session_state.show_profile = False
if 'show_admin' not in st.session_state: st.session_state.show_admin = False
if 'cart' not in st.session_state: st.session_state.cart = []
if 'user' not in st.session_state: st.session_state.user = None

# --- GOOGLE LOGIN URL CATCHER ---
query_params = st.query_params
if "email" in query_params and "name" in query_params:
    st.session_state.user = {
        "name": query_params["name"],
        "email": query_params["email"]
    }
    st.query_params.clear()

# ==========================================
# 2. PROFILE PAGE VIEW
# ==========================================
if st.session_state.show_profile and st.session_state.user:
    st.title("📜 Your Order History")
    email = st.session_state.user['email']

    try:
        orders_resp = requests.get(f"{API_URL}/my-orders?email={email}", timeout=10)
        if orders_resp.status_code == 200:
            orders = orders_resp.json()
            if not orders:
                st.write("You haven't placed any orders yet.")
            else:
                for order in orders:
                    with st.expander(f"Order #{order['id']} - Status: {order['status']}"):
                        if order.get('prescription_image'):
                            st.info("📄 Prescription attached to this order.")
                        for item in order['items']:
                            st.write(f"- {item['medicine']['name']} (Qty: {item['quantity']})")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load orders. Backend might be asleep. Error: {e}")

    if st.button("⬅️ Back to Store"):
        st.session_state.show_profile = False
        st.rerun()
    st.stop()

# ==========================================
# 3. ADMIN DASHBOARD VIEW
# ==========================================
if st.session_state.get('show_admin'):
    st.title("⚙️ Admin Control Panel")

    try:
        orders_resp = requests.get(f"{API_URL}/admin/orders", headers=ADMIN_HEADERS, timeout=10)
        if orders_resp.status_code == 200:
            for order in orders_resp.json():
                with st.container():
                    st.write(
                        f"**Order #{order['id']}** | Customer: {order['customer_name']} | Status: {order['status']}")

                    if order.get('prescription_image'):
                        st.markdown(
                            f"[📄 View Prescription](http://127.0.0.1:8000/media/prescriptions/{order['prescription_image']})")

                    new_status = st.selectbox("Update Status", ['PENDING', 'PAID', 'SHIPPED', 'DELIVERED'],
                                              key=f"sel_{order['id']}")
                    if st.button("Update Status", key=f"btn_{order['id']}"):
                        requests.put(f"{API_URL}/admin/orders/{order['id']}?status={new_status}", headers=ADMIN_HEADERS,
                                     timeout=10)
                        st.rerun()
                    st.divider()
        else:
            st.error("Unauthorized to view admin dashboard.")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend. Error: {e}")

    if st.button("⬅️ Back to Store"):
        st.session_state.show_admin = False
        st.rerun()
    st.stop()

# ==========================================
# 4. MAIN STOREFRONT
# ==========================================
st.title("💊 Python Pharmacy Storefront")
st.write("Welcome to our 100% Python E-Commerce store!")
st.divider()

# ==========================================
# 5. SIDEBAR (Auth, Admin, & Cart)
# ==========================================
st.sidebar.header("👤 User Account")

if not st.session_state.user:
    st.sidebar.markdown("""
        <a href="http://127.0.0.1:8000/login/google-oauth2/" target="_blank">
            <button style="width: 100%; cursor: pointer;">Continue with Google</button>
        </a>
    """, unsafe_allow_html=True)

    st.sidebar.divider()
    st.sidebar.markdown("**Or use Email & Password**")

    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Continue"):
        if not email or not password:
            st.sidebar.warning("Please enter both email and password.")
        else:
            try:
                login_payload = {"email": email, "password": password}
                login_resp = requests.post(f"{API_URL}/login", json=login_payload, timeout=10)

                if login_resp.status_code == 200:
                    st.session_state.user = login_resp.json()
                    st.rerun()
                else:
                    default_name = email.split('@')[0].capitalize()
                    reg_payload = {"name": default_name, "email": email, "password": password}
                    reg_resp = requests.post(f"{API_URL}/register", json=reg_payload, timeout=10)

                    if reg_resp.status_code in [200, 201]:
                        st.session_state.user = {"name": default_name, "email": email}
                        st.rerun()
                    else:
                        st.sidebar.error("⚠️ Incorrect password.")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Connection error: {e}")
else:
    display_name = st.session_state.user.get('name', 'User')
    st.sidebar.write(f"Logged in as: **{display_name}**")

    if st.sidebar.button("View My Orders"): st.session_state.show_profile = True; st.rerun()
    if st.session_state.user.get('email') == "admin@pharmacy.com":
        if st.sidebar.button("⚙️ Admin Dashboard"): st.session_state.show_admin = True; st.rerun()
    if st.sidebar.button("Logout"): st.session_state.user = None; st.rerun()

# --- CART & PRESCRIPTION LOGIC ---
st.sidebar.divider()
st.sidebar.header("🛒 Your Shopping Cart")
if len(st.session_state.cart) == 0:
    st.sidebar.write("Your cart is empty.")
else:
    total_price = 0.0
    for item in st.session_state.cart:
        total_price += (item['quantity'] * item['price'])
        rx_badge = " *(Rx Required)*" if item.get('requires_rx') else ""
        st.sidebar.write(
            f"- **{item['quantity']}x** {item['name']}{rx_badge} (*${(item['quantity'] * item['price']):.2f}*)")

    st.sidebar.subheader(f"Total: ${total_price:.2f}")
    if st.sidebar.button("🗑️ Empty Cart"): st.session_state.cart = []; st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Checkout Details")
    customer_name = st.sidebar.text_input("Checkout Name",
                                          value=st.session_state.user.get('name', '') if st.session_state.user else "")
    customer_email = st.sidebar.text_input("Checkout Email", value=st.session_state.user.get('email',
                                                                                             '') if st.session_state.user else "")

    payment_method = st.sidebar.selectbox("Payment Method", ["💵 Cash on Delivery (COD)", "💳 Credit Card (Coming Soon)"])

    needs_rx = any(item.get('requires_rx', False) for item in st.session_state.cart)
    uploaded_file = None

    if needs_rx:
        st.sidebar.warning("⚠️ A doctor's prescription is required for one or more items in your cart.")
        uploaded_file = st.sidebar.file_uploader("Upload Prescription (Image)", type=['jpg', 'png', 'jpeg'])

    if payment_method == "💳 Credit Card (Coming Soon)":
        st.sidebar.info("Online payments are currently disabled. Please select Cash on Delivery.")
    elif not needs_rx or uploaded_file is not None:
        st.sidebar.info("🚚 You will pay the delivery agent when your order arrives.")

        if st.sidebar.button("Confirm COD Order", type="primary"):
            rx_filename = None

            try:
                if uploaded_file is not None:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    upload_resp = requests.post(f"{API_URL}/upload-prescription", files=files, timeout=15)
                    if upload_resp.status_code == 200:
                        rx_filename = upload_resp.json()["filename"]

                payload = {
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "prescription_image": rx_filename,
                    "items": [{"medicine_id": i["medicine_id"], "quantity": i["quantity"]} for i in
                              st.session_state.cart]
                }

                if requests.post(f"{API_URL}/orders", json=payload, timeout=10).status_code == 200:
                    st.sidebar.success("🎉 Order Placed! Please keep exact change ready for delivery.")
                    st.session_state.cart = []
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Checkout failed: {e}")

# ==========================================
# 6. MEDICINE SEARCH, FILTER & DISPLAY
# ==========================================
st.subheader("Available Medicines")

ctrl_cols = st.columns([2, 1, 1])

with ctrl_cols[0]:
    search_query = st.text_input("🔍 Search by name...", "")

category_id = None
try:
    cat_response = requests.get(f"{API_URL}/categories", timeout=10)
    if cat_response.status_code == 200:
        categories_data = cat_response.json()
        cat_options = ["All Categories"] + [cat['name'] for cat in categories_data]

        with ctrl_cols[1]:
            selected_cat = st.selectbox("🏷️ Filter by Category", cat_options)

        if selected_cat != "All Categories":
            category_id = next(cat['id'] for cat in categories_data if cat['name'] == selected_cat)
except requests.exceptions.RequestException as e:
    st.warning(f"Could not load categories: {e}")

with ctrl_cols[2]:
    sort_option = st.selectbox("📊 Sort By Price", ["Default", "Price: Low to High", "Price: High to Low"])

st.divider()

# --- FETCH & DISPLAY LOGIC ---
try:
    request_url = f"{API_URL}/medicines"
    params = {}
    if search_query:
        params["search"] = search_query
    if category_id is not None:
        params["category_id"] = category_id

    response = requests.get(request_url, params=params, timeout=10)

    if response.status_code == 200:
        medicines = response.json()

        if sort_option == "Price: Low to High":
            medicines = sorted(medicines, key=lambda x: float(x['price']))
        elif sort_option == "Price: High to Low":
            medicines = sorted(medicines, key=lambda x: float(x['price']), reverse=True)

        if not medicines:
            st.info("No medicines found matching the selected criteria.")
        else:
            cols = st.columns(3)
            for index, med in enumerate(medicines):
                with cols[index % 3]:
                    if med.get('image'):
                        st.image(f"http://127.0.0.1:8000/media/{med['image']}", use_column_width=True)
                    else:
                        st.info("No image available")

                    if med.get('requires_prescription'):
                        st.markdown("⚕️ **Prescription Required**")

                    st.markdown(f"### {med['name']}")
                    st.write(f"**Price:** ${med['price']}")

                    stock = med.get('stock', 0)

                    if stock == 0:
                        st.error("🚨 Out of Stock")
                        st.button("Add to Cart", key=f"med_{med['id']}", disabled=True)
                    else:
                        if stock <= 5:
                            st.warning(f"⚠️ Hurry! Only {stock} left.")

                        if st.button(f"Add to Cart", key=f"med_{med['id']}"):
                            item_found = False
                            for cart_item in st.session_state.cart:
                                if cart_item["medicine_id"] == med['id']:
                                    if cart_item["quantity"] < stock:
                                        cart_item["quantity"] += 1
                                        st.success(f"Added another {med['name']}!")
                                    else:
                                        st.error(f"Cannot add more. Only {stock} in stock!")
                                    item_found = True
                                    break

                            if not item_found:
                                st.session_state.cart.append({
                                    "medicine_id": med['id'],
                                    "name": med['name'],
                                    "quantity": 1,
                                    "price": float(med['price']),
                                    "requires_rx": med.get('requires_prescription', False)
                                })
                                st.success(f"Added {med['name']}!")

                    with st.expander(f"⭐ Reviews & Ratings"):
                        rev_resp = requests.get(f"{API_URL}/medicines/{med['id']}/reviews", timeout=10)
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

                        if st.session_state.user:
                            st.write("📝 **Write a Review**")
                            with st.form(key=f"review_form_{med['id']}"):
                                rating = st.slider("Rating", 1, 5, 5, key=f"rate_{med['id']}")
                                comment = st.text_area("Share your experience (optional)", key=f"comment_{med['id']}")
                                submit_review = st.form_submit_button("Submit Review")

                                if submit_review:
                                    payload = {
                                        "customer_name": st.session_state.user.get('name', 'User'),
                                        "rating": rating,
                                        "comment": comment
                                    }
                                    requests.post(f"{API_URL}/medicines/{med['id']}/reviews", json=payload, timeout=10)
                                    st.success("Review submitted! Thank you.")
                                    st.rerun()
                        else:
                            st.info("Please log in to leave a review.")
except requests.exceptions.RequestException as e:
    st.error(f"Backend not running or timed out. Error: {e}")