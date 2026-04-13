from datetime import datetime, timezone
from app.core.extensions import db


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(db.Integer, primary_key=True)

    # Indexed — queried on every page via context processor (count + is_in_wishlist)
    # CASCADE: deleting user removes their wishlist rows automatically at DB level
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # CASCADE: deleting product removes it from all wishlists automatically
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # back_populates mirrors User.wishlist_items defined in auth model
    user = db.relationship(
        "User",
        back_populates="wishlist_items",
    )

    # back_populates mirrors any Product.wishlist_items relationship if defined
    # lazy="joined": always load product alongside wishlist row (avoids N+1)
    product = db.relationship(
        "Product",
        lazy="joined",
    )

    # DB-level constraint: one wishlist entry per user+product pair
    # Prevents duplicates even if service-level check is bypassed
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "product_id",
            name="unique_user_product_wishlist"
        ),
    )

    def __repr__(self):
        return f"<Wishlist user={self.user_id} product={self.product_id}>"
