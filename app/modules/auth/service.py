"""
Auth Service
Handles all authentication business logic:
  - User registration (validation + email verification)
  - Login (credential check + session creation)
  - Email verification (token consumption)
  - Password reset (token generation + application)
  - Logout (session destruction)

All public methods raise ValueError with human-readable messages on failure.
Routes catch ValueError and flash the message to the user — no traceback shown.

Security practices applied:
  - Passwords hashed with Werkzeug's scrypt (industry standard)
  - Email enumeration prevented (forgot-password always shows success)
  - Reset tokens are one-time use, expire in 1 hour
  - Refresh token rotated on every login
  - All sessions invalidated on password reset
"""

import re
from flask import current_app
from marshmallow import ValidationError

from app.core.extensions import db
from app.modules.auth.model import User
from app.modules.auth.schema import RegisterSchema, LoginSchema
from app.shared.marshmallow_utils import flatten_errors
from app.modules.auth.utils import (
    login_user_session,
    logout_user_session,
    generate_verification_token,
    generate_refresh_token,
    generate_reset_token,
)

register_schema = RegisterSchema()
login_schema = LoginSchema()


class AuthService:

    #  Registration

    @staticmethod
    def register(data: dict) -> User:
        """
        Validate form data, create an unverified user, send verification email.

        Flow:
          1. Validate name/email/password via RegisterSchema
          2. Check for duplicate email
          3. Create User with is_verified=False
          4. Generate and store verification token
          5. Send welcome email with clickable verify link
          6. Return the new User object

        Raises:
            ValueError: Validation failure or duplicate email.
        """
        try:
            validated = register_schema.load(data)
        except ValidationError as e:
            raise ValueError(flatten_errors(e.messages))

        if User.query.filter_by(email=validated["email"]).first():
            raise ValueError("This email address is already registered.")

        token = generate_verification_token()
        user = User(
            name=validated["name"],
            email=validated["email"],
            is_verified=False,
            verification_token=token,
        )
        user.set_password(validated["password"])
        db.session.add(user)
        db.session.commit()

        AuthService._send_verification_email(user, token)
        return user

    #  Login

    @staticmethod
    def authenticate(data: dict, remember: bool = False) -> User:
        """
        Validate credentials and create a login session.

        Flow:
          1. Validate email/password fields via LoginSchema
          2. Look up user by email
          3. Verify password hash (constant-time comparison)
          4. Check email is verified
          5. Rotate refresh token (invalidates previous sessions)
          6. Call login_user() to create Flask-Login session

        Security:
          - Generic error message prevents revealing whether email exists
          - check_password uses Werkzeug's constant-time compare

        Raises:
            ValueError: Invalid credentials or unverified email.
        """
        try:
            validated = login_schema.load(data)
        except ValidationError as e:
            raise ValueError(flatten_errors(e.messages))

        user = User.query.filter_by(email=validated["email"]).first()

        if not user or not user.check_password(validated["password"]):
            raise ValueError("Invalid email or password.")

        if not user.is_verified:
            raise ValueError(
                "Please verify your email address before logging in. "
                "Check your inbox for the verification link."
            )

        user.refresh_token = generate_refresh_token()
        db.session.commit()
        login_user_session(user, remember=remember)
        return user

    #  Email Verification

    @staticmethod
    def verify_email(token: str) -> User:
        """
        Consume the email verification token and activate the account.

        The token is cleared after use — clicking the link twice shows an error.
        A welcome notification is triggered after successful verification.

        Raises:
            ValueError: Token not found (invalid or already used).
        """
        user = User.query.filter_by(verification_token=token).first()
        if not user:
            raise ValueError(
                "Invalid or expired verification link. Please register again."
            )

        user.is_verified = True
        user.verification_token = None
        db.session.commit()

        # Trigger in-app welcome notification
        AuthService._trigger_notification("notify_welcome", user.id)
        return user

    #  Password Reset

    @staticmethod
    def request_password_reset(email: str) -> None:
        """
        Generate a reset token and email it to the user.

        Security: Always returns without error even if email not found.
        This prevents attackers from discovering registered emails by
        checking whether the response differs for known vs unknown emails.

        Flow:
          1. Look up user by email — silently return if not found
          2. Generate a secure one-time token
          3. Store token + 1-hour expiry on the User record
          4. Send reset email with tokenized link
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            current_app.logger.info(
                f"[AUTH] Password reset for unknown email: {email}"
            )
            return  # Silent — caller shows same success message either way

        token = generate_reset_token()
        user.set_reset_token(token)
        db.session.commit()
        AuthService._send_reset_email(user, token)

    @staticmethod
    def is_reset_token_valid(token: str) -> bool:
        """
        Check whether a reset token exists in the DB and has not expired.
        Used by the reset route GET handler to validate before showing the form.
        Returns False for any invalid/missing/expired token.
        """
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return False
        return user.is_reset_token_valid()

    @staticmethod
    def reset_password(token: str, new_password: str) -> None:
        """
        Validate the reset token, apply the new password, and clean up.

        Security:
          - Token validated before any DB write
          - Token cleared after use — one-time use only
          - refresh_token cleared — invalidates ALL existing login sessions
            (user must log in again on all devices)

        Raises:
            ValueError: Token invalid/expired or password too weak.
        """
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.is_reset_token_valid():
            raise ValueError(
                "This reset link is invalid or has expired. "
                "Please request a new password reset."
            )

        AuthService._validate_password(new_password)

        user.set_password(new_password)
        user.clear_reset_token()
        user.refresh_token = None  # Invalidate all active sessions
        db.session.commit()

        current_app.logger.info(f"[AUTH] Password reset successfully for: {user.email}")
        AuthService._trigger_notification("notify_password_changed", user.id)

    #  Logout

    @staticmethod
    def logout(user_id: int) -> None:
        """
        Clear the refresh token from DB and destroy the Flask-Login session.

        Clearing the DB token ensures the session cannot be replayed even if
        the session cookie is somehow obtained by an attacker.
        """
        user = db.session.get(User, user_id)
        if user:
            user.refresh_token = None
            db.session.commit()
        logout_user_session()

    @staticmethod
    def refresh_token(user_id: int) -> str:
        """Rotate and return a new refresh token for the user."""
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        user.refresh_token = generate_refresh_token()
        db.session.commit()
        return user.refresh_token

    #  Private helpers

    @staticmethod
    def _validate_password(password: str) -> None:
        """
        Enforce password complexity rules.
        Rules are hardcoded inline — no import chain that can fail at runtime.

        Rules:
            - Minimum 6 characters
            - At least one uppercase letter
            - At least one number
            - At least one special character
        """
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character.")

    @staticmethod
    def _send_verification_email(user: User, token: str) -> None:
        """
        Build the verify URL and dispatch the welcome email.
        Always logs the URL to terminal — useful fallback if email fails.
        Exceptions are caught and logged — email failure never blocks registration.
        """
        base_url = current_app.config.get("BASE_URL", "http://localhost:5000")
        verify_url = f"{base_url}/auth/verify/{token}"

        current_app.logger.info(f"[AUTH] Verify URL for {user.email}: {verify_url}")

        try:
            from app.shared.email_service import send_welcome_email
            ok = send_welcome_email(user, verify_url=verify_url)
            if ok:
                current_app.logger.info(f"[AUTH] Verification email sent to {user.email}")
            else:
                current_app.logger.error(
                    f"[AUTH] send_welcome_email returned False for {user.email} — "
                    "check MAIL_USERNAME and MAIL_PASSWORD in .env"
                )
        except Exception as exc:
            current_app.logger.error(f"[AUTH] Verification email exception for {user.email}: {exc}")

    @staticmethod
    def _send_reset_email(user: User, token: str) -> None:
        """
        Build the reset URL and dispatch the password-reset email.
        Always logs the URL to terminal — useful fallback if email fails.
        """
        base_url = current_app.config.get("BASE_URL", "http://localhost:5000")
        reset_url = f"{base_url}/auth/reset/{token}"

        current_app.logger.info(f"[AUTH] Reset URL for {user.email}: {reset_url}")

        try:
            from app.shared.email_service import send_password_reset_email
            ok = send_password_reset_email(user, reset_url)
            if ok:
                current_app.logger.info(f"[AUTH] Reset email sent to {user.email}")
            else:
                current_app.logger.error(
                    f"[AUTH] send_password_reset_email returned False for {user.email} — "
                    "check MAIL_USERNAME and MAIL_PASSWORD in .env"
                )
        except Exception as exc:
            current_app.logger.error(f"[AUTH] Reset email exception for {user.email}: {exc}")

    @staticmethod
    def _trigger_notification(method_name: str, user_id: int) -> None:
        """
        Safely call a NotificationService method by name.
        Wrapped in try/except so a notification failure never breaks auth flow.
        """
        try:
            from app.modules.notifications.service import NotificationService
            getattr(NotificationService, method_name)(user_id)
        except Exception as exc:
            current_app.logger.error(f"[AUTH] Notification trigger '{method_name}' failed: {exc}")
