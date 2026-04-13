from marshmallow import Schema, fields


class CartItemSchema(Schema):
    """
    Serializes a cart item dict produced by CartService.get_details().

    Note: This schema serializes the service's computed dict structure,
    not the CartItem model directly. Fields match the dict keys returned
    by get_details() — product is a Product model object, subtotal is Decimal.
    """

    # Nested product fields — only expose what the cart view needs
    product_id = fields.Method("get_product_id")
    product_title = fields.Method("get_product_title")
    product_image = fields.Method("get_product_image")
    product_price = fields.Method("get_product_price")

    quantity = fields.Int()

    # as_string=True returns Decimal as "49.90" string — safe for JSON/display
    subtotal = fields.Decimal(as_string=True)

    def get_product_id(self, obj):
        return obj["product"].id

    def get_product_title(self, obj):
        return obj["product"].title

    def get_product_image(self, obj):
        return obj["product"].image

    def get_product_price(self, obj):
        return str(obj["product"].price)


class CartSummarySchema(Schema):
    """
    Serializes the full cart summary dict from CartService.get_details().
    Used for API responses or when cart data needs to be serialized to JSON.
    """
    items = fields.List(fields.Nested(CartItemSchema))
    subtotal = fields.Decimal(as_string=True)
    shipping = fields.Decimal(as_string=True)
    total = fields.Decimal(as_string=True)
    item_count = fields.Int()
