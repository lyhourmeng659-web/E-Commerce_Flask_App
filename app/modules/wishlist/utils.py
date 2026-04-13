from flask_login import current_user
from app.core.extensions import db
from app.modules.wishlist.model import Wishlist


def get_wishlist_ids_for_user(user_id: int | None = None) -> set:
    """
    Return a set of product IDs in a user's wishlist.

    Args:
        user_id: Explicit user ID. If None, uses current_user.
                 Pass explicitly when calling outside a request context
                 (e.g. background jobs, tests).

    Returns:
        Set of int product IDs. Empty set for guests or users with
        no wishlist items.

    Performance:
        Single SELECT of product_id column only — no product rows loaded.
        O(1) lookup in templates via `product.id in wishlist_ids`.

    Usage:
        # In a route or service:
        wishlist_ids = get_wishlist_ids_for_user()

        # In a template (injected via context processor):
        {% if product.id in wishlist_ids %}
    """
    uid = user_id or (
        current_user.id if current_user.is_authenticated else None
    )

    if not uid:
        return set()

    rows = db.session.query(Wishlist.product_id).filter_by(
        user_id=uid
    ).all()

    return {row.product_id for row in rows}


def is_product_in_wishlist(product_id: int, user_id: int | None = None) -> bool:
    """
    Check if a single product is in a user's wishlist.

    Prefer get_wishlist_ids_for_user() when checking multiple products
    on one page — it avoids N+1 queries.

    Use this only when checking a single product (e.g. product detail page).

    Args:
        product_id: The product to check.
        user_id:    Explicit user ID. Defaults to current_user.

    Returns:
        True if in wishlist, False otherwise (including for guests).
    """
    uid = user_id or (
        current_user.id if current_user.is_authenticated else None
    )

    if not uid:
        return False

    return Wishlist.query.filter_by(
        user_id=uid,
        product_id=product_id,
    ).first() is not None


def format_wishlist_count(count: int) -> str:
    """
    Return a human-readable wishlist count string.

    Examples:
        0  → "0 items"
        1  → "1 item"
        12 → "12 items"

    Used in wishlist page footer and admin dashboard.
    """
    return f"{count} item{'s' if count != 1 else ''}"
