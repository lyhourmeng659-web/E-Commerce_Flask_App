from decimal import Decimal
from app.shared.constants import FREE_SHIPPING_THRESHOLD, SHIPPING_COST


def calculate_shipping(subtotal: Decimal) -> Decimal:
    """
    Calculate shipping fee based on order subtotal.

    Rules:
    - Orders at or above FREE_SHIPPING_THRESHOLD → free shipping ($0.00)
    - Orders below threshold → flat SHIPPING_COST fee

    Args:
        subtotal: Cart subtotal as Decimal (must be >= 0)

    Returns:
        Shipping fee as Decimal

    Why Decimal?
        Avoid floating precision errors in money calculations.
        e.g. Decimal("2000.00") >= Decimal("2000.00") is always True,
        whereas floats can introduce tiny rounding errors.
    """
    subtotal = max(subtotal, Decimal("0.00"))

    if subtotal >= Decimal(str(FREE_SHIPPING_THRESHOLD)):
        return Decimal("0.00")

    return Decimal(str(SHIPPING_COST))


def format_cart_price(value) -> str:
    """
    Format a Decimal cart value as a display currency string.
    Used in templates via context or passed through service.

    Example:
        format_cart_price(Decimal("49.90")) → "$49.90"
    """
    return f"${Decimal(str(value)):.2f}"
