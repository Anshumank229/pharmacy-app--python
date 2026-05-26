import requests
import streamlit as st


def render_store(api_url: str):
    st.markdown('<p class="section-label">Browse Medicines</p>', unsafe_allow_html=True)
    search_query, category_id, sort_option, num_cols = _render_controls(api_url)
    st.markdown("<hr>", unsafe_allow_html=True)
    _render_medicine_grid(api_url, search_query, category_id, sort_option, num_cols)


def _render_controls(api_url: str):
    ctrl_cols = st.columns([2, 1, 1, 1])
    with ctrl_cols[0]:
        search_query = st.text_input("Search by name or brand", "", max_chars=100,
                                     placeholder="e.g. Paracetamol, Cipla...")
    category_id = _render_category_filter(api_url, ctrl_cols[1])
    with ctrl_cols[2]:
        sort_option = st.selectbox("Sort by price", ["Default", "Low to High", "High to Low"])
    with ctrl_cols[3]:
        col_count = st.selectbox("Layout", ["2 columns", "3 columns"], index=0)
        num_cols  = 2 if col_count == "2 columns" else 3
    return search_query, category_id, sort_option, num_cols


def _render_category_filter(api_url: str, column):
    category_id = None
    try:
        cat_resp = requests.get(f"{api_url}/categories", timeout=10)
        if cat_resp.status_code == 200:
            cats = cat_resp.json()
            options = ["All categories"] + [c['name'] for c in cats]
            with column:
                selected = st.selectbox("Category", options)
            if selected != "All categories":
                category_id = next(c['id'] for c in cats if c['name'] == selected)
    except requests.exceptions.RequestException:
        pass
    return category_id


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

        if sort_option == "Low to High":
            medicines = sorted(medicines, key=lambda x: float(x['price']))
        elif sort_option == "High to Low":
            medicines = sorted(medicines, key=lambda x: float(x['price']), reverse=True)

        if not medicines:
            st.markdown("""
            <div style="text-align:center;padding:4rem 2rem;">
                <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
                <p style="font-size:1.1rem;color:var(--text-secondary);">No medicines found.</p>
                <p style="color:var(--text-muted);">Try a different search or category.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        st.markdown(
            f'<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">'
            f'{len(medicines)} result{"s" if len(medicines)!=1 else ""}</p>',
            unsafe_allow_html=True,
        )

        base_url = api_url.replace('/api', '')
        cols     = st.columns(num_cols)
        for i, med in enumerate(medicines):
            with cols[i % num_cols]:
                _render_medicine_card(api_url, med, base_url)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach backend: {e}")


def _render_medicine_card(api_url: str, med: dict, base_url: str):
    stock = med.get('stock', 0)

    if stock == 0:
        stock_badge = '<span class="badge badge-red">Out of stock</span>'
    elif stock <= 5:
        stock_badge = f'<span class="badge badge-amber">Only {stock} left</span>'
    else:
        stock_badge = '<span class="badge badge-green">In stock</span>'

    rx_badge = '<span class="badge badge-rx">Rx Required</span>&nbsp;' if med.get('requires_prescription') else ''

    st.markdown(f"""
    <div class="med-card">
        <div style="margin-bottom:0.6rem;">{rx_badge}{stock_badge}</div>
        <p class="med-card-name">{med['name']}</p>
        <p class="med-card-price">&#8377;{med['price']}</p>
    </div>
    """, unsafe_allow_html=True)

    if med.get('image'):
        st.image(f"{base_url}/media/{med['image']}", use_container_width=True)

    if stock == 0:
        st.button("Add to cart", key=f"med_{med['id']}", disabled=True, use_container_width=True)
    else:
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
    st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)


def _add_to_cart(med: dict, stock: int):
    for item in st.session_state.cart:
        if item["medicine_id"] == med['id']:
            if item["quantity"] < stock:
                item["quantity"] += 1
                st.toast(f"Added another {med['name']}", icon="✅")
            else:
                st.toast(f"Only {stock} in stock!", icon="⚠️")
            return
    st.session_state.cart.append({
        "medicine_id": med['id'],
        "name":        med['name'],
        "quantity":    1,
        "price":       float(med['price']),
        "requires_rx": med.get('requires_prescription', False),
    })
    st.toast(f"{med['name']} added to cart", icon="✅")


def _render_inline_reviews(api_url: str, med: dict):
    with st.expander("Reviews"):
        try:
            rev_resp = requests.get(f"{api_url}/medicines/{med['id']}/reviews", timeout=10)
            if rev_resp.status_code == 200:
                reviews = rev_resp.json()
                if not reviews:
                    st.markdown('<p style="color:var(--text-muted);font-size:0.85rem;">No reviews yet.</p>',
                                unsafe_allow_html=True)
                else:
                    avg = sum(r['rating'] for r in reviews) / len(reviews)
                    st.markdown(
                        f'<p style="color:var(--text-secondary);font-size:0.9rem;">'
                        f'{"⭐"*round(avg)} <strong style="color:var(--text-primary)">{avg:.1f}</strong>'
                        f'<span style="color:var(--text-muted)"> / 5 ({len(reviews)} reviews)</span></p>',
                        unsafe_allow_html=True,
                    )
                    for r in reviews[:3]:
                        st.markdown(
                            f'<div style="padding:0.5rem 0;border-bottom:1px solid var(--border);">'
                            f'<span style="font-weight:600;font-size:0.85rem;color:var(--text-primary);">'
                            f'{r["customer_name"]}</span> '
                            f'<span style="font-size:0.8rem;">{"⭐"*r["rating"]}</span><br>'
                            f'<span style="font-size:0.82rem;color:var(--text-secondary);">'
                            f'{r.get("comment","")}</span></div>',
                            unsafe_allow_html=True,
                        )
        except requests.exceptions.RequestException:
            st.warning("Could not load reviews.")

        if st.session_state.user:
            with st.form(key=f"review_form_{med['id']}"):
                rating  = st.slider("Your rating", 1, 5, 5)
                comment = st.text_area("Comment (optional)", max_chars=2000)
                if st.form_submit_button("Submit review", use_container_width=True):
                    try:
                        requests.post(
                            f"{api_url}/medicines/{med['id']}/reviews",
                            json={"customer_name": st.session_state.user.get('name', 'User'),
                                  "rating": rating, "comment": comment},
                            timeout=10,
                        )
                        st.toast("Review submitted!", icon="✅")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not submit: {e}")
        else:
            st.markdown('<p style="font-size:0.82rem;color:var(--text-muted);">Log in to leave a review.</p>',
                        unsafe_allow_html=True)
