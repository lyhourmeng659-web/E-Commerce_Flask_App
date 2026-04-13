from datetime import datetime, timezone
from decimal import Decimal
from app.core.extensions import db
from app.shared.constants import OrderStatus


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    # Human-readable order reference shown to customers (e.g. ORD-A3F2B19C04)
    # Indexed for fast lookup in admin and order history queries
    order_number = db.Column(
        db.String(20), unique=True, nullable=False, index=True
    )

    # FK to users table — allows querying all orders for a user efficiently
    # Nullable for potential guest checkout support in future
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Snapshot of customer info at time of order — stored independently
    # so changing user profile doesn't alter historical order records
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False, index=True)

    # Shipping address — snapshot at order time
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)

    # Payment method stored as string for flexibility
    # Indexed for filtering orders by payment type in admin
    payment_method = db.Column(db.String(50), nullable=False, index=True)

    # Stored as Numeric(10,2) for exact decimal money arithmetic
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # OrderStatus enum value stored as string — indexed for status filtering
    status = db.Column(
        db.String(50),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )

    # Indexed for sorting orders by date in admin and user history
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # One order has many line items
    # cascade="all, delete-orphan": deleting order deletes its items
    # back_populates mirrors OrderItem.order relationship
    # lazy="selectin": loads all items in a second query (efficient for lists)
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Many-to-one: order belongs to a user
    user = db.relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order #{self.order_number} status={self.status}>"

    @property
    def subtotal(self) -> Decimal:
        """
        Compute subtotal by subtracting shipping from total.
        Stored as a derived value — avoids storing redundant data
        while keeping the template clean.
        """
        return Decimal(str(self.total_amount)) - Decimal(str(self.shipping_amount))

    @property
    def is_free_shipping(self) -> bool:
        """True if no shipping was charged on this order."""
        return self.shipping_amount == 0

    @property
    def formatted_total(self) -> str:
        return f"${self.total_amount:.2f}"

    @property
    def formatted_shipping(self) -> str:
        return "FREE" if self.is_free_shipping else f"${self.shipping_amount:.2f}"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,  # Nullable: product may be deleted but order history preserved
    )

    # Snapshot of product name at the time of order
    # Stored so invoice stays accurate even if product title changes later
    product_name = db.Column(db.String(150), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    # Snapshot of price at time of order — preserves historical accuracy
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # back_populates mirrors Product.order_items
    product = db.relationship("Product", back_populates="order_items")

    # Mirrors Order.items
    order = db.relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"

    @property
    def subtotal(self) -> Decimal:
        """
        Line item total = unit price × quantity.
        Decimal arithmetic ensures exact money calculation.
        Used in invoice template: {{ item.subtotal }} instead of
        computing price * quantity in the template itself.
        """
        return Decimal(str(self.price)) * self.quantity
