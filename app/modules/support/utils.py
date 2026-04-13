# Email validation is already handled by the Marshmallow schema using
# the shared EMAIL_REGEX from auth/schema.py.
# This file retains only support-specific helpers.


def sanitize_message(text: str) -> str:
    """
    Basic text sanitization for support form inputs.

    Steps:
    1. Strip leading/trailing whitespace
    2. Collapse multiple internal newlines to max 2 (prevents message spam)

    Does NOT strip HTML — that should be handled at the template render layer
    using Jinja2's auto-escaping (enabled by default in Flask).

    Args:
        text: Raw user input string

    Returns:
        Cleaned string safe for DB storage
    """
    import re
    text = text.strip()
    # Collapse 3+ consecutive newlines to 2 — preserves paragraphs but prevents abuse
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text
