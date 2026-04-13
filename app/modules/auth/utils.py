import secrets
from flask_login import login_user, logout_user
from app.modules.auth.model import User


def login_user_session(user: User, remember: bool = False) -> None:
    """
    Log in a user via Flask-Login session.

    Args:
        user:     Authenticated User model instance
        remember: If True, set a persistent cookie (remember me)

    Flask-Login stores the user ID in the session cookie.
    On subsequent requests, load_user() in create_app() reloads
    the full User object from the DB using this ID.
    """
    login_user(user, remember=remember)


def logout_user_session() -> None:
    """
    Clear the current user's Flask-Login session.
    Removes the user ID from the session cookie.
    """
    logout_user()


def generate_verification_token() -> str:
    """
    Generate a cryptographically secure random token for email verification.

    Uses secrets.token_hex() instead of uuid4().hex:
    - secrets module is designed specifically for security tokens
    - uuid4 is random but not guaranteed cryptographically secure in all environments
    - 32 bytes = 64 hex chars — sufficient entropy to prevent brute-force guessing

    Returns:
        64-character hex string
    """
    return secrets.token_hex(32)


def generate_refresh_token() -> str:
    """
    Generate a secure opaque refresh token for session management.
    Same security properties as generate_verification_token().
    """
    return secrets.token_hex(32)


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure password reset token.

    Same mechanism as verification token — 32 bytes of randomness.
    Token is stored in User.reset_token and expires after 1 hour
    (check via User.reset_token_expiry in AuthService.reset_password()).

    Never reuse verification tokens for password reset — separate columns
    prevent a reset link from accidentally verifying an email or vice versa.
    """
    return secrets.token_hex(32)
