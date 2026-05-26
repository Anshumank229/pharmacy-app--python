import requests
import streamlit as st


def render_store(api_url: str):
    """
    Main storefront: search bar, category/sort/layout controls,
    and the medicine card grid.
    """
    st.subheader("Available medicines")

    search_query, category_id, sort_option, num_cols = _render_controls(api_url)

    st.divider()

    _render_medicine_grid(api_url, search_query, category_id, sort_option, num_cols)


# ==========================================
# CONTROLS ROW
# ==========================================
def _render_controls(api_url: str):
    ctrl_cols = st.columns([2, 1, 1, 1])

    with ctrl_cols[0]:
        search_query = st.text_input("Search by name or brand…", "", max_chars=100)

    category_id = _render_category_filter(api_url, ctrl_cols[1])

    with ctrl_cols[2]:
        sort_option = st.selectbox("Sort by price", ["Default", "Low to high", "High to low"])

    with ctrl_cols[3]:
        col_count = st.selectbox("Layout", ["2 columns", "3 columns"], index=0)
        num_cols  = 2 if col_count == "2 columns" else 3

    return search_query, category_id, sort_option, num_cols


def _render_category_filter(api_url: str, column):
    category_id = None
    try:
        cat_resp = requests.get(f"{api_url}/categories", timeout=10)
        if cat_resp.status_code == 200:
            categories_data = cat_resp.json()
            cat_options = ["All categories"] + [c['name'] for c in categories_data]
            with column:
                selected_cat = st.selectbox("Category", cat_options)
            if selected_cat != "All categories":
                category_id = next(c['id'] for c in categories_data if c['name'] == selected_cat)
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not load categories: {e}")
    return category_id


# ==========================================
# MEDICINE GRID
# ==========================================
def _render_medicine_grid(api_url, search_query, category_id, sort_option, num_cols):
    try:
        params = {}
        if search_query: params["search"]      = search_query
        if category_id:  params["category_id"] = category_id

        resp = requests.get(f"{api_url}/medicines", params=params, timeout=10)
        if resp.status_code != 200:
            st.error("Could not load medicines.")
            return

        medicines = resp.json()

        if sort_option == "Low to high":
            medicines = sorted(medicines, key=lambda x: float(x['price']))
        elif sort_option == "High to low":
            medicines = sorted(medicines, key=lambda x: float(x['price']), reverse=True)

        if not medicines:
            st.info("No medicines found.")
            return

        base_url = api_url.replace('/api', '')
        cols     = st.columns(num_cols)

        for index, med in enumerate(medicines):
            with cols[index % num_cols]:
                _render_medicine_card(api_url, med, base_url)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach backend: {e}")


# ==========================================
# SINGLE MEDICINE CARD
# ==========================================
def _render_medicine_card(api_url: str, med: dict, base_url: str):
    if med.get('image'):
        st.image(f"{base_url}/media/{med['image']}", use_container_width=True)
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

        btn_cols = st.columns(2)
        with btn_cols[0]:
            if st.button("Add to cart", key=f"med_{med['id']}", use_container_width=True):
                _add_to_cart(med, stock)
        with btn_cols[1]:
            if st.button("Details", key=f"det_{med['id']}", use_container_width=True):
                st.session_state.show_medicine_detail = True
                st.session_state.selected_medicine_id = med['id']
                st.rerun()

    _render_inline_reviews(api_url, med)


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
    st.success(f"Added {med['name']}!")


# ==========================================
# INLINE REVIEWS (collapsed)
# ==========================================
def _render_inline_reviews(api_url: str, med: dict):
    with st.expander("Reviews"):
        try:
            rev_resp = requests.get(f"{api_url}/medicines/{med['id']}/reviews", timeout=10)
            if rev_resp.status_code == 200:
                reviews = rev_resp.json()
                if not reviews:
                    st.write("No reviews yet.")
                else:
                    avg = sum(r['rating'] for r in reviews) / len(reviews)
                    st.write(f"{'⭐' * round(avg)} ({avg:.1f})")
                    for r in reviews[:3]:
                        st.markdown(f"**{r['customer_name']}** {'⭐' * r['rating']}")
                        if r['comment']:
                            st.write(f"*{r['comment']}*")
        except requests.exceptions.RequestException:
            st.warning("Could not load reviews.")

        if st.session_state.user:
            with st.form(key=f"review_form_{med['id']}"):
                rating  = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Your experience (optional)", max_chars=2000)
                if st.form_submit_button("Submit review"):
                    try:
                        requests.post(
                            f"{api_url}/medicines/{med['id']}/reviews",
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
