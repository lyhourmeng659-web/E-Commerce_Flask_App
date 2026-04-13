import re
from marshmallow import Schema, fields, validates, ValidationError, pre_load, validate
from app.shared.constants import (
    MIN_PASSWORD_LENGTH,
    MAX_NAME_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_NUMBER,
    PASSWORD_REQUIRE_SPECIAL,
)

EMAIL_REGEX = r"^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$"


class RegisterSchema(Schema):
    """
    Marshmallow schema for user registration input.

    Validates:
    - Name: required, 2–120 chars
    - Email: required, valid format, lowercased in @pre_load
    - Password: required, complexity rules from shared/constants.py
    """

    name = fields.Str(
        required=True,
        validate=validate.Length(
            min=2, max=MAX_NAME_LENGTH,
            error=f"Name must be between 2 and {MAX_NAME_LENGTH} characters."
        )
    )
    email = fields.Str(
        required=True,
        error_messages={"required": "Email address is required."}
    )
    password = fields.Str(required=True, load_only=True)

    @pre_load
    def normalize(self, data, **kwargs):
        """
        Strip whitespace and lowercase email before validation.
        Password is NOT stripped — spaces are valid password characters.
        """
        data = dict(data)
        if "name" in data and data["name"]:
            data["name"] = data["name"].strip()
        if "email" in data and data["email"]:
            data["email"] = data["email"].strip().lower()
        return data

    @validates("email")
    def validate_email(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Email address is required.")
        if not re.match(EMAIL_REGEX, value):
            raise ValidationError("Please enter a valid email address.")

    @validates("password")
    def validate_password(self, value, **kwargs):
        """
        Enforce password complexity rules from shared/constants.py.
        Each rule is a boolean constant — toggle without touching logic.
        """
        if not value:
            raise ValidationError("Password is required.")

        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", value):
            raise ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if PASSWORD_REQUIRE_NUMBER and not re.search(r"[0-9]", value):
            raise ValidationError(
                "Password must contain at least one number."
            )
        if PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValidationError(
                "Password must contain at least one special character (!@#$%^&* etc.)"
            )


class LoginSchema(Schema):
    """
    Marshmallow schema for login input.
    Minimal — only checks presence and email format.
    Actual credential verification is done in AuthService.authenticate().
    """

    email = fields.Str(
        required=True,
        error_messages={"required": "Email address is required."}
    )
    password = fields.Str(required=True, load_only=True)

    @pre_load
    def normalize(self, data, **kwargs):
        """Strip and lowercase email only — password left untouched."""
        data = dict(data)
        if "email" in data and data["email"]:
            data["email"] = data["email"].strip().lower()
        return data

    @validates("email")
    def validate_email(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Email address is required.")
        if not re.match(EMAIL_REGEX, value):
            raise ValidationError("Please enter a valid email address.")
