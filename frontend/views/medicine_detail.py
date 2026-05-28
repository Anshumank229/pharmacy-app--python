# frontend/views/medicine_detail.py
import streamlit as st
import requests
from config import API_URL, BACKEND_MEDIA
from helpers import add_to_cart, stars
from theme import scroll_to_top


def render():
    scroll_to_top()

    med_id = st.session_state.selected_medicine_id
    try:
        resp = requests.get(f"{API_URL}/medicines/{med_id}", timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load medicine: {e}")
        _back_btn()
        return

    if resp.status_code != 200:
        st.error("Medicine not found.")
        _back_btn()
        return

    med   = resp.json()
    stock = med.get("stock", 0)

    # Back button — very first element (page feels top-anchored)
    _back_btn()

    # ── Title block ──
    if med.get("brand"):
        st.caption(med["brand"].upper())

    st.markdown(
        f"<h1 style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;"
        f"color:#f0f9ff;margin:0 0 4px'>{med['name']}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;"
        f"color:#f0b429'>₹{med['price']}</span>",
        unsafe_allow_html=True,
    )

    # Stock + Rx line
    if stock == 0:
        st.error("Out of stock")
    elif stock <= 5:
        st.warning(f"Only {stock} left in stock")
    else:
        st.success(f"In stock — {stock} available")

    if med.get("requires_prescription"):
        st.warning("⚕️ Prescription required for this medicine")

    # Info pills as native columns
    pill_items = []
    if med.get("dosage_form"): pill_items.append(("Form",     med["dosage_form"]))
    if med.get("strength"):    pill_items.append(("Strength", med["strength"]))
    if med.get("category"):    pill_items.append(("Category", med["category"]["name"]))

    if pill_items:
        pill_cols = st.columns(len(pill_items))
        for col, (label, value) in zip(pill_cols, pill_items):
            col.markdown(
                f"<div style='background:rgba(30,41,59,.9);border:1px solid rgba(255,255,255,.08);"
                f"border-radius:8px;padding:7px 12px;font-size:.83rem;color:#cbd5e1'>"
                f"<span style='color:#64748b;font-size:.72rem;display:block;text-transform:uppercase;"
                f"letter-spacing:.08em'>{label}</span>{value}</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Image + description + add-to-cart ──
    img_col, info_col = st.columns([1, 2])

    with img_col:
        if med.get("image"):
            st.image(f"{BACKEND_MEDIA}/{med['image']}", width='stretch')
        else:
            st.markdown(
                "<div style='height:220px;background:linear-gradient(145deg,#1e293b,#0f172a);"
                "border-radius:14px;display:flex;align-items:center;justify-content:center;"
                "color:#334155;font-size:.75rem;letter-spacing:.1em'>NO IMAGE</div>",
                unsafe_allow_html=True,
            )

    with info_col:
        if med.get("description"):
            st.markdown("**About this medicine**")
            st.markdown(
                f"<div style='background:rgba(15,23,42,.5);border:1px solid rgba(255,255,255,.06);"
                f"border-radius:12px;padding:1rem 1.2rem;color:#94a3b8;font-size:.9rem;"
                f"line-height:1.7'>{med['description']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

        if stock > 0:
            if st.button("🛒 Add to cart", type="primary", width='stretch', key="detail_add"):
                new_cart, msg = add_to_cart(med, st.session_state.cart)
                st.session_state.cart = new_cart
                st.toast(msg)
        else:
            st.button("Out of stock", disabled=True, width='stretch')

    st.divider()

    # ── Reviews ──
    _reviews_section(med_id)

    st.markdown("<br>", unsafe_allow_html=True)
    _back_btn(key="back_bottom")


# ── Private helpers ───────────────────────────────────────────────────────────

def _back_btn(key: str = "back_top"):
    if st.button("← Back to store", key=key):
        st.session_state.show_medicine_detail = False
        st.session_state.selected_medicine_id = None
        st.rerun()


def _reviews_section(med_id: int):
    st.markdown("### Reviews & ratings")

    try:
        r       = requests.get(f"{API_URL}/medicines/{med_id}/reviews", timeout=10)
        reviews = r.json() if r.ok else []
    except requests.exceptions.RequestException:
        st.warning("Could not load reviews.")
        reviews = []

    if reviews:
        avg = sum(x["rating"] for x in reviews) / len(reviews)
        st.markdown(
            f"<span style='font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;"
            f"color:#f0f9ff'>{avg:.1f}</span> "
            f"<span style='font-size:1.1rem'>{'⭐'*round(avg)}</span> "
            f"<span style='color:#64748b;font-size:.85rem'>from {len(reviews)} review{'s' if len(reviews)!=1 else ''}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        for rv in reviews:
            with st.container():
                st.markdown(
                    f"<div style='background:rgba(15,23,42,.6);border:1px solid rgba(255,255,255,.06);"
                    f"border-radius:12px;padding:.9rem 1.1rem;margin-bottom:.6rem'>"
                    f"<strong style='color:#e2e8f0'>{rv['customer_name']}</strong> "
                    f"<span style='font-size:.85rem'>{'⭐'*rv['rating']}</span>"
                    + (f"<div style='color:#94a3b8;font-size:.86rem;margin-top:5px'>{rv['comment']}</div>" if rv.get('comment') else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No reviews yet. Be the first!")

    if st.session_state.user:
        st.markdown("#### Leave a review")
        with st.form(key=f"detail_review_{med_id}"):
            rating  = st.slider("Rating", 1, 5, 5)
            comment = st.text_area("Your experience (optional)", height=90)
            if st.form_submit_button("Submit review", type="primary"):
                try:
                    requests.post(
                        f"{API_URL}/medicines/{med_id}/reviews",
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
        st.info("Log in to leave a review.")
