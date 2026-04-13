from app.shared.helpers import generate_slug

def normalize_name(name: str) -> str:
    """
    Clean and standardize a category name for consistent storage.

    Steps:
    1. Strip leading/trailing whitespace
    2. Collapse multiple internal spaces into one (e.g. "gaming  laptops" → "gaming laptops")
    3. Title-case the result (e.g. "gaming laptops" → "Gaming Laptops")

    Usage:
        normalize_name("  gaming  laptops  ") → "Gaming Laptops"
    """
    import re
    name = name.strip()
    name = re.sub(r"\s+", " ", name)  # Collapse internal whitespace
    return name.title()
