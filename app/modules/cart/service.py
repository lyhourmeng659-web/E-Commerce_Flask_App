from decimal import Decimal
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app.core.extensions import db
from app.modules.products.model import Product
from app.modules.cart.model import CartItem
from app.modules.cart.utils import calculate_shipping


class CartService:
    """
    Service layer for all cart operations.
    All methods operate on the currently authenticated user's cart
    via Flask-Login's current_user.
    """

    @staticmethod
    def get_item(product_id: int) -> CartItem | None:
        """
        Fetch a single cart item for the current user by product ID.
        Returns None if not found.
        Used internally and by checkout to validate items before order creation.
        """
        return CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
        ).first()

    @staticmethod
    def add_item(product_id: int, quantity: int = 1) -> None:
        """
        Add a product to the current user's cart, or increase quantity if already present.

        Validation:
        - quantity must be > 0
        - product must exist and be in stock
        - combined quantity (existing + new) must not exceed available stock

        Use the UniqueConstraint on (user_id, product_id) — we update
        existing rows rather than inserting duplicates.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be at least 1.")

        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")

        if product.stock <= 0:
            raise ValueError("This product is out of stock.")

        existing = CartService.get_item(product_id)
        new_quantity = (existing.quantity + quantity) if existing else quantity

        if new_quantity > product.stock:
            available = product.stock - (existing.quantity if existing else 0)
            raise ValueError(
                f"Only {available} more unit(s) available for this product."
            )

        if existing:
            existing.quantity = new_quantity
        else:
            db.session.add(CartItem(
                user_id=current_user.id,
                product_id=product_id,
                quantity=quantity,
            ))

        db.session.commit()

    @staticmethod
    def update_item(product_id: int, quantity: int) -> None:
        """
        Update the quantity of a cart item.

        - quantity <= 0 → removes the item entirely
        - quantity > stock → raises ValueError
        - otherwise → updates quantity

        Raises ValueError if item not found (prevents silent failures).
        """
        item = CartService.get_item(product_id)
        if not item:
            raise ValueError("Item not found in cart.")

        if quantity <= 0:
            # Treat quantity 0 as a remove action
            db.session.delete(item)
        elif quantity > item.product.stock:
            raise ValueError(
                f"Only {item.product.stock} unit(s) available."
            )
        else:
            item.quantity = quantity

        db.session.commit()

    @staticmethod
    def remove_item(product_id: int) -> None:
        """
        Remove a specific product from the current user's cart.
        Silently does nothing if item doesn't exist (idempotent).
        """
        item = CartService.get_item(product_id)
        if item:
            db.session.delete(item)
            db.session.commit()

    @staticmethod
    def clear_cart() -> None:
        """
        Remove all items from the current user's cart.
        Uses bulk delete — efficient for clearing many rows at once.
        SQLAlchemy cascade events are bypassed, which is fine here
        since we're intentionally deleting all cart rows directly.
        """
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

    @staticmethod
    def get_cart_count() -> int:
        """
        Return total number of units in the current user's cart.
        Uses SQL SUM for efficiency — avoid loading all cart rows.
        Returns 0 for unauthenticated users or empty carts.
        Called on every page via context processor in create_app().
        """
        if not current_user.is_authenticated:
            return 0

        result = db.session.query(
            db.func.sum(CartItem.quantity)
        ).filter_by(user_id=current_user.id).scalar()

        return int(result) if result else 0

    @staticmethod
    def get_details() -> dict:
        """
        Build the complete cart summary for the cart page and checkout.

        Process:
        1. Load all cart items with products eagerly (joined load avoids N+1)
        2. Compute subtotal using Decimal arithmetic (exact money math)
        3. Calculate shipping based on subtotal threshold
        4. Return structured dict used by cart.html template

        Returns dict with keys:
            items:    list of dicts with product, quantity, subtotal
            subtotal: Decimal — sum of all line items
            shipping: Decimal — flat fee or 0 if above threshold
            total:    Decimal — subtotal + shipping
            count:    int — total number of unique items
        """
        items = (
            CartItem.query
            .options(joinedload(CartItem.product))
            .filter_by(user_id=current_user.id)
            .order_by(CartItem.created_at.asc())
            .all()
        )

        if not items:
            return {
                "items": [],
                "subtotal": Decimal("0.00"),
                "shipping": Decimal("0.00"),
                "total": Decimal("0.00"),
                "count": 0,
            }

        cart_items = []
        subtotal = Decimal("0.00")

        for item in items:
            # Use the model's subtotal property for consistent calculation
            item_subtotal = item.subtotal
            subtotal += item_subtotal
            cart_items.append({
                "product": item.product,
                "quantity": item.quantity,
                "subtotal": item_subtotal,
            })

        shipping = calculate_shipping(subtotal)
        total = subtotal + shipping

        return {
            "items": cart_items,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
            "count": len(cart_items),
        }
