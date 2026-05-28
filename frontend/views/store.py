# frontend/views/store.py
import streamlit as st
import requests
from config import API_URL, BACKEND_MEDIA, WHATSAPP_NUMBER
from helpers import add_to_cart, stars


def render():
    _hero()
    _medicine_grid()


# ─── Hero ──────────────────────────────────────────────────────────────────────

def _hero():
    st.markdown(f"""
    <div class="hero">
        <div class="hero-eyebrow">✦ MediCare Local Pharmacy</div>
        <div class="hero-title">Your Health,<br><span>Delivered Fast</span></div>
        <div class="hero-sub">
            Genuine medicines sourced directly from certified distributors.<br>
            No advance payment — pay cash on delivery at your door.
        </div>
        <a class="wa-btn" href="https://wa.me/{WHATSAPP_NUMBER}?text=Hi,%20I%20need%20help" target="_blank">
            💬 &nbsp;WhatsApp Support
        </a>
        <div class="hero-chips">
            <span class="hero-chip green">✓ &nbsp;Free Delivery</span>
            <span class="hero-chip blue">⚡ Same Day Dispatch</span>
            <span class="hero-chip gold">💵 Cash on Delivery</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Filter bar + grid ─────────────────────────────────────────────────────────

def _medicine_grid():
    if "search_suggestions" not in st.session_state:
        st.session_state.search_suggestions = []
    if "search_selected" not in st.session_state:
        st.session_state.search_selected = ""

    # ── Filter bar ──
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])

    with fc1:
        search_input = st.text_input(
            "Search",
            value=st.session_state.search_selected,
            placeholder="🔍  Search medicines, brands…",
            label_visibility="collapsed",
            key="store_search",
        )
        # Fetch suggestions
        if search_input and len(search_input.strip()) >= 2:
            if search_input != st.session_state.search_selected:
                try:
                    r = requests.get(
                        f"{API_URL}/medicines",
                        params={"search": search_input.strip()},
                        timeout=4,
                    )
                    if r.ok:
                        results = r.json()
                        seen = set()
                        suggestions = []
                        for m in results:
                            label = m["name"]
                            if m.get("brand"):
                                label += f"  ·  {m['brand']}"
                            if m["name"] not in seen:
                                seen.add(m["name"])
                                suggestions.append({
                                    "label": label,
                                    "name":  m["name"],
                                    "price": m["price"],
                                    "stock": m["stock"],
                                })
                        st.session_state.search_suggestions = suggestions[:6]
                    else:
                        st.session_state.search_suggestions = []
                except requests.exceptions.RequestException:
                    st.session_state.search_suggestions = []
        else:
            st.session_state.search_suggestions = []

        # Suggestion dropdown
        suggestions = st.session_state.search_suggestions
        if suggestions and search_input != st.session_state.search_selected:
            st.markdown('<div class="sugg-box">', unsafe_allow_html=True)
            for i, s in enumerate(suggestions):
                stock = s["stock"]
                stock_color = "#34d399" if stock > 5 else ("#f59e0b" if stock > 0 else "#f87171")
                stock_text  = "In stock" if stock > 5 else (f"Only {stock} left" if stock > 0 else "Out of stock")
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                     padding:10px 16px;border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer;">
                  <div>
                    <span style="font-size:.86rem;font-weight:700;color:#f1f5f9;">{s['name']}</span>
                    {'<span style="font-size:.7rem;color:#38bdf8;margin-left:8px;">' + s['label'].split('·')[-1].strip() + '</span>' if '·' in s['label'] else ''}
                  </div>
                  <div style="text-align:right;flex-shrink:0;margin-left:12px">
                    <span style="font-size:.85rem;font-weight:700;color:#f59e0b;">₹{s['price']}</span>
                    <span style="font-size:.66rem;color:{stock_color};margin-left:7px;">{stock_text}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(s["name"], key=f"sugg_btn_{i}_{s['name']}", width='stretch'):
                    st.session_state.search_selected = s["name"]
                    st.session_state.search_suggestions = []
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("✕  Clear", key="clear_search"):
                st.session_state.search_selected = ""
                st.session_state.search_suggestions = []
                st.rerun()

    with fc3:
        sort = st.selectbox(
            "Sort", ["Default", "Price: Low → High", "Price: High → Low"],
            label_visibility="collapsed", key="store_sort",
        )
    with fc4:
        layout = st.selectbox(
            "Layout", ["2 col", "3 col"],
            label_visibility="collapsed", key="store_layout",
        )

    # Category filter
    category_id = None
    try:
        cat_resp = requests.get(f"{API_URL}/categories", timeout=8)
        if cat_resp.ok:
            cats = cat_resp.json()
            with fc2:
                sel = st.selectbox(
                    "Category",
                    ["All categories"] + [c["name"] for c in cats],
                    label_visibility="collapsed", key="store_cat",
                )
            if sel != "All categories":
                category_id = next(c["id"] for c in cats if c["name"] == sel)
    except requests.exceptions.RequestException:
        pass

    st.markdown("</div>", unsafe_allow_html=True)  # close filter-bar

    # ── Fetch medicines ──
    active_search = st.session_state.search_selected or search_input
    try:
        params = {}
        if active_search:  params["search"]      = active_search
        if category_id:    params["category_id"] = category_id

        resp = requests.get(f"{API_URL}/medicines", params=params, timeout=10)
        if not resp.ok:
            st.error("Could not load medicines.")
            return
        meds = resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach backend: {e}")
        return

    if sort == "Price: Low → High":
        meds = sorted(meds, key=lambda x: float(x["price"]))
    elif sort == "Price: High → Low":
        meds = sorted(meds, key=lambda x: float(x["price"]), reverse=True)

    if not meds:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#334155;">
            <div style="font-size:3rem;margin-bottom:1rem;opacity:.3">🔍</div>
            <div style="font-size:1rem;font-weight:600;color:#475569;margin-bottom:.4rem">No medicines found</div>
            <div style="font-size:.82rem;color:#334155">Try a different search or category</div>
        </div>
        """, unsafe_allow_html=True)
        return

    count = len(meds)
    st.markdown(
        f'<div class="result-pill"><span>{count}</span> medicine{"s" if count != 1 else ""} found</div>',
        unsafe_allow_html=True
    )

    n_cols = 2 if layout == "2 col" else 3
    cols   = st.columns(n_cols, gap="medium")
    for i, med in enumerate(meds):
        with cols[i % n_cols]:
            _med_card(med)


