import requests
import streamlit as st


def render_medicine_detail(api_url: str):
    """
    Full-page medicine detail view.
    Renders image, stock, description, reviews, and add-to-cart.
    Calls st.stop() so nothing else renders behind it.
    """
    med_id = st.session_state.selected_medicine_id

    try:
        med_resp = requests.get(f"{api_url}/medicines/{med_id}", timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load medicine: {e}")
        _back_button()
        st.stop()

    if med_resp.status_code != 200:
        st.error("Medicine not found.")
        _back_button()
        st.stop()

    med = med_resp.json()

    if st.button("← Back to store"):
        _close_detail()

    # ---- Header ----
    st.title(med['name'])
    if med.get('brand'):
        st.caption(f"Brand: {med['brand']}")

    # ---- Image + purchase panel ----
    col1, col2 = st.columns([1, 2])
    with col1:
        _render_image(api_url, med)
    with col2:
        _render_purchase_panel(med)

    st.divider()

    # ---- Reviews ----
    _render_reviews_section(api_url, med_id)

    st.stop()


# ==========================================
# HELPERS
# ==========================================
def _close_detail():
    st.session_state.show_medicine_detail = False
    st.session_state.selected_medicine_id = None
    st.rerun()


def _back_button():
    if st.button("Back to store"):
        _close_detail()


def _render_image(api_url: str, med: dict):
    if med.get('image'):
        base_url = api_url.replace('/api', '')
        st.image(f"{base_url}/media/{med['image']}", use_container_width=True)
    else:
        st.info("No image available")


def _render_purchase_panel(med: dict):
    if med.get('requires_prescription'):
        st.warning("⚕️ Prescription required")

    st.markdown(f"### ₹{med['price']}")

    stock = med.get('stock', 0)
    if stock == 0:
        st.error("Out of stock")
    elif stock <= 5:
        st.warning(f"Only {stock} left in stock!")
    else:
        st.success(f"In stock ({stock} available)")

    # Details rows
    details = []
    if med.get('dosage_form'): details.append(f"**Form:** {med['dosage_form']}")
    if med.get('strength'):    details.append(f"**Strength:** {med['strength']}")
    if med.get('category'):    details.append(f"**Category:** {med['category']['name']}")
    for d in details:
        st.markdown(d)

    if med.get('description'):
        st.divider()
        st.markdown("**About this medicine**")
        st.write(med['description'])

    if stock > 0:
        if st.button("Add to cart", type="primary", use_container_width=True):
            _add_to_cart(med, stock)


def _add_to_cart(med: dict, stock: int):
    for cart_item in st.session_state.cart:
        if cart_item["medicine_id"] == med['id']:
            if cart_item["quantity"] < stock:
                cart_item["quantity"] += 1
                st.success(f"Added another {med['name']}!")
            else:
                st.error(f"Only {stock} in stock!")
            return

    st.session_state.cart.append({
        "medicine_id": med['id'],
        "name":        med['name'],
        "quantity":    1,
        "price":       float(med['price']),
        "requires_rx": med.get('requires_prescription', False),
    })
    st.success(f"Added {med['name']} to cart!")


# ==========================================
# REVIEWS
# ==========================================
def _render_reviews_section(api_url: str, med_id: int):
    st.subheader("Reviews & ratings")

    try:
        rev_resp = requests.get(f"{api_url}/medicines/{med_id}/reviews", timeout=10)
        if rev_resp.status_code == 200:
            reviews = rev_resp.json()
            if not reviews:
                st.info("No reviews yet. Be the first!")
            else:
                avg = sum(r['rating'] for r in reviews) / len(reviews)
                st.markdown(
                    f"**Average rating: {'⭐' * round(avg)} ({avg:.1f}/5 from {len(reviews)} reviews)**"
                )
                st.divider()
                for r in reviews:
                    st.markdown(f"**{r['customer_name']}** {'⭐' * r['rating']}")
                    if r['comment']:
                        st.write(f"*{r['comment']}*")
                    st.divider()
    except requests.exceptions.RequestException:
        st.warning("Could not load reviews.")

    if st.session_state.user:
        _render_review_form(api_url, med_id)
    else:
        st.info("Log in to leave a review.")


def _render_review_form(api_url: str, med_id: int):
    st.subheader("Leave a review")
    with st.form(key=f"detail_review_{med_id}"):
        rating  = st.slider("Rating", 1, 5, 5)
        comment = st.text_area("Your experience (optional)", max_chars=2000)
        if st.form_submit_button("Submit review"):
            try:
                requests.post(
                    f"{api_url}/medicines/{med_id}/reviews",
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
                st.error(f"Could not submit: {e}")
