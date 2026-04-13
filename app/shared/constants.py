from enum import Enum

# Pagination
# Default values used across all paginated queries in services.
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10

# Products
# Threshold below which a product is considered "low stock" and
# triggers a warning badge in admin and product detail views.
LOW_STOCK_THRESHOLD = 5

# Fallback image path (relative to /static) used when a product
# has no uploaded image. Rendered via: url_for('static', filename=...)
DEFAULT_PRODUCT_IMAGE = "uploads/products/default.png"

# File Uploads
# Allowed image extensions for product photo uploads.
# Used in helpers.allowed_file() and registered in Flask app config.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Shipping
# Orders above this total qualify for free shipping.
FREE_SHIPPING_THRESHOLD = 200

# Flat shipping fee applied to orders below the FREE_SHIPPING_THRESHOLD.
SHIPPING_COST = 5.00

# Currency
CURRENCY_SYMBOL = "$"

# Password Validation Rules
# Used in shared/helpers.py validate_password() and register forms.
MIN_PASSWORD_LENGTH = 6
MAX_NAME_LENGTH = 120
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True


# Order Status
class OrderStatus(str, Enum):
    """
    Enum for all possible order lifecycle states.
    Inherits from str so values can be stored directly in the DB
    as strings and compared with == without calling .value.
    """
    PENDING = "PENDING"  # Order placed, awaiting payment
    PAID = "PAID"  # Payment confirmed
    SHIPPED = "SHIPPED"  # Package dispatched
    DELIVERED = "DELIVERED"  # Package received by customer
    CANCELLED = "CANCELLED"  # Order canceled by user or admin
    REFUNDED = "REFUNDED"  # Payment refunded


# Payment Methods
class PaymentMethod(str, Enum):
    """
    Enum for supported payment methods.
    Stored as strings in DB — same str inheritance pattern as OrderStatus.
    """
    COD = "COD"  # Cash on delivery
    CARD = "CARD"  # Credit/debit card
    PAYPAL = "PAYPAL"  # PayPal checkout
