import re
from marshmallow import Schema, fields, validates, ValidationError, pre_load

# Shared email regex — single source of truth across all schemas
EMAIL_REGEX = r"^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$"


class SupportMessageSchema(Schema):
    """
    Marshmallow schema for support contact form validation.

    All fields are load_only — support messages are never
    serialized back to the user via this schema.
    """

    name    = fields.Str(required=True)
    email   = fields.Str(
        required=True,
        error_messages={"required": "Email address is required."}
    )

    # Optional — defaults to "General Inquiry" in service if blank
    subject = fields.Str(load_default="")
    message = fields.Str(required=True)

    @pre_load
    def strip_inputs(self, data, **kwargs):
        """
        Strip whitespace from all string inputs before validation.
        Prevents whitespace-only values from passing required checks.
        Converts ImmutableMultiDict (Flask forms) to plain dict.
        """
        data = dict(data)
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }

    @validates("name")
    def validate_name(self, value, **kwargs):
        if len(value) < 2:
            raise ValidationError("Name must be at least 2 characters.")
        if len(value) > 120:
            raise ValidationError("Name must be under 120 characters.")

    @validates("email")
    def validate_email(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Email address is required.")
        if not re.match(EMAIL_REGEX, value):
            raise ValidationError("Please enter a valid email address.")

    @validates("subject")
    def validate_subject(self, value, **kwargs):
        if value and len(value) < 3:
            raise ValidationError("Subject must be at least 3 characters.")
        if len(value) > 200:
            raise ValidationError("Subject must be under 200 characters.")

    @validates("message")
    def validate_message(self, value, **kwargs):
        if len(value) < 10:
            raise ValidationError("Message must be at least 10 characters.")
        if len(value) > 5000:
            raise ValidationError("Message must be under 5000 characters.")