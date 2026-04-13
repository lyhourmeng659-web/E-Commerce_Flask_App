from marshmallow import Schema, fields, validates, ValidationError


class WishlistSchema(Schema):
    """
    Marshmallow schema for Wishlist serialization.

    Used for API responses and admin data export — not for form validation
    (wishlist add/remove only needs a product_id from the URL, no form body).

    All fields are dump_only — wishlist items are read, not written via schema.
    """

    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    product_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    # Nested product info — included when serializing for API responses
    product = fields.Nested(
        "ProductSchema",
        only=("id", "title", "slug", "formatted_price", "image"),
        dump_only=True,
    )


class WishlistAddSchema(Schema):
    """
    Schema for validating wishlist add requests that come via JSON body
    (e.g. future API endpoint) rather than URL parameter.

    The current routes use product_id as a URL parameter (<int:product_id>)
    so this schema is not used by existing routes — it's here for API
    consistency and future use.
    """

    product_id = fields.Int(required=True)

    @validates("product_id")
    def validate_product_id(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("A valid product ID is required.")
