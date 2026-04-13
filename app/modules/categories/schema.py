from marshmallow import Schema, fields, validates, ValidationError, pre_load


class CategorySchema(Schema):
    """
    Validates category create/update form data.
    All fields are load-only — categories are never serialized via this schema.
    """

    name = fields.Str(required=True)
    description = fields.Str(load_default="")
    slug = fields.Str(load_default="")

    @pre_load
    def strip_inputs(self, data, **kwargs):
        """Strip whitespace from all string fields before validation."""
        return {
            k: v.strip() if isinstance(v, str) else v
            for k, v in data.items()
        }

    @validates("name")
    def validate_name(self, value, **kwargs):
        """Name must be between 2 and 80 characters."""
        if not value or not value.strip():
            raise ValidationError("Category name is required.")
        if len(value.strip()) < 2:
            raise ValidationError("Category name must be at least 2 characters.")
        if len(value.strip()) > 80:
            raise ValidationError("Category name cannot exceed 80 characters.")
