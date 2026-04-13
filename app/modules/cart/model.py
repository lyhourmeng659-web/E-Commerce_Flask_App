from datetime import datetime, timezone
from app.core.extensions import db


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for fast per-user cart queries
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # joinedload-friendly: loading CartItem will also load product in same query
    # avoids N+1 queries when iterating cart items in get_details()
    product = db.relationship(
        "Product",
        lazy="joined",  # Always load product alongside cart item in one JOIN
    )

    # back_populates instead of backref — explicit and consistent with other models
    user = db.relationship(
        "User",
        back_populates="cart_items",
    )

    # DB-level constraint: one row per user+product combination.
    # Prevents duplicate entries — service uses update instead of insert when exists.
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "product_id",
            name="unique_user_cart_product"
        ),
    )

    def __repr__(self):
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"

    @property
    def subtotal(self):
        """
        Compute line item total from product price × quantity.
        Using Decimal arithmetic avoids float precision issues with money.
        Centralizes subtotal logic so templates and service use same calculation.
        """
        from decimal import Decimal
        return Decimal(str(self.product.price)) * self.quantity
