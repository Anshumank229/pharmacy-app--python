import requests
import streamlit as st
from datetime import datetime, timedelta


def delivery_estimate(created_at_str: str) -> str:
    """Return a human-readable delivery ETA based on order creation time."""
    try:
        created = datetime.fromisoformat(created_at_str)
        eta     = created + timedelta(hours=24)
        now     = datetime.now(tz=created.tzinfo)
        if eta > now:
            hrs = int((eta - now).total_seconds() // 3600)
            return f"Expected within ~{hrs} hrs"
        return "Expected: any moment now"
    except Exception:
        return "Expected within 24 hrs"


def reorder(order: dict, api_url: str):
    """
    Add all items from a past order back into the cart.
    Checks current stock before adding.
    Returns (added: list[str], skipped: list[str]).
    """
    added   = []
    skipped = []

    for item in order.get('items', []):
        med_name = item['medicine']['name']
        qty      = item['quantity']

        try:
            search_resp = requests.get(
                f"{api_url}/medicines",
                params={"search": med_name},
                timeout=5,
            )
            if search_resp.status_code != 200:
                skipped.append(f"{med_name} (could not load)")
                continue

            results = search_resp.json()
            med = next((m for m in results if m['name'] == med_name), None)
            if not med:
                skipped.append(f"{med_name} (not found)")
                continue

            stock = med.get('stock', 0)
            if stock == 0:
                skipped.append(f"{med_name} (out of stock)")
                continue

            qty_to_add = min(qty, stock)
            item_found = False
            for cart_item in st.session_state.cart:
                if cart_item["medicine_id"] == med['id']:
                    new_qty = cart_item["quantity"] + qty_to_add
                    cart_item["quantity"] = min(new_qty, stock)
                    item_found = True
                    break

            if not item_found:
                st.session_state.cart.append({
                    "medicine_id": med['id'],
                    "name":        med['name'],
                    "quantity":    qty_to_add,
                    "price":       float(med['price']),
                    "requires_rx": med.get('requires_prescription', False),
                })

            if qty_to_add < qty:
                added.append(f"{med_name} ×{qty_to_add} (only {stock} in stock)")
            else:
                added.append(f"{med_name} ×{qty_to_add}")

        except requests.exceptions.RequestException:
            skipped.append(f"{med_name} (connection error)")

    return added, skipped
