from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from flask_login import current_user

from app.core.extensions import db
from app.modules.products.model import Product
from app.modules.wishlist.model import Wishlist
from app.modules.wishlist.utils import (
    get_wishlist_ids_for_user,
    is_product_in_wishlist,
)


class WishlistService:
    """
    Service layer for all wishlist operations.
    Authentication is enforced at route level via @login_required.
    All methods assume current_user is authenticated when called.
    """

    @staticmethod
    def add(product_id: int) -> bool:
        """
        Add a product to the current user's wishlist.

        Uses IntegrityError as a safety net against race conditions —
        the UniqueConstraint prevents duplicate rows at DB level.

        Returns True if added, False if already in wishlist.
        """
        # Use util for consistent duplicate check logic
        if is_product_in_wishlist(product_id):
            return False

        try:
            db.session.add(Wishlist(
                user_id=current_user.id,
                product_id=product_id,
            ))
            db.session.commit()
            return True

        except IntegrityError:
            # Race condition: another request added it between check and insert
            db.session.rollback()
            return False

    @staticmethod
    def remove(product_id: int) -> bool:
        """
        Remove a product from the current user's wishlist.
        Returns True if removed, False if it wasn't in the wishlist.
        Idempotent — safe to call even if item doesn't exist.
        """
        item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
        ).first()

        if not item:
            return False

        db.session.delete(item)
        db.session.commit()
        return True

    @staticmethod
    def get_all() -> list:
        """
        Return all wishlist items for the current user.

        Uses joinedload chain to prevent N+1 queries:
        - 1 query for wishlist + JOINed product + JOINed category
        Ordered newest first.
        """
        return (
            Wishlist.query
            .options(
                joinedload(Wishlist.product)
                .joinedload(Product.category)
            )
            .filter_by(user_id=current_user.id)
            .order_by(Wishlist.created_at.desc())
            .all()
        )

    @staticmethod
    def count() -> int:
        """
        Return count of items in the current user's wishlist.
        Returns 0 for unauthenticated users.
        Called on every page via context processor.
        """
        if not current_user.is_authenticated:
            return 0

        return Wishlist.query.filter_by(
            user_id=current_user.id
        ).count()

    @staticmethod
    def is_in_wishlist(product_id: int) -> bool:
        """
        Check if a product is in the current user's wishlist.

        For product listing pages with many cards, prefer get_wishlist_ids()
        to batch-load all IDs in one query, then do O(1) set lookups.
        Use this only for single-product pages (e.g. product detail).
        """
        return is_product_in_wishlist(product_id)

    @staticmethod
    def get_wishlist_ids() -> set:
        """
        Return a set of all wishlisted product IDs for the current user.

        Single DB query → O(1) Python set lookups in templates.
        Injected into every template via context processor in __init__.py:
            {% if product.id in wishlist_ids %}

        Returns empty set for guests.
        """
        return get_wishlist_ids_for_user()
