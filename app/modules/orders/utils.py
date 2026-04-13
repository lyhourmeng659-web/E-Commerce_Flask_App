from decimal import Decimal
from app.shared.helpers import to_decimal


def calculate_order_total(subtotal, shipping) -> Decimal:
    """
    Calculate the final order total from subtotal and shipping fee.

    Both inputs are converted via to_decimal() which safely handles
    int, float, str, and Decimal inputs — preventing type errors from
    mixed numeric types arriving from cart service or form data.

    Args:
        subtotal: Cart subtotal (any numeric type)
        shipping: Shipping fee (any numeric type)

    Returns:
        Exact Decimal total — safe for DB storage and display.

    Example:
        calculate_order_total("49.90", "5.00") → Decimal("54.90")
    """
    return to_decimal(subtotal) + to_decimal(shipping)


def validate_checkout_data(data: dict) -> dict:
    """
    Validate and sanitize checkout form data before order creation.

    Strips whitespace from all fields, checks required fields are present,
    and builds the customer_name from first + last name.

    Args:
        data: Raw form data dict (from request.form)

    Returns:
        Cleaned dict ready to pass to OrderService.create_order()

    Raises:
        ValueError: With a descriptive message listing missing fields
    """
    # Strip all string values
    cleaned = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.items()
    }

    required = [
        "first_name", "last_name", "email",
        "address", "city", "country",
        "zip_code", "payment_method",
    ]

    missing = [f for f in required if not cleaned.get(f)]
    if missing:
        # Format field names for readable error: first_name → First Name
        labels = [f.replace("_", " ").title() for f in missing]
        raise ValueError(f"Required fields missing: {', '.join(labels)}")

    # Combine first + last name into single customer_name for storage
    cleaned["name"] = f"{cleaned['first_name']} {cleaned['last_name']}"

    return cleaned