# ─── Medicine card ─────────────────────────────────────────────────────────────

def _med_card(med: dict):
    stock = med.get("stock", 0)

    st.markdown('<div class="med-card">', unsafe_allow_html=True)

    # ── Image ──
    if med.get("image"):
        st.markdown('<div class="med-img-wrap">', unsafe_allow_html=True)
        st.image(f"{BACKEND_MEDIA}/{med['image']}", width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="med-img-wrap">
            <div class="med-img-placeholder">
                <div class="med-img-placeholder-icon">💊</div>
                <div class="med-img-placeholder-text">No Image</div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Body ──
    st.markdown('<div class="med-body">', unsafe_allow_html=True)

    if med.get("brand"):
        st.markdown(
            f'<div class="med-brand">{med["brand"].upper()}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="med-name">{med["name"]}</div>',
        unsafe_allow_html=True,
    )

    # Description snippet
    if med.get("description"):
        desc = med["description"][:90] + ("…" if len(med.get("description","")) > 90 else "")
        st.markdown(f'<div class="med-desc-short">{desc}</div>', unsafe_allow_html=True)

    # Price
    st.markdown(f"""
    <div class="med-price-row">
        <span class="med-price">₹{med['price']}</span>
        <span class="med-price-unit">/ unit</span>
    </div>""", unsafe_allow_html=True)

    # Badges
    if stock == 0:
        badge = '<span class="badge-out">Out of stock</span>'
    elif stock <= 5:
        badge = f'<span class="badge-low">Only {stock} left</span>'
    else:
        badge = '<span class="badge-instock">In stock</span>'

    rx_tag = ' &nbsp;<span class="badge-rx">⚕ Rx</span>' if med.get("requires_prescription") else ""
    st.markdown(f'<div class="med-badges">{badge}{rx_tag}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close med-body

    # ── Footer buttons ──
    st.markdown('<div class="med-footer">', unsafe_allow_html=True)
    if stock == 0:
        st.button("Add to cart", key=f"add_{med['id']}", disabled=True, width='stretch')
        if st.button("View Details →", key=f"det_{med['id']}", width='stretch'):
            _open_detail(med["id"])
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🛒 Add to cart", key=f"add_{med['id']}", type="primary", width='stretch'):
                new_cart, msg = add_to_cart(med, st.session_state.cart)
                st.session_state.cart = new_cart
                st.toast(msg)
        with b2:
            if st.button("Details →", key=f"det_{med['id']}", width='stretch'):
                _open_detail(med["id"])
    st.markdown("</div>", unsafe_allow_html=True)  # close med-footer

    st.markdown("</div>", unsafe_allow_html=True)  # close med-card

    # ── Reviews expander ──
    with st.expander("⭐ Reviews"):
        _inline_reviews(med)


def _open_detail(med_id: int):
    st.session_state.show_medicine_detail = True
    st.session_state.selected_medicine_id = med_id
    st.rerun()


def _inline_reviews(med: dict):
    try:
        if "page" not in st.session_state:
            st.session_state.page = 1

        r = requests.get(
            f"{API_URL}/medicines",
            params={
                "category_id": category_id,
                "search": search_input,
                "page": st.session_state.page,
                "page_size": 40,
            },
            timeout=10,
        )

        data = r.json() if r.ok else {"items": [], "total": 0, "total_pages": 1}
        medicines = data.get("items", [])
        total_pages = data.get("total_pages", 1)
        has_next = data.get("has_next", False)
        has_prev = data.get("has_prev", False)
    except requests.exceptions.RequestException:
        st.caption("Could not load reviews.")
        return

    if not reviews:
        st.caption("No reviews yet.")
    else:
        avg = sum(x["rating"] for x in reviews) / len(reviews)
        st.markdown(
            f"{'⭐' * round(avg)} **{avg:.1f}** / 5 &nbsp;·&nbsp; "
            f"{len(reviews)} review{'s' if len(reviews) != 1 else ''}"
        )
        for rv in reviews[:3]:
            st.markdown(f"**{rv['customer_name']}** {'⭐' * rv['rating']}")
            if rv.get("comment"):
                st.caption(rv["comment"])

    if st.session_state.user:
        with st.form(key=f"rv_form_{med['id']}"):
            rating  = st.slider("Rating", 1, 5, 5)
            comment = st.text_area("Your experience (optional)", height=70)
            if st.form_submit_button("Submit review"):
                try:
                    requests.post(
                        f"{API_URL}/medicines/{med['id']}/reviews",
                        json={
                            "customer_name": st.session_state.user.get("name", "User"),
                            "rating":  rating,
                            "comment": comment,
                        },
                        timeout=10,
                    )
                    st.success("Review submitted!")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not submit: {e}")
    else:
        st.caption("Log in to leave a review.")
