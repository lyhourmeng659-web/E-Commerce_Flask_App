from flask_login import current_user
from app.core.base_service import BaseService
from app.core.extensions import db
from app.modules.orders.model import Order, OrderItem
from app.modules.cart.service import CartService
from app.modules.orders.utils import calculate_order_total
from app.modules.products.model import Product
from app.shared.helpers import generate_order_number, to_decimal
from app.shared.constants import OrderStatus, LOW_STOCK_THRESHOLD


class OrderService(BaseService):
    model = Order

    @staticmethod
    def get_by_id_or_404(order_id: int) -> Order:
        """
        Fetch order by ID — aborts with 404 if not found.
        Consistent with Flask pattern for route handlers.
        Use get_or_404 so we don't need a manual if-not-found check.
        """
        return Order.query.get_or_404(order_id)

    @staticmethod
    def get_user_orders(user_id: int):
        """
        Return all orders for a specific user, newest first.
        Used in user order history page.
        """
        return (
            Order.query
            .filter_by(user_id=user_id)
            .order_by(Order.created_at.desc())
            .all()
        )

    @staticmethod
    def create_order(data: dict) -> Order:
        """
        Create a new order from validated checkout form data and current cart.

        Process:
        1. Load and validate cart is not empty
        2. Build Order record with customer and shipping info
        3. flush() to get order.id before creating OrderItems
        4. For each cart item: validate stock, deduct stock, create OrderItem
        5. Clear cart after all items processed
        6. Commit transaction — rollback on any failure
        7. Send notifications (email + Telegram) — non-blocking, won't fail order

        Args:
            data: Cleaned dict from validate_checkout_data() containing:
                  name, email, address, city, country, zip_code, payment_method

        Returns:
            Created Order model instance

        Raises:
            ValueError: If cart is empty, stock insufficient, or product missing
        """
        cart = CartService.get_details()

        if not cart.get("items"):
            raise ValueError("Your cart is empty.")

        subtotal = to_decimal(cart["subtotal"])
        shipping = to_decimal(cart["shipping"])
        total = calculate_order_total(subtotal, shipping)

        try:
            order = Order(
                order_number=generate_order_number(),
                # Link to authenticated user if logged in
                user_id=current_user.id if current_user.is_authenticated else None,
                customer_name=data["name"],
                customer_email=data["email"],
                address=data["address"],
                city=data["city"],
                country=data["country"],
                zip_code=data["zip_code"],
                payment_method=data["payment_method"],
                total_amount=total,
                shipping_amount=shipping,
                status=OrderStatus.PENDING,
            )

            db.session.add(order)
            # flush() writes to DB without committing — gives us order.id
            # needed to set order_id on each OrderItem before commit
            db.session.flush()

            low_stock_products = []

            for item in cart["items"]:
                product = db.session.get(Product, item["product"].id)

                if not product:
                    raise ValueError(
                        f"'{item['product'].title}' is no longer available."
                    )

                if product.stock < item["quantity"]:
                    raise ValueError(
                        f"'{product.title}' only has {product.stock} unit(s) left."
                    )

                # Deduct stock — DB constraint prevents going negative
                product.stock -= item["quantity"]

                # Track products that hit low stock after this order
                if product.stock < LOW_STOCK_THRESHOLD:
                    low_stock_products.append(product)

                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    # Snapshot name and price — preserves invoice accuracy
                    # even if the product is later renamed or repriced
                    product_name=product.title,
                    quantity=item["quantity"],
                    price=to_decimal(product.price),
                ))

            # Clear cart only after all items are successfully processed
            CartService.clear_cart()

            # Single commit for the entire transaction
            # If anything above failed, we never reach this line
            db.session.commit()

            # Send notifications after successful commit — non-critical
            # Wrapped in try/except so notification failure doesn't affect order
            OrderService._send_notifications(order, low_stock_products)

            return order

        except Exception:
            db.session.rollback()
            raise  # Re-raise so route can catch and flash the error

    @staticmethod
    def _send_notifications(order: Order, low_stock_products: list) -> None:
        """
        Send order confirmation email and Telegram notification.
        Also sends low stock alerts for any products that hit the threshold.

        Private method — called internally after successful order commit.
        Use logger instead of print() for proper log management.
        All failures are caught and logged — never propagated to caller.
        """
        from flask import current_app
        from app.shared.email_service import send_order_confirmation
        from app.shared.telegram_service import (
            send_order_notification,
            send_low_stock_notification,
        )

        try:
            send_order_confirmation(order)
        except Exception as e:
            current_app.logger.error(f"Order email failed for #{order.id}: {e}")

        try:
            send_order_notification(order)
        except Exception as e:
            current_app.logger.error(f"Telegram notification failed for #{order.id}: {e}")

        # notify_order_placed: shows in navbar bell -> "Order #XXX confirmed"
        if order.user_id:
            try:
                from app.modules.notifications.service import NotificationService
                NotificationService.notify_order_placed(
                    order.user_id, order.order_number, order.id
                )
            except Exception as e:
                current_app.logger.error(
                    f"[ORDER] notify_order_placed failed: {e}"
                )

        for product in low_stock_products:
            try:
                send_low_stock_notification(product)
            except Exception as e:
                current_app.logger.error(
                    f"Low stock alert failed for product #{product.id}: {e}"
                )

    @staticmethod
    def update_status(order_id: int, new_status: str) -> Order:
        """
        Update order status and fire the matching in-app notification.

        Called by: admin/routes.py when admin changes order status.

        Status → notification mapping:
            shipped   → notify_order_shipped
            delivered → notify_order_delivered
            canceled → notify_order_canceled

        Raises:
            ValueError: order not found or invalid status.
        """
        valid = {
            OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.SHIPPED,
            OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED
        }

        if new_status not in valid:
            raise ValueError(f"Invalid status: '{new_status}'.")

        order = db.session.get(Order, order_id)
        if not order:
            raise ValueError("Order not found.")

        old_status = order.status
        order.status = new_status
        db.session.commit()

        # Fire in-app notification if user is linked to the order
        if order.user_id:
            OrderService._trigger_status_notification(order, new_status)

        from flask import current_app
        current_app.logger.info(
            f"[ORDER] #{order.order_number} status: {old_status} → {new_status}"
        )
        return order

    @staticmethod
    def _trigger_status_notification(order: Order, status: str) -> None:
        """
        Fire the correct NotificationService method for a status change.
        Mapping:
            shipped   → notify_order_shipped
            delivered → notify_order_delivered
            canceled → notify_order_canceled
        """
        try:
            from app.modules.notifications.service import NotificationService
            mapping = {
                OrderStatus.SHIPPED: NotificationService.notify_order_shipped,
                OrderStatus.DELIVERED: NotificationService.notify_order_delivered,
                OrderStatus.CANCELLED: NotificationService.notify_order_cancelled,
            }
            fn = mapping.get(status)
            if fn:
                fn(order.user_id, order.order_number)
        except Exception as e:
            from flask import current_app
            current_app.logger.error(
                f"[ORDER] Status notification failed for #{order.order_number}: {e}"
            )
