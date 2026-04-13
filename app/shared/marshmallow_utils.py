"""
Shared Marshmallow Utilities
Helpers used across all service modules that validate with Marshmallow.

Why a shared module:
  _flatten_errors() was duplicated in AuthService, SupportService, and any
  other service that uses Marshmallow validation. Duplicated code means bug
  fixes must be applied in multiple places — easy to miss one.

  Centralizing here means every service calls the same function and any
  future improvements (new field types, better formatting) apply everywhere.
"""


def flatten_errors(messages: dict) -> str:
    """
    Flatten Marshmallow's nested ValidationError.messages dict into one
    human-readable string safe to pass directly to flash().

    Examples:
        Input:  {'email': ['Not a valid email.'], 'password': ['Too short.']}
        Output: 'Email: Not a valid email. — Password: Too short.'

        Input:  {'address': {'city': ['Required.']}}
        Output: 'Address city: Required.'

    Args:
        messages: The .messages dict from a caught ValidationError.

    Returns:
        A single flat string. Falls back to a generic message if input is empty.
    """
    parts = []
    for field, errors in messages.items():
        label = field.replace("_", " ").capitalize()
        if isinstance(errors, list):
            parts.append(f"{label}: {' '.join(str(e) for e in errors)}")
        elif isinstance(errors, dict):
            for subfield, suberrors in errors.items():
                sub_label = f"{label} {subfield}"
                parts.append(f"{sub_label}: {' '.join(str(e) for e in suberrors)}")
    return " — ".join(parts) if parts else "Please check your input and try again."