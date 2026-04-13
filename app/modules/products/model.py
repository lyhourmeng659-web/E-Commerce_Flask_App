from datetime import datetime, timezone
from app.core.extensions import db
from app.shared.constants import LOW_STOCK_THRESHOLD, DEFAULT_PRODUCT_IMAGE


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    # index=True speeds up title searches (ilike queries in search())
    title = db.Column(db.String(200), nullable=False, index=True)

    # Unique slug for SEO-friendly URLs — indexed for fast lookups
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)

    description = db.Column(db.Text, nullable=True)

    # Numeric(10,2) stores exact decimal values — avoids float precision issues
    # e.g. 49.99 stored as exactly 49.99, not 49.990000000001
    price = db.Column(db.Numeric(10, 2), nullable=False)

    stock = db.Column(db.Integer, nullable=False, default=0)

    # Default image used when no upload is provided
    image = db.Column(
        db.String(255),
        nullable=False,
        default=DEFAULT_PRODUCT_IMAGE
    )

    # lambda ensures a new datetime is evaluated at insert time,
    # not at class definition time (common Python pitfall with mutable defaults)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # FK to categorize — CASCADE means deleting a category deletes its products
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for fast category-based filtering
    )

    # Many-to-one: each product belongs to one category
    category = db.relationship("Category", back_populates="products")

    # One-to-many: a product can appear in many order line items
    order_items = db.relationship(
        "OrderItem",
        back_populates="product",
        lazy="select",
    )

    # DB-level constraint prevents negative stock from being stored
    # even if application-level validation is bypassed
    __table_args__ = (
        db.CheckConstraint("stock >= 0", name="check_stock_non_negative"),
    )

    def __repr__(self):
        return f"<Product {self.title}>"

    # Convenience Properties
    # These centralize business logic so templates and services don't
    # repeat the same conditions scattered throughout the codebase.

    @property
    def is_in_stock(self) -> bool:
        """True if the product has at least 1 unit available."""
        return self.stock > 0

    @property
    def is_low_stock(self) -> bool:
        """
        True if stock is above 0 but below LOW_STOCK_THRESHOLD.
        Used to show a 'Low Stock' warning badge in templates and admin.
        """
        return 0 < self.stock < LOW_STOCK_THRESHOLD

    @property
    def formatted_price(self) -> str:
        """
        Returns price as a formatted currency string (e.g. '$49.99').
        Centralizes formatting so templates use {{ product.formatted_price }}
        instead of repeating ${{ "%.2f"|format(product.price) }} everywhere.
        """
        return f"${self.price:.2f}"
