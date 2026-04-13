from marshmallow import Schema, fields


class OrderItemSchema(Schema):
    """
    Serializes a single order line item.
    All fields are dump_only — order items are never created via API directly,
    only through OrderService.create_order().
    """
    id = fields.Int(dump_only=True)
    product_id = fields.Int(dump_only=True)
    product_name = fields.Str(dump_only=True)
    quantity = fields.Int(dump_only=True)
    price = fields.Decimal(as_string=True, dump_only=True)
    # Computed from model property
    subtotal = fields.Decimal(as_string=True, dump_only=True)


class OrderSchema(Schema):
    """
    Serializes full order for API responses and admin views.
    All fields are dump_only — orders are created through
    OrderService, not deserialized from user input directly.
    """
    id = fields.Int(dump_only=True)
    order_number = fields.Str(dump_only=True)

    # Customer info snapshot
    customer_name = fields.Str(dump_only=True)
    customer_email = fields.Str(dump_only=True)

    # Shipping address
    address = fields.Str(dump_only=True)
    city = fields.Str(dump_only=True)
    country = fields.Str(dump_only=True)
    zip_code = fields.Str(dump_only=True)

    # Financials
    total_amount = fields.Decimal(as_string=True, dump_only=True)
    shipping_amount = fields.Decimal(as_string=True, dump_only=True)

    # Order metadata
    status = fields.Str(dump_only=True)
    payment_method = fields.Str(dump_only=True)

    # ISO 8601 datetime string
    created_at = fields.DateTime(dump_only=True)

    # Nested line items
    items = fields.Nested(OrderItemSchema, many=True, dump_only=True)
