import re
import os
import uuid
from decimal import Decimal, InvalidOperation

from app.shared.constants import CURRENCY_SYMBOL, ALLOWED_EXTENSIONS


# Slug Generation

def generate_slug(text: str) -> str:
    """
    Convert a string into a URL-safe slug.

    Process:
    1. Lowercase the text
    2. Replace any non-alphanumeric characters (except hyphens) with hyphens
    3. Collapse multiple consecutive hyphens into one
    4. Strip leading/trailing hyphens

    Examples:
        "Gaming Laptops!"  → "gaming-laptops"
        "  Hello World  "  → "hello-world"
        "RTX 3080 Ti"      → "rtx-3080-ti"
    """
    text = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", text)  # Remove special chars (keep word chars, spaces, hyphens)
    slug = re.sub(r"[\s_]+", "-", slug)  # Replace spaces/underscores with hyphens
    slug = re.sub(r"-{2,}", "-", slug)  # Collapse multiple hyphens
    return slug.strip("-")


# File Handling

def generate_unique_filename(filename: str) -> str:
    """
    Generate a UUID-based filename while preserving the original extension.

    Uses os.path.splitext() instead of split(".") to correctly handle
    filenames with multiple dots (e.g., "my.product.image.jpg").

    Example:
        "product photo.jpg" → "3f2a1b4c...uuid....jpg"
    """
    _, ext = os.path.splitext(filename)  # Safely extract extension (includes the dot)
    return f"{uuid.uuid4().hex}{ext.lower()}"  # Lowercase extension for consistency


def allowed_file(filename: str) -> bool:
    """
    Check whether a filename has an allowed upload extension.

    Validates against ALLOWED_EXTENSIONS from constants.
    It Also ensures the filename actually has an extension at all.

    Usage in upload routes:
        if not allowed_file(file.filename):
            abort(400)
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


# Currency & Numbers

def format_currency(amount, symbol: str = CURRENCY_SYMBOL) -> str:
    """
    Format a numeric value as a currency string.

    Safely handles int, float, Decimal, and string inputs.
    Falls back to "$0.00" if the value cannot be converted.

    Examples:
        format_currency(49.9)     → "$49.90"
        format_currency(1000)     → "$1000.00"
        format_currency("bad")    → "$0.00"
    """
    try:
        return f"{symbol}{Decimal(str(amount)):.2f}"
    except (InvalidOperation, TypeError):
        return f"{symbol}0.00"


def to_decimal(value) -> Decimal:
    """
    Safely convert any numeric-like value to a Python Decimal.

    Why Decimal instead of float?
    Floats have precision issues with money:
        0.1 + 0.2 == 0.30000000000000004  (float)
        Decimal("0.1") + Decimal("0.2") == Decimal("0.3")  (exact)

    Always convert via str() first to avoid float precision loss.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal("0")


# Order Utilities

def generate_order_number() -> str:
    """
    Generate a unique, human-readable order reference number.

    Format: ORD-XXX... (10 uppercase hex characters)
    Example: ORD-A3F2B19C04

    Using UUID hex ensures uniqueness without needing a DB sequence.
    """
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"
