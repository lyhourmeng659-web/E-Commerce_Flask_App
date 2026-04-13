import os
import uuid
from flask import current_app
from app.shared.constants import DEFAULT_PRODUCT_IMAGE


def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed image extension.
    Reads allowed extensions from Flask app config (set from constants).

    Use rsplit with max split=1 to handle filenames with multiple dots
    (e.g. 'my.product.image.jpg' → extension is 'jpg').
    """
    return (
            "." in filename and
            filename.rsplit(".", 1)[1].lower()
            in current_app.config.get("ALLOWED_EXTENSIONS", set())
    )


def save_product_image(file) -> str:
    """
    Validate and save an uploaded product image to disk.

    Process:
    1. Return default image path if no file or empty filename provided
    2. Validate file extension against allowed types
    3. Generate a UUID-based filename to prevent collisions and path traversal
    4. Save to the configured UPLOAD_FOLDER
    5. Return the relative path stored in the DB (relative to /static)

    Args:
        file: FileStorage object from request. Files

    Returns:
        Relative image path string (e.g. 'uploads/products/abc123.jpg')

    Raises:
        ValueError: If the file extension is not allowed
    """
    if not file or not file.filename:
        return DEFAULT_PRODUCT_IMAGE

    if not allowed_file(file.filename):
        raise ValueError(
            "Invalid image format. Allowed types: PNG, JPG, JPEG, WEBP."
        )

    # UUID hex prevents filename collisions and path traversal attacks
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_path = current_app.config["UPLOAD_FOLDER"]

    # Ensure upload directory exists — won't error if already present
    os.makedirs(upload_path, exist_ok=True)

    full_path = os.path.join(upload_path, unique_name)
    file.save(full_path)

    return f"uploads/products/{unique_name}"


def calculate_discount(original_price: float, percent: float) -> float:
    """
    Calculate a discounted price given a percentage off.

    Args:
        original_price: The original product price
        percent: Discount percentage (0-100)

    Returns:
        Discounted price as a float

    Example:
        calculate_discount(100.00, 20) → 80.00
    """
    if not (0 <= percent <= 100):
        raise ValueError("Discount percent must be between 0 and 100.")
    return round(original_price - (original_price * percent / 100), 2)
