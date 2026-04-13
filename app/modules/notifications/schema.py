from marshmallow import Schema, fields, validate, validates, ValidationError


class NotificationSchema(Schema):
    """
    Schema for serializing Notification objects to JSON.
    Used in the AJAX /api/notifications endpoint so the frontend
    can fetch and render notifications without a full page reload.
    """
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    link = fields.Str(dump_only=True, allow_none=True)
    icon = fields.Str(dump_only=True)
    is_read = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="%Y-%m-%dT%H:%M:%S")


class CreateNotificationSchema(Schema):
    """
    Schema for validating manual notification creation (admin use).
    All fields validated before hitting the DB.
    """
    user_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=120))
    message = fields.Str(required=True, validate=validate.Length(min=5, max=500))
    link = fields.Str(load_default=None, validate=validate.Length(max=255))
    icon = fields.Str(load_default="bi-bell", validate=validate.Length(max=60))

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Title cannot be blank.")

    @validates("icon")
    def validate_icon(self, value, **kwargs):
        """Must be a Bootstrap Icons class starting with bi-"""
        if value and not value.startswith("bi-"):
            raise ValidationError("Icon must be a Bootstrap Icons class (e.g. bi-bell).")


notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)
create_notification_schema = CreateNotificationSchema()
