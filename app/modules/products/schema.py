from marshmallow import Schema, fields, validates, ValidationError, pre_load


class ProductSchema(Schema):
    """
    Marshmallow schema for Product serialization and deserialization.
    Used in the service layer to validate incoming form data before
    creating or updating products.
    """

    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    slug = fields.Str(dump_only=True)  # Auto-generated, never user input
    description = fields.Str(load_default=None)
    price = fields.Float(required=True)  # Float input → Decimal in service
    stock = fields.Int(required=True)
    category_id = fields.Int(required=True)
    image = fields.Str(dump_only=True)  # Set by save_product_image(), not form
    created_at = fields.DateTime(dump_only=True)

    @pre_load
    def strip_strings(self, data, **kwargs):
        """
        Strip whitespace from all string fields before validation.
        Converts ImmutableMultiDict (Flask form data) to plain dict.
        """
        data = dict(data)
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value or len(value) < 2:
            raise ValidationError("Title must be at least 2 characters.")
        if len(value) > 200:
            raise ValidationError("Title cannot exceed 200 characters.")

    @validates("price")
    def validate_price(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("Price must be greater than 0.")
        if value > 999999.99:
            raise ValidationError("Price is unrealistically high.")

    @validates("stock")
    def validate_stock(self, value, **kwargs):
        if value < 0:
            raise ValidationError("Stock cannot be negative.")

    @validates("category_id")
    def validate_category_id(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("A valid category must be selected.")
