# frontend/helpers.py
# ─────────────────────────────────────────
# Pure utility functions — NO Streamlit imports.
# ─────────────────────────────────────────
from datetime import datetime, timedelta


def delivery_estimate(created_at_str: str) -> str:
    """Human-readable ETA from an ISO timestamp string."""
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


def stars(rating: float) -> str:
    """Star emojis for a 1-5 rating."""
    return "⭐" * max(1, min(5, round(rating)))


def stock_badge(stock: int) -> str:
    """Return a styled HTML badge string based on stock level."""
    if stock == 0:
        return '<span class="badge-out">Out of stock</span>'
    if stock <= 5:
        return f'<span class="badge-low">Only {stock} left</span>'
    return '<span class="badge-instock">In stock</span>'


def add_to_cart(med: dict, cart: list) -> tuple[list, str]:
    """
    Add medicine to cart or increment quantity.
    Returns (updated_cart, message).
    """
    stock = med.get("stock", 0)
    for item in cart:
        if item["medicine_id"] == med["id"]:
            if item["quantity"] < stock:
                item["quantity"] += 1
                return cart, f"Added another {med['name']}!"
            return cart, f"Only {stock} in stock!"
    cart.append({
        "medicine_id": med["id"],
        "name":        med["name"],
        "quantity":    1,
        "price":       float(med["price"]),
        "requires_rx": med.get("requires_prescription", False),
    })
    return cart, f"Added {med['name']} to cart!"
